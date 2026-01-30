from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ExtractionRule:
    path: str
    formatter: str
    label: str | None = None
    metadata_keys: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExtractionRule":
        return cls(
            path=data["path"],
            formatter=data["formatter"],
            label=data.get("label"),
            metadata_keys=tuple(data.get("metadata_keys", [])),
        )


@dataclass(frozen=True)
class Channel:
    name: str
    glob_patterns: tuple[str, ...]
    extraction_rules: tuple[ExtractionRule, ...]
    enabled: bool = True

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> "Channel":
        rules = tuple(ExtractionRule.from_dict(r) for r in data.get("extraction_rules", []))
        return cls(
            name=name,
            glob_patterns=tuple(data.get("glob_patterns", [])),
            extraction_rules=rules,
            enabled=data.get("enabled", True),
        )


@dataclass(frozen=True)
class Config:
    root: bool = False
    channels: tuple[Channel, ...] = ()
    default_channel: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Config":
        channels_data = data.get("channels", {})
        channels = tuple(
            Channel.from_dict(name, ch_data) for name, ch_data in channels_data.items()
        )
        return cls(
            root=data.get("root", False),
            channels=channels,
            default_channel=data.get("default_channel"),
        )

    def get_channel(self, name: str | None = None) -> Channel | None:
        target = name or self.default_channel
        if not target:
            return self.channels[0] if self.channels else None
        return next((ch for ch in self.channels if ch.name == target), None)

    def merge(self, other: "Config") -> "Config":
        existing_names = {ch.name for ch in self.channels}
        merged_channels = list(self.channels)
        for ch in other.channels:
            if ch.name not in existing_names:
                merged_channels.append(ch)
        return Config(
            root=other.root or self.root,
            channels=tuple(merged_channels),
            default_channel=other.default_channel or self.default_channel,
        )
