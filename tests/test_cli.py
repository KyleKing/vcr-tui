"""Tests for the Click CLI via click.testing.CliRunner."""

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
        assert result.output.strip() == 'proj/cassettes/example_api.yaml'

    def test_yaml_channel_lists_all_yaml(self, runner: CliRunner, workspace: Path) -> None:
        result = runner.invoke(main, ['--channel', 'yaml', str(workspace), 'files'])
        assert result.exit_code == 0
        assert 'proj/cassettes/example_api.yaml' in result.output

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
        # File-level preview uses extraction_rules[0] of the vcr channel (json).
        # The bodies are embedded JSON strings, so their quotes are escaped in the dump.
        assert '\\"name\\": \\"John Doe\\"' in result.output
        assert '"interactions": [' in result.output

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
        self, runner: CliRunner, cassette: Path
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


class TestChannels:
    def test_lists_default_channels(self, runner: CliRunner, tmp_path: Path) -> None:
        result = runner.invoke(main, [str(tmp_path), 'channels'])
        assert result.exit_code == 0
        assert 'vcr: enabled (default)' in result.output
        assert 'yaml: enabled' in result.output
        assert '  - **/cassettes/*.yaml' in result.output

    def test_local_config_adds_channel(self, runner: CliRunner, workspace: Path) -> None:
        (workspace / 'vcr-tui.toml').write_text(
            '[channels.custom]\nglob_patterns = ["**/x.yaml"]\n'
        )
        result = runner.invoke(main, [str(workspace), 'channels'])
        assert result.exit_code == 0
        assert 'custom: enabled' in result.output
