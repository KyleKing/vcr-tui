# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""Shared type definitions for the preview subsystem."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PreviewResult:
    """A formatted value ready for display, plus where it came from."""

    content: str
    formatter: str
    metadata: dict[str, Any]
    source_path: str
    label: str | None = None


@dataclass(frozen=True)
class YAMLKey:
    """One selectable line of a YAML document."""

    path: str
    display: str
    depth: int
    is_leaf: bool
