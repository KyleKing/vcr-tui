# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""Core engine that discovers cassette files and builds previews."""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from vcr_tui.config.models import Channel, Config, ExtractionRule, FormatterType
from vcr_tui.preview.audit import Cassette
from vcr_tui.preview.cassette import Interaction, is_cassette, parse_cassette
from vcr_tui.preview.diff import CassetteDiff, DiffOptions, diff_cassette
from vcr_tui.preview.formatters import format_content
from vcr_tui.preview.git_source import ChangedFile, changed_files, read_at_ref, repo_root
from vcr_tui.preview.types import PreviewResult, YAMLKey
from vcr_tui.preview.yaml_parser import (
    get_value_at_path,
    get_yaml_keys,
    load_yaml,
    load_yaml_text,
)

EXCLUDED_DIRS = frozenset({'.git', '.venv', 'venv', 'node_modules', '__pycache__', '.tox'})


class PreviewEngine:
    """Finds cassette files and formats the values selected from them."""

    def __init__(self, config: Config) -> None:
        """Store the configuration used for every later operation."""
        self.config = config

    def discover_files(self, directory: Path, channel_name: str | None = None) -> list[Path]:
        """List files under the directory matching the channel's glob patterns.

        Returns:
            The matching file paths sorted by name, or empty when no channel matches.
        """
        channel = self.config.get_channel(channel_name)
        if not channel:
            return []

        files: list[Path] = []
        seen: set[Path] = set()
        for path in directory.rglob('*'):
            if not (path.is_file() and path not in seen):
                continue
            for pattern in channel.glob_patterns:
                if self._should_include(path, directory, pattern):
                    seen.add(path)
                    files.append(path)
                    break

        return sorted(set(files), key=lambda p: p.name)

    def matches_channel(
        self,
        path: Path,
        directory: Path,
        channel_name: str | None = None,
    ) -> bool:
        """Whether a path under the directory matches the channel's patterns.

        Unlike discover_files, the file need not exist, so a deleted cassette
        can still be recognised.
        """
        channel = self.config.get_channel(channel_name)
        if not channel:
            return False
        return any(self._should_include(path, directory, p) for p in channel.glob_patterns)

    def diff_against(
        self,
        directory: Path,
        ref: str,
        channel_name: str | None = None,
        options: DiffOptions | None = None,
    ) -> tuple[list[CassetteDiff], list[tuple[Path, str]]]:
        """Compare each changed cassette under the directory with its version at the ref.

        Returns:
            The diffs (files with no reviewable change included, as empty diffs),
            plus (path, reason) for each changed file that failed to parse.
        """
        directory = directory.resolve()
        root = repo_root(directory)
        diffs: list[CassetteDiff] = []
        unreadable: list[tuple[Path, str]] = []
        for changed in changed_files(directory, ref):
            if not self.matches_channel(changed.path, directory, channel_name):
                continue
            try:
                old, new = _load_versions(root, changed, ref)
            except Exception as exc:
                reason = str(exc).splitlines()[0] if str(exc) else type(exc).__name__
                unreadable.append((changed.path, reason))
                continue
            if old is None and new is None:
                continue
            diffs.append(diff_cassette(changed.path, old, new, options))
        return diffs, unreadable

    def _should_include(self, path: Path, directory: Path, pattern: str) -> bool:
        rel_path = path.relative_to(directory)
        if any(part in EXCLUDED_DIRS for part in rel_path.parts):
            return False
        return rel_path.match(self._relativize_pattern(pattern, directory.name))

    @staticmethod
    def _relativize_pattern(pattern: str, directory_name: str) -> str:
        """Make a glob pattern match paths relative to the start directory.

        ``PurePath.match`` treats ``**`` as a single ``*`` level, so
        ``Path('a.yaml').match('**/*.yaml')`` is False and a file directly in
        the start directory is missed. Likewise ``**/cassettes/*.yaml`` cannot
        match anything when the start directory *is* the cassettes directory,
        since there is no ``cassettes`` level below it — so a leading literal
        segment equal to the start directory's name is dropped as well.

        Returns:
            The adjusted pattern.
        """
        if not pattern.startswith('**/'):
            return pattern
        stripped = pattern[3:]
        prefix = f'{directory_name}/'
        if stripped.startswith(prefix):
            return stripped[len(prefix) :]
        return stripped

    @staticmethod
    def get_keys(file_path: Path) -> list[YAMLKey]:
        """List the selectable YAML keys contained in the file.

        Returns:
            The YAML keys.
        """
        return get_yaml_keys(file_path)

    @staticmethod
    def get_interactions(file_path: Path) -> list[Interaction] | None:
        """Parse the file's recorded HTTP interactions.

        Returns:
            The interactions, or None when the file is not a VCR cassette.
        """
        data = load_yaml(file_path)
        if not is_cassette(data):
            return None
        return parse_cassette(data)

    def load_cassettes(
        self,
        directory: Path,
        channel_name: str | None = None,
    ) -> tuple[list[Cassette], list[tuple[Path, str]]]:
        """Parse every discovered file that is a VCR cassette.

        Returns:
            The cassettes, plus (path, reason) for each file that failed to load.
        """
        cassettes: list[Cassette] = []
        unreadable: list[tuple[Path, str]] = []
        for path in self.discover_files(directory, channel_name):
            try:
                interactions = self.get_interactions(path)
            except Exception as exc:
                reason = str(exc).splitlines()[0] if str(exc) else type(exc).__name__
                unreadable.append((path, reason))
                continue
            if interactions is not None:
                cassettes.append(Cassette(path=path, interactions=tuple(interactions)))
        return cassettes, unreadable

    def preview_key(
        self,
        file_path: Path,
        key_path: str,
        channel_name: str | None = None,
    ) -> PreviewResult:
        """Format the value at one key path using the matching extraction rule.

        Returns:
            The formatted preview result.
        """
        data = load_yaml(file_path)
        value = get_value_at_path(data, key_path)

        channel = self.config.get_channel(channel_name)
        rule = self._find_matching_rule(key_path, channel)

        formatter: FormatterType = rule.formatter if rule else 'yaml'
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
        """Format the whole file as YAML.

        Returns:
            The formatted preview result.
        """
        data = load_yaml(file_path)
        channel = self.config.get_channel(channel_name)

        label: str | None = None
        if channel and channel.extraction_rules:
            label = channel.extraction_rules[0].label

        formatted = format_content(data, 'yaml')

        return PreviewResult(
            content=formatted,
            formatter='yaml',
            metadata={},
            source_path='.',
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

    @staticmethod
    def _path_matches_rule(key_path: str, rule_path: str) -> bool:
        if rule_path == '.':
            return True

        rule_parts = rule_path.lstrip('.').split('.')
        key_parts = key_path.split('.')

        if len(key_parts) < len(rule_parts):
            return False

        for rule_part, key_part in zip(rule_parts, key_parts, strict=False):
            if '[]' in rule_part:
                base = rule_part.replace('[]', '')
                if not key_part.startswith(base):
                    return False
            elif rule_part != key_part:
                return False

        return True

    def _extract_metadata(
        self,
        data: object,
        key_path: str,
        rule: ExtractionRule | None,
    ) -> dict[str, Any]:
        if not rule or not rule.metadata_keys:
            return {}

        metadata: dict[str, Any] = {}
        base_path = self._get_base_path(key_path)

        for meta_key in rule.metadata_keys:
            value = None
            # Metadata keys are relative to the key's parent; if not found there
            # (e.g. interaction-level status for a `.response.body.string` rule),
            # walk up the ancestor chain until the key resolves.
            for candidate in self._ancestor_paths(base_path):
                full_path = f'{candidate}.{meta_key}' if candidate else meta_key
                value = get_value_at_path(data, full_path)
                if value is not None:
                    break
            if value is not None:
                metadata[meta_key] = value

        return metadata

    @staticmethod
    def _get_base_path(key_path: str) -> str:
        parts = key_path.rsplit('.', 1)
        return parts[0] if len(parts) > 1 else ''

    @staticmethod
    def _ancestor_paths(base_path: str) -> Iterator[str]:
        """Yield base_path and each of its ancestors, innermost first, then ''.

        Index suffixes are preserved: 'a[0].b.c' -> 'a[0].b.c', 'a[0].b', 'a[0]', ''.
        """
        current = base_path
        while current:
            yield current
            parts = current.rsplit('.', 1)
            current = parts[0] if len(parts) > 1 else ''


def _cassette_or_none(data: object) -> list[Interaction] | None:
    return parse_cassette(data) if is_cassette(data) else None


def _load_versions(
    root: Path,
    changed: ChangedFile,
    ref: str,
) -> tuple[list[Interaction] | None, list[Interaction] | None]:
    """Parse a changed file at the ref and in the working tree; None where absent or no cassette."""
    old = None
    if changed.status != 'added':
        old = _cassette_or_none(load_yaml_text(read_at_ref(root, changed.path, ref)))
    new = None
    if changed.status != 'deleted':
        new = _cassette_or_none(load_yaml(changed.path))
    return old, new
