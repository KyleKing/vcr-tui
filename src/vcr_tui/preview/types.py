from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PreviewResult:
    content: str
    formatter: str
    metadata: dict[str, Any]
    source_path: str
    label: str | None = None


@dataclass(frozen=True)
class YAMLKey:
    path: str
    display: str
    depth: int
    is_leaf: bool
