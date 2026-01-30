from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from vcr_tui.preview.types import YAMLKey

_yaml = YAML()
_yaml.preserve_quotes = True


def load_yaml(file_path: Path) -> Any:
    with file_path.open() as f:
        return _yaml.load(f)


def _extract_keys(data: Any, prefix: str = "", depth: int = 0) -> list[YAMLKey]:
    keys: list[YAMLKey] = []

    match data:
        case dict():
            for key, value in data.items():
                current_path = f"{prefix}.{key}" if prefix else key
                is_leaf = not isinstance(value, (dict, list))
                keys.append(YAMLKey(
                    path=current_path,
                    display=key,
                    depth=depth,
                    is_leaf=is_leaf,
                ))
                if isinstance(value, (dict, list)):
                    keys.extend(_extract_keys(value, current_path, depth + 1))

        case list():
            for i, item in enumerate(data):
                current_path = f"{prefix}[{i}]"
                is_leaf = not isinstance(item, (dict, list))
                keys.append(YAMLKey(
                    path=current_path,
                    display=f"[{i}]",
                    depth=depth,
                    is_leaf=is_leaf,
                ))
                if isinstance(item, (dict, list)):
                    keys.extend(_extract_keys(item, current_path, depth + 1))

    return keys


def get_yaml_keys(file_path: Path) -> list[YAMLKey]:
    data = load_yaml(file_path)
    return _extract_keys(data)


def get_value_at_path(data: Any, path: str) -> Any:
    if not path or path == ".":
        return data

    parts = _parse_path(path)
    current = data

    for part in parts:
        match part:
            case int():
                if isinstance(current, list) and 0 <= part < len(current):
                    current = current[part]
                else:
                    return None
            case str():
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None

    return current


def _parse_path(path: str) -> list[str | int]:
    parts: list[str | int] = []
    current = ""
    i = 0

    while i < len(path):
        char = path[i]
        match char:
            case ".":
                if current:
                    parts.append(current)
                    current = ""
            case "[":
                if current:
                    parts.append(current)
                    current = ""
                end = path.index("]", i)
                index_str = path[i + 1 : end]
                parts.append(int(index_str))
                i = end
            case _:
                current += char
        i += 1

    if current:
        parts.append(current)

    return parts
