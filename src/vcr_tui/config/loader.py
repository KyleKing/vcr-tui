"""Configuration file loading and merging."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import platformdirs

from vcr_tui.config.defaults import get_default_config
from vcr_tui.config.models import Config

# Config file names to search for
CONFIG_FILENAMES = ["vcr-tui.toml", ".vcr-tui.toml"]


def find_config_files(start_path: Path) -> list[Path]:
    """Find all config files from start_path up to filesystem root.

    Walks up the directory tree searching for vcr-tui.toml or .vcr-tui.toml
    files. Stops when a config with root=true is found or filesystem root
    is reached.

    Args:
        start_path: Directory to start searching from

    Returns:
        List of config file paths, ordered from deepest to shallowest
    """
    configs: list[Path] = []
    current = start_path.resolve()

    while current != current.parent:
        for filename in CONFIG_FILENAMES:
            config_path = current / filename
            if config_path.exists() and config_path.is_file():
                configs.append(config_path)

                # Check if this config has root=true
                try:
                    with open(config_path, "rb") as f:
                        data = tomllib.load(f)
                        if data.get("root", False):
                            return configs
                except (OSError, tomllib.TOMLDecodeError):
                    # If we can't read the file, continue searching
                    pass

                # Only use the first matching filename at this level
                break

        current = current.parent

    return configs


def load_global_config() -> Config | None:
    """Load global configuration from OS-appropriate location.

    Locations:
    - macOS: ~/Library/Application Support/vcr-tui/config.toml
    - Linux: ~/.config/vcr-tui/config.toml
    - Windows: %APPDATA%/vcr-tui/config.toml

    Returns:
        Config object if global config exists, None otherwise
    """
    config_dir = Path(platformdirs.user_config_dir("vcr-tui"))
    config_file = config_dir / "config.toml"

    if not config_file.exists():
        return None

    try:
        with open(config_file, "rb") as f:
            data = tomllib.load(f)
            return Config.from_dict(data)
    except (OSError, tomllib.TOMLDecodeError):
        return None


def load_config_from_file(config_path: Path) -> Config | None:
    """Load a single config file.

    Args:
        config_path: Path to config file

    Returns:
        Config object if file is valid, None otherwise
    """
    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
            return Config.from_dict(data)
    except (OSError, tomllib.TOMLDecodeError):
        return None


def load_config(start_path: Path | None = None) -> Config:
    """Load merged configuration from all sources.

    Configuration priority (lowest to highest):
    1. Built-in defaults
    2. Global config
    3. Local configs (from shallowest to deepest)

    Args:
        start_path: Directory to start searching for local configs.
                   If None, uses current working directory.

    Returns:
        Merged Config object
    """
    if start_path is None:
        start_path = Path.cwd()

    # Start with defaults
    config = get_default_config()

    # Merge global config
    global_config = load_global_config()
    if global_config:
        config = config.merge(global_config)

    # Find and merge local configs (from shallowest to deepest)
    local_config_paths = find_config_files(start_path)
    for config_path in reversed(local_config_paths):
        local_config = load_config_from_file(config_path)
        if local_config:
            config = config.merge(local_config)

    return config
