"""Preview engine - core logic for discovering and previewing files.

This module provides the main PreviewEngine class that ties together
the YAML parser, extractors, and formatters. It has NO Textual dependencies
and can be used independently for CLI tools or testing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from vcr_tui.config.models import Config, ExtractionRule
from vcr_tui.preview.extractors import ExtractorRegistry
from vcr_tui.preview.formatters import FormatterRegistry
from vcr_tui.preview.yaml_parser import YAMLParser


@dataclass
class PreviewResult:
    """Result of a preview operation.

    Attributes:
        content: Formatted content ready for display
        formatter: Name of formatter used
        metadata: Extracted metadata key-value pairs
        source_path: Path expression used for extraction
        label: Optional display label for this preview
    """

    content: str
    formatter: str
    metadata: dict[str, Any] = field(default_factory=dict)
    source_path: str = ""
    label: str = ""


class PreviewEngine:
    """Core preview engine with no UI dependencies.

    Discovers files, extracts data using configured rules, and formats
    content for display. Can be used standalone for CLI tools or integrated
    into a TUI application.
    """

    def __init__(self, config: Config) -> None:
        """Initialize preview engine with configuration.

        Args:
            config: Configuration object with channels and extraction rules
        """
        self.config = config
        self.parser = YAMLParser()
        self.extractor = ExtractorRegistry()
        self.formatter = FormatterRegistry()

    def discover_files(
        self, directory: Path, channel: str | None = None
    ) -> list[Path]:
        """Discover files matching channel's glob patterns.

        Args:
            directory: Directory to search for files
            channel: Channel name (uses default if None)

        Returns:
            List of matching file paths
        """
        channel_obj = self.config.get_channel(channel)
        if not channel_obj or not channel_obj.enabled:
            return []

        matches: list[Path] = []
        for pattern in channel_obj.glob_patterns:
            matches.extend(directory.glob(pattern))

        # Return unique paths, sorted
        return sorted(set(matches))

    def get_yaml_keys(self, file_path: Path) -> list[str]:
        """Extract all keys from a YAML file in flat format.

        Args:
            file_path: Path to YAML file

        Returns:
            List of key paths (e.g., ["user.name", "items[0].id"])

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If YAML is invalid
        """
        data = self.parser.load(file_path)
        return self.parser.get_all_keys(data)

    def preview_key(
        self,
        file_path: Path,
        key_path: str,
        channel: str | None = None,
    ) -> PreviewResult | None:
        """Preview a specific key using channel's extraction rules.

        Finds an extraction rule that matches the key path, extracts the value,
        formats it, and returns a PreviewResult.

        Args:
            file_path: Path to YAML file
            key_path: Key path to preview (e.g., "items[0].name")
            channel: Channel name (uses default if None)

        Returns:
            PreviewResult if matching rule found, None otherwise
        """
        channel_obj = self.config.get_channel(channel)
        if not channel_obj or not channel_obj.enabled:
            return None

        # Load the file
        try:
            data = self.parser.load(file_path)
        except (FileNotFoundError, ValueError):
            return None

        # Find matching extraction rule
        matching_rule = self._find_matching_rule(key_path, channel_obj.extraction_rules)
        if not matching_rule:
            return None

        # Extract value using the rule's path
        extracted_values = self.extractor.extract(data, matching_rule.path)
        if not extracted_values:
            return None

        # For now, use the first extracted value
        # (array iteration can return multiple values)
        value = extracted_values[0]

        # Format the value
        try:
            formatted_content = self.formatter.format(value, matching_rule.formatter)
        except Exception:
            # If formatting fails, convert to string
            formatted_content = str(value)

        # Extract metadata if specified
        metadata = self._extract_metadata(data, matching_rule.metadata_keys)

        return PreviewResult(
            content=formatted_content,
            formatter=matching_rule.formatter,
            metadata=metadata,
            source_path=matching_rule.path,
            label=matching_rule.label or "",
        )

    def preview_file(
        self, file_path: Path, channel: str | None = None
    ) -> dict[str, PreviewResult]:
        """Preview all previewable keys in a file.

        Extracts and formats all values that match the channel's extraction rules.

        Args:
            file_path: Path to YAML file
            channel: Channel name (uses default if None)

        Returns:
            Dictionary mapping key paths to PreviewResults
        """
        results: dict[str, PreviewResult] = {}

        # Get all keys in the file
        try:
            keys = self.get_yaml_keys(file_path)
        except (FileNotFoundError, ValueError):
            return results

        # Try to preview each key
        for key in keys:
            preview = self.preview_key(file_path, key, channel)
            if preview:
                results[key] = preview

        return results

    def _find_matching_rule(
        self, key_path: str, rules: list[ExtractionRule]
    ) -> ExtractionRule | None:
        """Find extraction rule that matches the key path.

        Args:
            key_path: Key path to match (e.g., "items[0].id")
            rules: List of extraction rules to check

        Returns:
            Matching ExtractionRule or None
        """
        for rule in rules:
            if self.extractor.matches_path(key_path, rule.path):
                return rule
        return None

    def _extract_metadata(
        self, data: Any, metadata_keys: list[str]
    ) -> dict[str, Any]:
        """Extract metadata values from data.

        Args:
            data: Data structure to extract from
            metadata_keys: List of key paths to extract

        Returns:
            Dictionary of metadata key-value pairs
        """
        metadata: dict[str, Any] = {}

        for key in metadata_keys:
            try:
                value = self.parser.get_value_at_path(data, key)
                metadata[key] = value
            except (KeyError, IndexError, ValueError):
                # Skip keys that don't exist
                continue

        return metadata

    def get_previewable_keys(
        self, file_path: Path, channel: str | None = None
    ) -> list[str]:
        """Get list of keys that have matching extraction rules.

        Args:
            file_path: Path to YAML file
            channel: Channel name (uses default if None)

        Returns:
            List of previewable key paths
        """
        channel_obj = self.config.get_channel(channel)
        if not channel_obj or not channel_obj.enabled:
            return []

        # Get all keys
        try:
            all_keys = self.get_yaml_keys(file_path)
        except (FileNotFoundError, ValueError):
            return []

        # Filter to only previewable keys
        previewable = []
        for key in all_keys:
            if self._find_matching_rule(key, channel_obj.extraction_rules):
                previewable.append(key)

        return previewable
