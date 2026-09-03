from dataclasses import dataclass
from itertools import starmap
from typing import Any, Literal

FormatterType = Literal['html', 'json', 'text', 'toml', 'yaml']


@dataclass(frozen=True)
class ExtractionRule:
    path: str
    formatter: FormatterType
    label: str | None = None
    metadata_keys: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'ExtractionRule':
        return cls(
            path=data['path'],
            formatter=data['formatter'],
            label=data.get('label'),
            metadata_keys=tuple(data.get('metadata_keys', [])),
        )


@dataclass(frozen=True)
class Channel:
    name: str
    glob_patterns: tuple[str, ...]
    extraction_rules: tuple[ExtractionRule, ...]
    enabled: bool = True

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> 'Channel':
        rules = tuple(ExtractionRule.from_dict(r) for r in data.get('extraction_rules', []))
        return cls(
            name=name,
            glob_patterns=tuple(data.get('glob_patterns', [])),
            extraction_rules=rules,
            enabled=data.get('enabled', True),
        )


@dataclass(frozen=True)
class Config:
    root: bool = False
    channels: tuple[Channel, ...] = ()
    default_channel: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Config':
        channels_data = data.get('channels', {})
        channels = tuple(starmap(Channel.from_dict, channels_data.items()))
        return cls(
            root=data.get('root', False),
            channels=channels,
            default_channel=data.get('default_channel'),
        )

    def get_channel(self, name: str | None = None) -> Channel | None:
        target = name or self.default_channel
        if not target:
            return self.channels[0] if self.channels else None
        return next((ch for ch in self.channels if ch.name == target), None)

    def merge(self, other: 'Config') -> 'Config':
        merged_channels = list(self.channels)
        positions = {ch.name: i for i, ch in enumerate(merged_channels)}
        for ch in other.channels:
            if ch.name in positions:
                merged_channels[positions[ch.name]] = ch
            else:
                positions[ch.name] = len(merged_channels)
                merged_channels.append(ch)
        return Config(
            root=other.root or self.root,
            channels=tuple(merged_channels),
            default_channel=other.default_channel or self.default_channel,
        )
