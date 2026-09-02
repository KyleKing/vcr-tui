"""Tests for config loader layering (defaults -> global -> local)."""

from pathlib import Path

import pytest

from vcr_tui.config import loader
from vcr_tui.config.defaults import get_default_config
from vcr_tui.config.loader import _find_config_files, load_config
from vcr_tui.config.models import Config


@pytest.fixture(autouse=True)
def no_global_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(loader, 'load_global_config', lambda: None)


@pytest.fixture
def global_config(monkeypatch: pytest.MonkeyPatch) -> Config:
    config = Config.from_dict({'channels': {'global-only': {'glob_patterns': ['**/g.yaml']}}})
    monkeypatch.setattr(loader, 'load_global_config', lambda: config)
    return config


def _write_config(path: Path, text: str) -> Path:
    path.write_text(text)
    return path


class TestFindConfigFiles:
    def test_no_config_files(self, tmp_path: Path) -> None:
        assert _find_config_files(tmp_path) == []

    @pytest.mark.parametrize('name', ['vcr-tui.toml', '.vcr-tui.toml'])
    def test_finds_both_config_names(self, tmp_path: Path, name: str) -> None:
        config = _write_config(tmp_path / name, '')
        assert _find_config_files(tmp_path) == [config]

    def test_walks_up_and_collects_innermost_first(self, tmp_path: Path) -> None:
        outer = _write_config(tmp_path / 'vcr-tui.toml', '')
        inner_dir = tmp_path / 'proj' / 'sub'
        inner_dir.mkdir(parents=True)
        inner = _write_config(inner_dir / 'vcr-tui.toml', '')
        assert _find_config_files(inner_dir) == [inner, outer]

    def test_root_true_stops_the_walk(self, tmp_path: Path) -> None:
        # Files above the root=true file are never reached; ones below it still are.
        outer = _write_config(tmp_path / 'vcr-tui.toml', '')
        assert outer
        mid = tmp_path / 'proj'
        mid.mkdir()
        root_flag = _write_config(mid / 'vcr-tui.toml', 'root = true\n')
        start = mid / 'sub'
        start.mkdir()
        assert _find_config_files(start) == [root_flag]


class TestLoadConfig:
    def test_defaults_when_no_files(self, tmp_path: Path) -> None:
        assert load_config(tmp_path) == get_default_config()

    def test_global_adds_channels_to_defaults(self, tmp_path: Path, global_config: Config) -> None:
        config = load_config(tmp_path)
        names = {ch.name for ch in config.channels}
        assert names >= {'vcr', 'yaml', 'global-only'}

    def test_local_adds_channel(self, tmp_path: Path) -> None:
        _write_config(
            tmp_path / 'vcr-tui.toml',
            '[channels.local-only]\nglob_patterns = ["**/l.yaml"]\n',
        )
        config = load_config(tmp_path)
        names = {ch.name for ch in config.channels}
        assert 'local-only' in names
        assert 'vcr' in names  # defaults still present

    def test_local_overrides_default_channel(self, tmp_path: Path) -> None:
        _write_config(tmp_path / 'vcr-tui.toml', 'default_channel = "yaml"\n')
        assert load_config(tmp_path).default_channel == 'yaml'

    def test_innermost_file_wins_for_scalars(self, tmp_path: Path) -> None:
        (tmp_path / 'proj').mkdir()
        _write_config(tmp_path / 'vcr-tui.toml', 'default_channel = "vcr"\n')
        _write_config(tmp_path / 'proj' / 'vcr-tui.toml', 'default_channel = "yaml"\n')
        assert load_config(tmp_path / 'proj').default_channel == 'yaml'

    def test_root_true_layers_global_but_stops_local_walk(
        self, tmp_path: Path, global_config: Config
    ) -> None:
        outer = tmp_path / 'outer'
        outer.mkdir()
        _write_config(
            outer / 'vcr-tui.toml',
            '[channels.outer-only]\nglob_patterns = ["**/o.yaml"]\n',
        )
        start = outer / 'proj'
        start.mkdir()
        _write_config(start / 'vcr-tui.toml', 'root = true\n')
        config = load_config(start)
        names = {ch.name for ch in config.channels}
        assert 'global-only' in names  # global still layered
        assert 'outer-only' not in names  # file beyond the root=true boundary
        assert config.root is True

    def test_full_stack_defaults_global_local(self, tmp_path: Path, global_config: Config) -> None:
        _write_config(
            tmp_path / 'vcr-tui.toml',
            'default_channel = "local-only"\n\n'
            '[channels.local-only]\nglob_patterns = ["**/l.yaml"]\n',
        )
        config = load_config(tmp_path)
        names = {ch.name for ch in config.channels}
        assert names == {'vcr', 'yaml', 'global-only', 'local-only'}
        assert config.default_channel == 'local-only'

    def test_local_cannot_override_global_channel(
        self, tmp_path: Path, global_config: Config
    ) -> None:
        # Pins current behaviour (suspected bug): merge keeps the existing (global)
        # channel definition, so a local file redefining it changes nothing.
        _write_config(
            tmp_path / 'vcr-tui.toml',
            '[channels.global-only]\nglob_patterns = ["**/overridden.yaml"]\n',
        )
        config = load_config(tmp_path)
        channel = next(ch for ch in config.channels if ch.name == 'global-only')
        assert channel.glob_patterns == ('**/g.yaml',)
