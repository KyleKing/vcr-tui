"""Tests for preview/engine.py."""

from pathlib import Path
from typing import Any

import pytest
from ruamel.yaml import YAML

from vcr_tui.config.defaults import get_default_config
from vcr_tui.config.models import Channel, Config, ExtractionRule
from vcr_tui.preview.engine import EXCLUDED_DIRS, PreviewEngine

_yaml = YAML()


def _write_yaml(path: Path, data: object) -> Path:
    with path.open('w') as fh:
        _yaml.dump(data, fh)
    return path


@pytest.fixture
def engine() -> PreviewEngine:
    return PreviewEngine(get_default_config())


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """A tmp_path tree with cassettes in and out of excluded dirs."""
    files = [
        'proj/cassettes/a.yaml',
        'proj/cassettes/nested/b.yml',
        'proj/other/c.yaml',  # not under a cassettes dir: not matched by the vcr channel
        '.git/cassettes/ignored.yaml',
        '.venv/cassettes/ignored.yaml',
        '__pycache__/cassettes/ignored.yaml',
        'proj/cassettes/.git/deep-ignored.yaml',
    ]
    for rel in files:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('interactions: []\n')
    return tmp_path


class TestDiscoverFiles:
    def test_finds_yaml_directly_in_start_directory(
        self, engine: PreviewEngine, tmp_path: Path
    ) -> None:
        # Regression: Path('a.yaml').match('**/*.yaml') is False, so with the
        # broad 'yaml' channel a file at the top of the start directory was missed.
        top = tmp_path / 'example.yaml'
        top.write_text('a: 1\n')
        assert engine.discover_files(tmp_path, 'yaml') == [top]

    def test_finds_vcr_cassette_directly_under_start(
        self, engine: PreviewEngine, tmp_path: Path
    ) -> None:
        # Regression: pathlib treats '**' as a single '*' level, so a cassette
        # directly under <start>/cassettes/ did not match '**/cassettes/*.yaml'.
        f = tmp_path / 'cassettes' / 'example_api.yaml'
        f.parent.mkdir()
        f.write_text('interactions: []\n')
        assert engine.discover_files(tmp_path) == [f]

    def test_finds_yaml_in_cassettes_dirs(self, engine: PreviewEngine, tree: Path) -> None:
        found = engine.discover_files(tree)
        assert [f.name for f in found] == ['a.yaml', 'b.yml']

    @pytest.mark.parametrize('excluded', sorted(EXCLUDED_DIRS))
    def test_excluded_dirs_are_skipped(
        self, excluded: str, engine: PreviewEngine, tmp_path: Path
    ) -> None:
        included = tmp_path / 'proj' / 'cassettes' / 'in.yaml'
        excluded_file = tmp_path / excluded / 'cassettes' / 'out.yaml'
        for p in (included, excluded_file):
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('interactions: []\n')

        assert engine.discover_files(tmp_path) == [included]

    def test_unknown_channel_returns_empty(self, engine: PreviewEngine, tree: Path) -> None:
        assert engine.discover_files(tree, channel_name='nope') == []

    def test_explicit_channel(self, engine: PreviewEngine, tree: Path) -> None:
        found = engine.discover_files(tree, channel_name='yaml')
        assert {f.name for f in found} == {'a.yaml', 'b.yml', 'c.yaml'}

    def test_top_level_cassettes_dir_is_not_matched(
        self, engine: PreviewEngine, tmp_path: Path
    ) -> None:
        # pathlib's match() treats '**' as a single '*' level, so without the
        # top-level fallback in _should_include a cassette directly under
        # <start>/cassettes/ would not match '**/cassettes/*.yaml'.
        f = tmp_path / 'cassettes' / 'top.yaml'
        f.parent.mkdir(parents=True)
        f.write_text('interactions: []\n')
        assert engine.discover_files(tmp_path) == [f]

    def test_tree_walked_once_for_overlapping_patterns(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Regression: discover_files used to rglob once per pattern, walking the
        # whole tree N times for N patterns; now the tree is walked once and each
        # path is matched against every pattern.
        config = Config(
            channels=(
                Channel(
                    name='overlap',
                    glob_patterns=('**/*.yaml', '**/cassettes/*.yaml'),
                    extraction_rules=(ExtractionRule(path='.', formatter='yaml'),),
                ),
            )
        )
        cassette = tmp_path / 'cassettes' / 'example_api.yaml'
        cassette.parent.mkdir(parents=True)
        cassette.write_text('interactions: []\n')
        plain = tmp_path / 'plain.yaml'
        plain.write_text('a: 1\n')

        calls: list[Path] = []
        original = Path.rglob

        def counting_rglob(self: Path, pattern: str) -> Any:
            calls.append(self)
            return original(self, pattern)

        monkeypatch.setattr(Path, 'rglob', counting_rglob)

        found = PreviewEngine(config).discover_files(tmp_path, channel_name='overlap')

        assert {f.name for f in found} == {'example_api.yaml', 'plain.yaml'}
        assert calls == [tmp_path]


class TestPreviewKey:
    @pytest.mark.parametrize(
        ('key_path', 'label', 'snippet'),
        [
            ('interactions[0].response.body.string', 'Response Body', '"name"'),
            # Pins current behaviour: interaction 1's request body is a bare string (no
            # .string key), so the value is None ('null') even though the rule matched.
            ('interactions[1].request.body.string', 'Request Body', 'null'),
        ],
    )
    def test_matching_rule_sets_formatter_and_label(
        self,
        engine: PreviewEngine,
        cassette_path: Path,
        key_path: str,
        label: str,
        snippet: str,
    ) -> None:
        result = engine.preview_key(cassette_path, key_path)
        assert result.label == label
        assert result.formatter == 'json'
        assert result.source_path == key_path
        assert snippet in result.content

    def test_unmatched_key_falls_back_to_yaml(
        self, engine: PreviewEngine, cassette_path: Path
    ) -> None:
        result = engine.preview_key(cassette_path, 'version')
        assert result.formatter == 'yaml'
        assert result.label is None
        assert result.content == '1'

    def test_default_channel_metadata_is_extracted(
        self, engine: PreviewEngine, cassette_path: Path
    ) -> None:
        result = engine.preview_key(cassette_path, 'interactions[0].response.body.string')
        assert result.metadata['status.code'] == 200
        assert result.metadata['request.method'] == 'GET'

    @pytest.mark.parametrize(
        ('key_path', 'expected'),
        [
            # Leading-dot key path: the empty rule part ('') never equals 'interactions',
            # so the rule does not match and the yaml fallback applies.
            ('.interactions[0].response.body.string', 'yaml'),
            ('interactions[0].response.body.string', 'json'),
        ],
    )
    def test_rule_matches_only_paths_without_leading_dot(
        self, engine: PreviewEngine, cassette_path: Path, key_path: str, expected: str
    ) -> None:
        # Pins current behaviour: rules only match key paths without a leading dot
        # (the shape get_yaml_keys produces).
        assert engine.preview_key(cassette_path, key_path).formatter == expected


class TestPreviewFile:
    def test_uses_first_rule_of_channel(self, engine: PreviewEngine, cassette_path: Path) -> None:
        # File-level preview always dumps as yaml; only the label comes from rules[0].
        result = engine.preview_file(cassette_path)
        assert result.formatter == 'yaml'
        assert result.label == 'Response Body'
        assert result.source_path == '.'
        assert 'John Doe' in result.content

    def test_json_body_string_renders_as_nested_keys(
        self, engine: PreviewEngine, cassette_path: Path
    ) -> None:
        result = engine.preview_file(cassette_path)
        assert 'name: John Doe' in result.content
        assert 'email: john@example.com' in result.content
        assert '\\"' not in result.content

    def test_plain_string_value_survives_untouched(
        self, engine: PreviewEngine, cassette_path: Path
    ) -> None:
        result = engine.preview_file(cassette_path)
        assert 'uri: https://api.example.com/users/1' in result.content
        assert 'message: OK' in result.content

    def test_invalid_and_scalar_json_strings_stay_strings(
        self, engine: PreviewEngine, tmp_path: Path
    ) -> None:
        path = _write_yaml(
            tmp_path / 'odd.yaml',
            {
                'not_json': '{oops',
                'number_string': '42',
                'bool_string': 'true',
                'null_string': 'null',
            },
        )
        result = engine.preview_file(path)
        assert "not_json: '{oops'" in result.content
        assert "number_string: '42'" in result.content
        assert "bool_string: 'true'" in result.content
        assert "null_string: 'null'" in result.content

    def test_loaded_data_is_not_mutated(self, engine: PreviewEngine, cassette_path: Path) -> None:
        from vcr_tui.preview.yaml_parser import load_yaml

        data = load_yaml(cassette_path)
        before = data['interactions'][0]['response']['body']['string']
        engine.preview_file(cassette_path)
        assert data['interactions'][0]['response']['body']['string'] == before
        assert isinstance(data['interactions'][0]['response']['body']['string'], str)

    def test_metadata_is_empty(self, engine: PreviewEngine, cassette_path: Path) -> None:
        # Pins current behaviour: preview_file never extracts metadata.
        assert engine.preview_file(cassette_path).metadata == {}

    def test_channel_without_rules_uses_yaml(self, cassette_path: Path) -> None:
        engine = PreviewEngine(
            Config(channels=(Channel(name='bare', glob_patterns=('**/*',), extraction_rules=()),))
        )
        result = engine.preview_file(cassette_path, 'bare')
        assert result.formatter == 'yaml'
        assert result.label is None


class TestPathMatching:
    @pytest.mark.parametrize(
        ('key_path', 'rule_path', 'expected'),
        [
            ('anything', '.', True),
            ('interactions[0].response.body.string', '.interactions[].response.body.string', True),
            ('interactions[10].response.body.string', '.interactions[].response.body.string', True),
            ('interactions[0].response.body', '.interactions[].response.body.string', False),
            ('interactions[0].request.body.string', '.interactions[].response.body.string', False),
            ('other[0].response.body.string', '.interactions[].response.body.string', False),
            # Suspected bug: '[]' matches by startswith, so a key part with the rule
            # part as a prefix also matches.
            (
                'interactions-longer[0].response.body.string',
                '.interactions[].response.body.string',
                True,
            ),
        ],
    )
    def test_path_matches_rule(
        self, engine: PreviewEngine, key_path: str, rule_path: str, expected: bool
    ) -> None:
        assert engine._path_matches_rule(key_path, rule_path) is expected


def _meta_config() -> Config:
    return Config(
        channels=(
            Channel(
                name='meta',
                glob_patterns=('**/*.yaml',),
                extraction_rules=(
                    ExtractionRule(
                        path='.users[].profile.name',
                        formatter='yaml',
                        metadata_keys=('id', 'name'),
                    ),
                ),
            ),
        ),
        default_channel='meta',
    )


class TestMetadataExtraction:
    @pytest.mark.parametrize(
        ('key_path', 'expected'),
        [
            ('users[0].profile.name', {'id': 7, 'name': 'a'}),
            ('users[1].profile.name', {'id': 8, 'name': 'b'}),
        ],
    )
    def test_metadata_resolved_relative_to_key_parent(
        self, tmp_path: Path, key_path: str, expected: dict[str, Any]
    ) -> None:
        data = {
            'users': [
                {'profile': {'name': 'a', 'id': 7}},
                {'profile': {'name': 'b', 'id': 8}},
            ]
        }
        f = _write_yaml(tmp_path / 'meta.yaml', data)
        result = PreviewEngine(_meta_config()).preview_key(f, key_path, 'meta')
        assert result.metadata == expected

    def test_missing_metadata_keys_are_omitted(self, tmp_path: Path) -> None:
        f = _write_yaml(tmp_path / 'm.yaml', {'users': [{'profile': {'name': 'a'}}]})
        result = PreviewEngine(_meta_config()).preview_key(f, 'users[0].profile.name', 'meta')
        assert result.metadata == {'name': 'a'}

    def test_no_rule_gives_empty_metadata(self, engine: PreviewEngine, cassette_path: Path) -> None:
        result = engine.preview_key(cassette_path, 'version')  # no rule matches
        assert result.metadata == {}

    def test_rule_without_metadata_keys_gives_empty_metadata(self, tmp_path: Path) -> None:
        config = Config(
            channels=(
                Channel(
                    name='plain',
                    glob_patterns=('**/*.yaml',),
                    extraction_rules=(
                        ExtractionRule(path='.users[].profile.name', formatter='yaml'),
                    ),
                ),
            ),
        )
        f = _write_yaml(tmp_path / 'm.yaml', {'users': [{'profile': {'name': 'a', 'id': 7}}]})
        result = PreviewEngine(config).preview_key(f, 'users[0].profile.name', 'plain')
        assert result.metadata == {}
