# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""Parse syrupy's amber (``.ambr``) snapshot files into named snapshots.

An amber file holds one block per snapshot::

    # serializer version: 1
    # name: TestUsers.test_get[admin]
      dict({
        'id': 1,
      })
    # ---

Block bodies are indented two spaces and end at a ``# ---`` line.
"""

from dataclasses import dataclass
from pathlib import Path

AMBER_SUFFIX = '.ambr'
_NAME = '# name: '
_END = '# ---'
_INDENT = '  '
_KIND_PREFIXES = (
    ('dict(', 'dict'),
    ('list(', 'list'),
    ('tuple(', 'tuple'),
    ('set(', 'set'),
    ("'", 'str'),
    ('"', 'str'),
    ("b'", 'bytes'),
    ('<', 'object'),
)


@dataclass(frozen=True)
class AmberSnapshot:
    """One named snapshot block and where it starts in the file."""

    index: int
    name: str
    body: str
    line: int

    @property
    def test_name(self) -> str:
        """The test function's name: no class prefix, parameter id, or ``.N`` suffix."""
        bare = self.name.split('[', 1)[0]
        parts = bare.split('.')
        if len(parts) > 1 and parts[-1].isdigit():
            parts = parts[:-1]
        return parts[-1]

    @property
    def kind(self) -> str:
        """A rough type for the snapshot value, e.g. dict, list, str, or other."""
        first = self.body.lstrip()
        if first[:1].isdigit() or first[:1] == '-':
            return 'number'
        return next((kind for prefix, kind in _KIND_PREFIXES if first.startswith(prefix)), 'other')

    @property
    def line_count(self) -> int:
        """Number of lines in the snapshot body."""
        return len(self.body.splitlines()) if self.body else 0


def is_amber_path(path: Path) -> bool:
    """Whether the path names an amber snapshot file."""
    return path.suffix == AMBER_SUFFIX


def parse_amber(text: str) -> list[AmberSnapshot]:
    """Split amber text into snapshots; an unterminated last block is still kept.

    Returns:
        The snapshots in file order.
    """
    snapshots: list[AmberSnapshot] = []
    name: str | None = None
    start = 0
    body: list[str] = []

    def close() -> None:
        snapshots.append(AmberSnapshot(len(snapshots), name or '', '\n'.join(body), start))

    for number, line in enumerate(text.splitlines(), start=1):
        if name is None:
            if line.startswith(_NAME):
                name, start, body = line[len(_NAME) :].strip(), number, []
            continue
        if line.rstrip() == _END:
            close()
            name = None
            continue
        body.append(line.removeprefix(_INDENT))
    if name is not None:
        close()
    return snapshots


def format_snapshot_row(snapshot: AmberSnapshot) -> str:
    """Render a snapshot as one aligned summary line."""
    return f'{snapshot.index:>3}  {snapshot.kind:<6} {snapshot.line_count:>5}L  {snapshot.name}'
