"""Tests for configuration loading."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from vcr_tui.config.loader import (
    find_config_files,
    load_config,
    load_config_from_file,
    load_global_config,
)
from vcr_tui.config.models import Config


class TestLoadConfigFromFile:
    """Tests for load_config_from_file()."""

    def test_load_valid_config(self, configs_dir: Path) -> None:
        """Test loading a valid config file."""
        config_path = configs_dir / "local.toml"
        config = load_config_from_file(config_path)

        assert config is not None
        assert isinstance(config, Config)
        assert config.default_channel == "local"

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """Test loading non-existent file returns None."""
        config_path = tmp_path / "nonexistent.toml"
        config = load_config_from_file(config_path)

        assert config is None

    def test_load_invalid_toml(self, configs_dir: Path) -> None:
        """Test loading invalid TOML file returns None."""
        config_path = configs_dir / "invalid.toml"
        config = load_config_from_file(config_path)

        assert config is None

    def test_load_root_config(self, configs_dir: Path) -> None:
        """Test loading config with root=true."""
        config_path = configs_dir / "root.toml"
        config = load_config_from_file(config_path)

        assert config is not None
        assert config.root is True


class TestFindConfigFiles:
    """Tests for find_config_files()."""

    def test_find_single_config(self, tmp_path: Path) -> None:
        """Test finding a single config file."""
        config_path = tmp_path / "vcr-tui.toml"
        config_path.write_text("[channels]")

        result = find_config_files(tmp_path)

        assert len(result) == 1
        assert result[0] == config_path

    def test_find_dotfile_config(self, tmp_path: Path) -> None:
        """Test finding hidden config file."""
        config_path = tmp_path / ".vcr-tui.toml"
        config_path.write_text("[channels]")

        result = find_config_files(tmp_path)

        assert len(result) == 1
        assert result[0] == config_path

    def test_prefers_non_dotfile(self, tmp_path: Path) -> None:
        """Test that non-dotfile is preferred over dotfile at same level."""
        config1 = tmp_path / "vcr-tui.toml"
        config2 = tmp_path / ".vcr-tui.toml"
        config1.write_text("[channels]")
        config2.write_text("[channels]")

        result = find_config_files(tmp_path)

        assert len(result) == 1
        assert result[0] == config1

    def test_find_multiple_levels(self, tmp_path: Path) -> None:
        """Test finding configs at multiple directory levels."""
        # Create nested directories
        sub1 = tmp_path / "sub1"
        sub2 = sub1 / "sub2"
        sub2.mkdir(parents=True)

        # Create configs at different levels
        config_root = tmp_path / "vcr-tui.toml"
        config_sub1 = sub1 / "vcr-tui.toml"
        config_sub2 = sub2 / "vcr-tui.toml"

        config_root.write_text("[channels]")
        config_sub1.write_text("[channels]")
        config_sub2.write_text("[channels]")

        # Search from deepest level
        result = find_config_files(sub2)

        assert len(result) == 3
        # Should be ordered from deepest to shallowest
        assert result[0] == config_sub2
        assert result[1] == config_sub1
        assert result[2] == config_root

    def test_stops_at_root_config(self, tmp_path: Path) -> None:
        """Test that search stops at config with root=true."""
        # Create nested directories
        sub1 = tmp_path / "sub1"
        sub2 = sub1 / "sub2"
        sub2.mkdir(parents=True)

        # Create configs
        config_root = tmp_path / "vcr-tui.toml"
        config_sub1 = sub1 / "vcr-tui.toml"
        config_sub2 = sub2 / "vcr-tui.toml"

        config_root.write_text("[channels]")
        config_sub1.write_text("root = true\n[channels]")
        config_sub2.write_text("[channels]")

        # Search from deepest level
        result = find_config_files(sub2)

        # Should stop at sub1 (root=true)
        assert len(result) == 2
        assert result[0] == config_sub2
        assert result[1] == config_sub1

    def test_handles_unreadable_config(self, tmp_path: Path) -> None:
        """Test that unreadable config files are skipped."""
        sub1 = tmp_path / "sub1"
        sub1.mkdir()

        config_bad = tmp_path / "vcr-tui.toml"
        config_good = sub1 / "vcr-tui.toml"

        # Invalid TOML
        config_bad.write_text("[invalid")
        config_good.write_text("[channels]")

        result = find_config_files(sub1)

        # Should find the good one and skip the bad one
        assert len(result) == 2
        assert result[0] == config_good

    def test_empty_directory(self, tmp_path: Path) -> None:
        """Test searching in directory with no configs."""
        result = find_config_files(tmp_path)

        assert result == []


class TestLoadGlobalConfig:
    """Tests for load_global_config()."""

    def test_no_global_config(self) -> None:
        """Test when no global config exists."""
        with patch("vcr_tui.config.loader.platformdirs.user_config_dir") as mock_dir:
            mock_dir.return_value = "/nonexistent/path"

            config = load_global_config()

            assert config is None

    def test_load_existing_global_config(self, tmp_path: Path) -> None:
        """Test loading existing global config."""
        global_config = tmp_path / "config.toml"
        global_config.write_text("""
default_channel = "global"

[channels.global]
glob_patterns = ["*.yaml"]
enabled = true

[[channels.global.extraction_rules]]
path = ".test"
formatter = "json"
""")

        with patch("vcr_tui.config.loader.platformdirs.user_config_dir") as mock_dir:
            mock_dir.return_value = str(tmp_path)

            config = load_global_config()

            assert config is not None
            assert config.default_channel == "global"
            assert "global" in config.channels

    def test_invalid_global_config(self, tmp_path: Path) -> None:
        """Test that invalid global config returns None."""
        global_config = tmp_path / "config.toml"
        global_config.write_text("[invalid toml")

        with patch("vcr_tui.config.loader.platformdirs.user_config_dir") as mock_dir:
            mock_dir.return_value = str(tmp_path)

            config = load_global_config()

            assert config is None


class TestLoadConfig:
    """Tests for load_config() - the main entry point."""

    def test_returns_defaults_when_no_configs(self, tmp_path: Path) -> None:
        """Test that defaults are returned when no config files exist."""
        with patch("vcr_tui.config.loader.load_global_config") as mock_global:
            mock_global.return_value = None

            config = load_config(tmp_path)

            assert config is not None
            # Should have default channels
            assert "vcr" in config.channels
            assert "yaml" in config.channels

    def test_merges_global_with_defaults(self, tmp_path: Path, configs_dir: Path) -> None:
        """Test that global config is merged with defaults."""
        # Create a mock global config
        global_toml = tmp_path / "global_config.toml"
        global_toml.write_text("""
default_channel = "global"

[channels.global]
glob_patterns = ["*.global"]
enabled = true

[[channels.global.extraction_rules]]
path = ".global"
formatter = "json"
""")

        with patch("vcr_tui.config.loader.load_global_config") as mock_global:
            mock_global.return_value = load_config_from_file(global_toml)

            # Search in empty directory (no local configs)
            config = load_config(tmp_path / "empty")

            # Should have both default and global channels
            assert "vcr" in config.channels  # from defaults
            assert "yaml" in config.channels  # from defaults
            assert "global" in config.channels  # from global
            assert config.default_channel == "global"

    def test_local_overrides_global(self, tmp_path: Path) -> None:
        """Test that local config overrides global config."""
        global_toml = tmp_path / "global.toml"
        global_toml.write_text('default_channel = "global"')

        local_toml = tmp_path / "local" / "vcr-tui.toml"
        local_toml.parent.mkdir()
        local_toml.write_text('default_channel = "local"')

        with patch("vcr_tui.config.loader.load_global_config") as mock_global:
            mock_global.return_value = load_config_from_file(global_toml)

            config = load_config(local_toml.parent)

            assert config.default_channel == "local"

    def test_deeper_config_overrides_shallow(self, tmp_path: Path) -> None:
        """Test that deeper local configs override shallower ones."""
        root_toml = tmp_path / "vcr-tui.toml"
        sub_toml = tmp_path / "sub" / "vcr-tui.toml"
        sub_toml.parent.mkdir()

        root_toml.write_text('default_channel = "root"')
        sub_toml.write_text('default_channel = "sub"')

        with patch("vcr_tui.config.loader.load_global_config") as mock_global:
            mock_global.return_value = None

            config = load_config(sub_toml.parent)

            assert config.default_channel == "sub"

    def test_uses_cwd_when_no_path_provided(self) -> None:
        """Test that current working directory is used when start_path is None."""
        with (
            patch("vcr_tui.config.loader.Path.cwd") as mock_cwd,
            patch("vcr_tui.config.loader.find_config_files") as mock_find,
            patch("vcr_tui.config.loader.load_global_config") as mock_global,
        ):
            mock_cwd.return_value = Path("/mock/cwd")
            mock_find.return_value = []
            mock_global.return_value = None

            config = load_config()

            mock_find.assert_called_once_with(Path("/mock/cwd"))
            assert config is not None

    def test_complete_merge_hierarchy(self, tmp_path: Path) -> None:
        """Test complete config merging from all sources."""
        # Setup: defaults + global + parent + local
        global_toml = tmp_path / "global.toml"
        parent_toml = tmp_path / "parent" / "vcr-tui.toml"
        local_toml = tmp_path / "parent" / "child" / "vcr-tui.toml"

        parent_toml.parent.mkdir(parents=True)
        local_toml.parent.mkdir(parents=True)

        # Global adds a channel
        global_toml.write_text("""
[channels.global]
glob_patterns = ["*.global"]
enabled = true

[[channels.global.extraction_rules]]
path = ".global"
formatter = "json"
""")

        # Parent adds another channel
        parent_toml.write_text("""
[channels.parent]
glob_patterns = ["*.parent"]
enabled = true

[[channels.parent.extraction_rules]]
path = ".parent"
formatter = "yaml"
""")

        # Local sets default and adds its own channel
        local_toml.write_text("""
default_channel = "local"

[channels.local]
glob_patterns = ["*.local"]
enabled = true

[[channels.local.extraction_rules]]
path = ".local"
formatter = "text"
""")

        with patch("vcr_tui.config.loader.load_global_config") as mock_global:
            mock_global.return_value = load_config_from_file(global_toml)

            config = load_config(local_toml.parent)

            # Should have all channels
            assert "vcr" in config.channels  # from defaults
            assert "yaml" in config.channels  # from defaults
            assert "global" in config.channels  # from global
            assert "parent" in config.channels  # from parent
            assert "local" in config.channels  # from local

            # Local should win for default_channel
            assert config.default_channel == "local"
