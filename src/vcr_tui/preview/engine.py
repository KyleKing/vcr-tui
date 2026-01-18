from pathlib import Path
from typing import Any

from vcr_tui.config.models import Channel, Config, ExtractionRule
from vcr_tui.preview.formatters import format_content
from vcr_tui.preview.types import PreviewResult, YAMLKey
from vcr_tui.preview.yaml_parser import get_value_at_path, get_yaml_keys, load_yaml


EXCLUDED_DIRS = frozenset({".git", ".venv", "venv", "node_modules", "__pycache__", ".tox"})


class PreviewEngine:
    def __init__(self, config: Config):
        self.config = config

    def discover_files(self, directory: Path, channel_name: str | None = None) -> list[Path]:
        channel = self.config.get_channel(channel_name)
        if not channel:
            return []

        files: list[Path] = []
        for pattern in channel.glob_patterns:
            for path in directory.rglob("*"):
                if path.is_file() and self._should_include(path, directory, pattern):
                    files.append(path)

        return sorted(set(files), key=lambda p: p.name)

    def _should_include(self, path: Path, directory: Path, pattern: str) -> bool:
        rel_path = path.relative_to(directory)
        if any(part in EXCLUDED_DIRS for part in rel_path.parts):
            return False
        return rel_path.match(pattern)

    def get_keys(self, file_path: Path) -> list[YAMLKey]:
        return get_yaml_keys(file_path)

    def preview_key(
        self,
        file_path: Path,
        key_path: str,
        channel_name: str | None = None,
    ) -> PreviewResult:
        data = load_yaml(file_path)
        value = get_value_at_path(data, key_path)

        channel = self.config.get_channel(channel_name)
        rule = self._find_matching_rule(key_path, channel)

        formatter = rule.formatter if rule else "yaml"
        label = rule.label if rule else None

        formatted = format_content(value, formatter)
        metadata = self._extract_metadata(data, key_path, rule)

        return PreviewResult(
            content=formatted,
            formatter=formatter,
            metadata=metadata,
            source_path=key_path,
            label=label,
        )

    def preview_file(
        self,
        file_path: Path,
        channel_name: str | None = None,
    ) -> PreviewResult:
        data = load_yaml(file_path)
        channel = self.config.get_channel(channel_name)

        if channel and channel.extraction_rules:
            rule = channel.extraction_rules[0]
            formatter = rule.formatter
            label = rule.label
        else:
            formatter = "yaml"
            label = None

        formatted = format_content(data, formatter)

        return PreviewResult(
            content=formatted,
            formatter=formatter,
            metadata={},
            source_path=".",
            label=label,
        )

    def _find_matching_rule(
        self,
        key_path: str,
        channel: Channel | None,
    ) -> ExtractionRule | None:
        if not channel:
            return None

        for rule in channel.extraction_rules:
            if self._path_matches_rule(key_path, rule.path):
                return rule
        return None

    def _path_matches_rule(self, key_path: str, rule_path: str) -> bool:
        if rule_path == ".":
            return True

        rule_parts = rule_path.lstrip(".").split(".")
        key_parts = self._normalize_path(key_path).split(".")

        if len(key_parts) < len(rule_parts):
            return False

        for rule_part, key_part in zip(rule_parts, key_parts):
            if "[]" in rule_part:
                base = rule_part.replace("[]", "")
                if not key_part.startswith(base):
                    return False
            elif rule_part != key_part:
                return False

        return True

    def _normalize_path(self, path: str) -> str:
        import re
        return re.sub(r"\[(\d+)\]", r"[\1]", path)

    def _extract_metadata(
        self,
        data: Any,
        key_path: str,
        rule: ExtractionRule | None,
    ) -> dict[str, Any]:
        if not rule or not rule.metadata_keys:
            return {}

        metadata: dict[str, Any] = {}
        base_path = self._get_base_path(key_path)

        for meta_key in rule.metadata_keys:
            full_path = f"{base_path}.{meta_key}" if base_path else meta_key
            value = get_value_at_path(data, full_path)
            if value is not None:
                metadata[meta_key] = value

        return metadata

    def _get_base_path(self, key_path: str) -> str:
        parts = key_path.rsplit(".", 1)
        return parts[0] if len(parts) > 1 else ""
