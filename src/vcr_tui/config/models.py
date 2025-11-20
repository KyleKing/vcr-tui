"""Configuration data models for vcr-tui."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExtractionRule:
    """Rule for extracting and processing data from files.

    Attributes:
        path: yq/jq path expression (e.g., ".body.string")
        formatter: Format type for display ("html", "json", "text", "toml", "yaml")
        label: Optional display label for this extraction
        metadata_keys: Optional list of keys to show as metadata
    """

    path: str
    formatter: str
    label: str | None = None
    metadata_keys: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for TOML serialization."""
        result: dict[str, Any] = {
            "path": self.path,
            "formatter": self.formatter,
        }
        if self.label:
            result["label"] = self.label
        if self.metadata_keys:
            result["metadata_keys"] = self.metadata_keys
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExtractionRule:
        """Create from dictionary (TOML deserialization)."""
        return cls(
            path=data["path"],
            formatter=data["formatter"],
            label=data.get("label"),
            metadata_keys=data.get("metadata_keys", []),
        )


@dataclass
class Channel:
    """A channel defines file patterns and extraction rules.

    Similar to television channels - each channel provides a different
    view of the same files with different extraction and formatting rules.

    Attributes:
        name: Channel identifier
        glob_patterns: List of glob patterns for file discovery
        extraction_rules: List of extraction rules to apply
        enabled: Whether this channel is active
    """

    name: str
    glob_patterns: list[str] = field(default_factory=list)
    extraction_rules: list[ExtractionRule] = field(default_factory=list)
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for TOML serialization."""
        return {
            "name": self.name,
            "glob_patterns": self.glob_patterns,
            "extraction_rules": [rule.to_dict() for rule in self.extraction_rules],
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> Channel:
        """Create from dictionary (TOML deserialization)."""
        extraction_rules = [
            ExtractionRule.from_dict(rule_data)
            for rule_data in data.get("extraction_rules", [])
        ]
        return cls(
            name=name,
            glob_patterns=data.get("glob_patterns", []),
            extraction_rules=extraction_rules,
            enabled=data.get("enabled", True),
        )


@dataclass
class Config:
    """Complete vcr-tui configuration.

    Attributes:
        root: If True, stop searching for parent configs
        channels: Dictionary mapping channel names to Channel objects
        default_channel: Name of the default channel to use
    """

    root: bool = False
    channels: dict[str, Channel] = field(default_factory=dict)
    default_channel: str | None = None

    def get_channel(self, name: str | None = None) -> Channel | None:
        """Get a channel by name, or the default channel if name is None."""
        channel_name = name or self.default_channel
        if channel_name is None:
            return None
        return self.channels.get(channel_name)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for TOML serialization."""
        result: dict[str, Any] = {"root": self.root}

        if self.channels:
            channels_dict = {}
            for name, channel in self.channels.items():
                channels_dict[name] = channel.to_dict()
            result["channels"] = channels_dict

        if self.default_channel:
            result["default_channel"] = self.default_channel

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        """Create from dictionary (TOML deserialization)."""
        channels_data = data.get("channels", {})
        channels = {
            name: Channel.from_dict(name, channel_data)
            for name, channel_data in channels_data.items()
        }

        return cls(
            root=data.get("root", False),
            channels=channels,
            default_channel=data.get("default_channel"),
        )

    def merge(self, other: Config) -> Config:
        """Merge another config into this one, with other taking precedence.

        Args:
            other: Config to merge (takes precedence over self)

        Returns:
            New Config with merged values
        """
        # Start with a copy of self's channels
        merged_channels = dict(self.channels)

        # Override with other's channels
        merged_channels.update(other.channels)

        return Config(
            root=other.root if other.root else self.root,
            channels=merged_channels,
            default_channel=other.default_channel or self.default_channel,
        )
