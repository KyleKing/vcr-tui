import tomllib
from pathlib import Path

import platformdirs

from vcr_tui.config.defaults import get_default_config
from vcr_tui.config.models import Config

CONFIG_NAMES = ("vcr-tui.toml", ".vcr-tui.toml")


def _find_config_files(start_path: Path) -> list[Path]:
    configs: list[Path] = []
    current = start_path.resolve()

    while current != current.parent:
        for name in CONFIG_NAMES:
            config_path = current / name
            if config_path.exists():
                configs.append(config_path)
                with config_path.open("rb") as f:
                    data = tomllib.load(f)
                    if data.get("root", False):
                        return configs
        current = current.parent

    return configs


def _load_config_file(path: Path) -> Config:
    with path.open("rb") as f:
        data = tomllib.load(f)
    return Config.from_dict(data)


def load_global_config() -> Config | None:
    config_dir = Path(platformdirs.user_config_dir("vcr-tui"))
    for name in CONFIG_NAMES:
        config_file = config_dir / name
        if config_file.exists():
            return _load_config_file(config_file)
    return None


def load_config(start_path: Path | None = None) -> Config:
    if start_path is None:
        start_path = Path.cwd()

    config = get_default_config()

    if (global_config := load_global_config()):
        config = config.merge(global_config)

    local_configs = _find_config_files(start_path)
    for config_file in reversed(local_configs):
        local_config = _load_config_file(config_file)
        config = config.merge(local_config)

    return config
