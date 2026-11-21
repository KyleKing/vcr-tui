# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""Tests for the Click CLI via click.testing.CliRunner."""

import json
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from vcr_tui.cli import main
from vcr_tui.config import loader

REPO_ROOT = Path(__file__).parents[1]


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(autouse=True)
def no_global_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """No global config; only defaults plus whatever lives under the start dir."""
    monkeypatch.setattr(loader, 'load_global_config', lambda: None)


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """A tmp_path workspace with the fixture cassette under <ws>/proj/cassettes/."""
    cassette = REPO_ROOT / 'fixtures' / 'cassettes' / 'example_api.yaml'
    target_dir = tmp_path / 'proj' / 'cassettes'
    target_dir.mkdir(parents=True)
    shutil.copy(cassette, target_dir / 'example_api.yaml')
    return tmp_path


class TestFiles:
    def test_lists_cassette_relative_paths(self, runner: CliRunner, workspace: Path) -> None:
        result = runner.invoke(main, [str(workspace), 'files'])
        assert result.exit_code == 0
        expected = str(Path('proj') / 'cassettes' / 'example_api.yaml')
        assert result.output.strip() == expected

    def test_yaml_channel_lists_all_yaml(self, runner: CliRunner, workspace: Path) -> None:
        result = runner.invoke(main, ['--channel', 'yaml', str(workspace), 'files'])
        assert result.exit_code == 0
        expected = str(Path('proj') / 'cassettes' / 'example_api.yaml')
        assert expected in result.output

    def test_unknown_channel_lists_nothing(self, runner: CliRunner, workspace: Path) -> None:
        result = runner.invoke(main, ['-c', 'nope', str(workspace), 'files'])
        assert result.exit_code == 0
        assert result.output == ''

    def test_nonexistent_directory_fails(self, runner: CliRunner, tmp_path: Path) -> None:
        result = runner.invoke(main, [str(tmp_path / 'missing'), 'files'])
        assert result.exit_code != 0


class TestKeys:
    def test_lists_key_tree_indented(self, runner: CliRunner, workspace: Path) -> None:
        cassette = workspace / 'proj' / 'cassettes' / 'example_api.yaml'
        result = runner.invoke(main, [str(workspace), 'keys', str(cassette)])
        assert result.exit_code == 0
        lines = result.output.splitlines()
        assert 'interactions' in lines
        assert '  [0]' in lines
        assert '    response' in lines
        assert 'version' in lines

    def test_nonexistent_file_fails(self, runner: CliRunner, workspace: Path) -> None:
        result = runner.invoke(main, [str(workspace), 'keys', str(workspace / 'missing.yaml')])
        assert result.exit_code != 0


class TestPreview:
    @pytest.fixture
    def cassette(self, workspace: Path) -> Path:
        return workspace / 'proj' / 'cassettes' / 'example_api.yaml'

    def test_file_preview_prints_yaml_document(self, runner: CliRunner, cassette: Path) -> None:
        result = runner.invoke(main, [str(cassette.parent), 'preview', str(cassette)])
        assert result.exit_code == 0
        # File-level preview dumps as yaml, with embedded JSON body strings
        # expanded into nested yaml keys.
        assert 'name: John Doe' in result.output
        assert 'interactions:' in result.output
        assert '\\"' not in result.output

    def test_key_preview_formats_json(self, runner: CliRunner, cassette: Path) -> None:
        result = runner.invoke(
            main,
            [
                str(cassette.parent),
                'preview',
                str(cassette),
                '-k',
                'interactions[0].response.body.string',
            ],
        )
        assert result.exit_code == 0
        assert '"name": "John Doe"' in result.output

    def test_key_preview_metadata_on_default_channel(
        self,
        runner: CliRunner,
        cassette: Path,
    ) -> None:
        result = runner.invoke(
            main,
            [
                str(cassette.parent),
                'preview',
                str(cassette),
                '-k',
                'interactions[0].response.body.string',
            ],
        )
        assert result.exit_code == 0
        assert 'status.code' in result.stderr
        assert '---' in result.stderr

    def test_nonexistent_file_fails(self, runner: CliRunner, workspace: Path) -> None:
        result = runner.invoke(main, [str(workspace), 'preview', str(workspace / 'missing.yaml')])
        assert result.exit_code != 0


class TestInteractions:
    @pytest.fixture
    def cassette(self, workspace: Path) -> Path:
        return workspace / 'proj' / 'cassettes' / 'example_api.yaml'

    def test_lists_one_row_per_interaction(self, runner: CliRunner, cassette: Path) -> None:
        result = runner.invoke(main, [str(cassette.parent), 'interactions', str(cassette)])
        assert result.exit_code == 0
        rows = [line.split() for line in result.output.splitlines()]
        assert [row[:3] for row in rows] == [['0', 'GET', '200'], ['1', 'POST', '201']]
        assert rows[0][-1] == 'api.example.com/users/1'

    def test_index_prints_request_and_response(self, runner: CliRunner, cassette: Path) -> None:
        result = runner.invoke(
            main,
            [str(cassette.parent), 'interactions', str(cassette), '--index', '1'],
        )
        assert result.exit_code == 0
        assert result.output.startswith('POST https://api.example.com/users\n-> 201 Created')
        assert '== Request (json, 49 B) ==' in result.output
        assert '"created_at": "2024-01-15T10:30:00Z"' in result.output

    def test_unknown_index_fails(self, runner: CliRunner, cassette: Path) -> None:
        result = runner.invoke(
            main,
            [str(cassette.parent), 'interactions', str(cassette), '-i', '9'],
        )
        assert result.exit_code != 0
        assert 'no interaction 9' in result.output
        assert '(2 recorded)' in result.output

    def test_non_cassette_fails(self, runner: CliRunner, tmp_path: Path) -> None:
        doc = tmp_path / 'doc.yaml'
        doc.write_text('key: value\n', encoding='utf-8')
        result = runner.invoke(main, [str(tmp_path), 'interactions', str(doc)])
        assert result.exit_code != 0
        assert 'is not a VCR cassette' in result.output


AMBER = REPO_ROOT / 'fixtures' / 'snapshots' / '__snapshots__' / 'test_example.ambr'


class TestSnapshots:
    def test_lists_rows(self, runner: CliRunner, tmp_path: Path) -> None:
        result = runner.invoke(main, [str(tmp_path), 'snapshots', str(AMBER)])
        assert result.exit_code == 0
        rows = [line.split() for line in result.output.splitlines()]
        assert [row[-1] for row in rows] == [
            'TestUsers.test_get[admin]',
            'test_greeting',
            'test_report',
        ]
        assert rows[0][:2] == ['0', 'dict']

    def test_prints_one_body(self, runner: CliRunner, tmp_path: Path) -> None:
        result = runner.invoke(
            main,
            [str(tmp_path), 'snapshots', str(AMBER), '--name', 'test_greeting'],
        )
        assert result.exit_code == 0
        assert result.output == "'Hello, Ann!'\n"

    def test_unknown_name_fails(self, runner: CliRunner, tmp_path: Path) -> None:
        result = runner.invoke(main, [str(tmp_path), 'snapshots', str(AMBER), '-n', 'nope'])
        assert result.exit_code != 0
        assert "no snapshot named 'nope'" in result.output

    def test_non_amber_fails(self, runner: CliRunner, workspace: Path) -> None:
        cassette = workspace / 'proj' / 'cassettes' / 'example_api.yaml'
        result = runner.invoke(main, [str(workspace), 'snapshots', str(cassette)])
        assert result.exit_code != 0
        assert 'is not a syrupy .ambr file' in result.output


LEAKY_CASSETTE = """\
interactions:
- request:
    body: null
    headers:
      Authorization:
      - Bearer live-token-123
    method: GET
    uri: https://api.example.com/me
  response:
    body:
      string: '{"id": 1}'
    headers: {}
    status:
      code: 200
      message: OK
version: 1
"""


class TestAudit:
    def test_clean_fixture_passes(self, runner: CliRunner, workspace: Path) -> None:
        result = runner.invoke(main, [str(workspace), 'audit'])
        assert result.exit_code == 0
        lines = result.output.splitlines()
        assert lines[0] == '1 cassettes, 2 interactions, 1 hosts'
        assert 'Findings (0 error, 0 warning, 3 info)' in lines
        assert any('POST' in line and '201x1' in line for line in lines)

    def test_unredacted_secret_fails(self, runner: CliRunner, workspace: Path) -> None:
        leaky = workspace / 'proj' / 'cassettes' / 'leaky.yaml'
        leaky.write_text(LEAKY_CASSETTE, encoding='utf-8')
        result = runner.invoke(main, [str(workspace), 'audit'])
        assert result.exit_code == 1
        expected = str(Path('proj') / 'cassettes' / 'leaky.yaml')
        assert f'secret-header   {expected}#0' in result.output

    def test_skip_and_fail_on(self, runner: CliRunner, workspace: Path) -> None:
        leaky = workspace / 'proj' / 'cassettes' / 'leaky.yaml'
        leaky.write_text(LEAKY_CASSETTE, encoding='utf-8')
        skipped = runner.invoke(main, [str(workspace), 'audit', '--skip', 'secret-header'])
        assert skipped.exit_code == 0
        strict = runner.invoke(
            main,
            [str(workspace), 'audit', '--skip', 'secret-header', '--fail-on', 'info'],
        )
        assert strict.exit_code == 1

    def test_json_format(self, runner: CliRunner, workspace: Path) -> None:
        result = runner.invoke(main, [str(workspace), 'audit', '--format', 'json'])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['interactions'] == 2
        assert data['hosts'] == {'api.example.com': 2}
        assert {f['code'] for f in data['findings']} == {'email'}


class TestChannels:
    def test_lists_default_channels(self, runner: CliRunner, tmp_path: Path) -> None:
        result = runner.invoke(main, [str(tmp_path), 'channels'])
        assert result.exit_code == 0
        assert 'vcr: enabled (default)' in result.output
        assert 'yaml: enabled' in result.output
        assert '  - **/cassettes/*.yaml' in result.output

    def test_local_config_adds_channel(self, runner: CliRunner, workspace: Path) -> None:
        (workspace / 'vcr-tui.toml').write_text(
            '[channels.custom]\nglob_patterns = ["**/x.yaml"]\n',
        )
        result = runner.invoke(main, [str(workspace), 'channels'])
        assert result.exit_code == 0
        assert 'custom: enabled' in result.output
