# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""Compare two versions of a cassette interaction by interaction.

Pure functions over parsed interactions: interactions are paired by method and
URL path in recorded order, then compared on status, headers, and bodies. JSON
bodies are compared field by field, so a re-recorded cassette shows which
values changed rather than a wall of YAML.
"""

import difflib
import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit, urlunsplit

from vcr_tui.preview.cassette import Body, HttpMessage, Interaction

ChangeKind = Literal['added', 'removed', 'changed']
FileStatus = Literal['added', 'deleted', 'modified']

VOLATILE_HEADERS = frozenset({
    'age',
    'cf-ray',
    'content-length',
    'date',
    'etag',
    'expires',
    'last-modified',
    'request-id',
    'server-timing',
    'traceparent',
    'x-amz-cf-id',
    'x-amzn-requestid',
    'x-amzn-trace-id',
    'x-cache',
    'x-correlation-id',
    'x-request-id',
    'x-runtime',
    'x-trace-id',
})
_VALUE_WIDTH = 80
_MISSING = object()


@dataclass(frozen=True)
class DiffOptions:
    """What to leave out of a comparison and how much text diff to keep."""

    ignore_headers: frozenset[str] = VOLATILE_HEADERS
    ignore_fields: frozenset[str] = field(default_factory=frozenset)
    max_text_lines: int = 20


@dataclass(frozen=True)
class Change:
    """One difference within a paired interaction.

    ``section`` is ``status``, ``request.uri``, ``request.headers``,
    ``request.body``, ``response.headers``, or ``response.body``; ``path`` is
    the header name or JSON path (``$.items[0].id``), empty for whole values.
    A text body diff carries unified-diff ``lines`` instead of before/after.
    """

    section: str
    kind: ChangeKind
    path: str = ''
    before: str | None = None
    after: str | None = None
    lines: tuple[str, ...] = ()


@dataclass(frozen=True)
class InteractionDiff:
    """A paired interaction and everything that changed in it."""

    old: Interaction
    new: Interaction
    changes: tuple[Change, ...]


@dataclass(frozen=True)
class CassetteDiff:
    """Everything that changed in one cassette file."""

    path: Path
    status: FileStatus
    added: tuple[Interaction, ...] = ()
    removed: tuple[Interaction, ...] = ()
    changed: tuple[InteractionDiff, ...] = ()
    unchanged: int = 0

    @property
    def is_empty(self) -> bool:
        """Whether nothing a reviewer would care about changed."""
        return not (self.added or self.removed or self.changed)


def diff_cassette(
    path: Path,
    old: Sequence[Interaction] | None,
    new: Sequence[Interaction] | None,
    options: DiffOptions | None = None,
) -> CassetteDiff:
    """Compare two versions of a cassette; None means the file did not exist.

    Returns:
        The differences, with added and removed interactions in recorded order.
    """
    options = options or DiffOptions()
    if old is None:
        return CassetteDiff(path, 'added', added=tuple(new or ()))
    if new is None:
        return CassetteDiff(path, 'deleted', removed=tuple(old))

    pending: dict[tuple[str, str], list[Interaction]] = {}
    for interaction in old:
        pending.setdefault(_pair_key(interaction), []).append(interaction)

    added: list[Interaction] = []
    changed: list[InteractionDiff] = []
    unchanged = 0
    for interaction in new:
        candidates = pending.get(_pair_key(interaction))
        if not candidates:
            added.append(interaction)
            continue
        before = candidates.pop(0)
        changes = compare_interactions(before, interaction, options)
        if changes:
            changed.append(InteractionDiff(before, interaction, changes))
        else:
            unchanged += 1

    removed = sorted((i for group in pending.values() for i in group), key=lambda i: i.index)
    return CassetteDiff(
        path,
        'modified',
        added=tuple(added),
        removed=tuple(removed),
        changed=tuple(changed),
        unchanged=unchanged,
    )


def compare_interactions(
    old: Interaction,
    new: Interaction,
    options: DiffOptions | None = None,
) -> tuple[Change, ...]:
    """List what changed between two interactions paired as the same call.

    Returns:
        The changes, in section order: status, URI, request, response.
    """
    options = options or DiffOptions()
    changes: list[Change] = []
    if old.status_code != new.status_code:
        changes.append(Change('status', 'changed', before=old.status, after=new.status))
    if old.uri != new.uri:
        changes.append(Change('request.uri', 'changed', before=old.uri, after=new.uri))
    for side, before, after in (
        ('request', old.request, new.request),
        ('response', old.response, new.response),
    ):
        changes.extend(_header_changes(f'{side}.headers', before, after, options))
        changes.extend(_body_changes(f'{side}.body', before.body, after.body, options))
    return tuple(changes)


def json_changes(
    before: object,
    after: object,
    ignore_fields: Iterable[str] = (),
    path: str = '$',
) -> list[Change]:
    """Compare two parsed JSON values structurally.

    Returns:
        One change per added, removed, or changed leaf (or mismatched type),
        with ``section`` left empty for the caller to fill in.
    """
    ignored = frozenset(ignore_fields)
    if isinstance(before, dict) and isinstance(after, dict):
        changes: list[Change] = []
        for key in sorted(before.keys() | after.keys(), key=str):
            if key in ignored:
                continue
            child = f'{path}.{key}'
            old_value = before.get(key, _MISSING)
            new_value = after.get(key, _MISSING)
            changes.extend(_leaf_or_recurse(old_value, new_value, ignored, child))
        return changes
    if isinstance(before, list) and isinstance(after, list):
        changes = []
        for index in range(max(len(before), len(after))):
            old_item = before[index] if index < len(before) else _MISSING
            new_item = after[index] if index < len(after) else _MISSING
            changes.extend(_leaf_or_recurse(old_item, new_item, ignored, f'{path}[{index}]'))
        return changes
    if before != after or type(before) is not type(after):
        return [Change('', 'changed', path, _show(before), _show(after))]
    return []


def _leaf_or_recurse(
    before: object,
    after: object,
    ignored: frozenset[str],
    path: str,
) -> list[Change]:
    if before is _MISSING:
        return [Change('', 'added', path, after=_show(after))]
    if after is _MISSING:
        return [Change('', 'removed', path, before=_show(before))]
    return json_changes(before, after, ignored, path)


def _pair_key(interaction: Interaction) -> tuple[str, str]:
    parts = urlsplit(interaction.uri)
    return interaction.method, urlunsplit((parts.scheme, parts.netloc, parts.path, '', ''))


def _header_changes(
    section: str,
    before: HttpMessage,
    after: HttpMessage,
    options: DiffOptions,
) -> list[Change]:
    ignored = {name.casefold() for name in options.ignore_headers}
    old = _flat_headers(before, ignored)
    new = _flat_headers(after, ignored)
    changes: list[Change] = []
    for name in sorted(old.keys() | new.keys()):
        if name not in new:
            changes.append(Change(section, 'removed', name, before=old[name]))
        elif name not in old:
            changes.append(Change(section, 'added', name, after=new[name]))
        elif old[name] != new[name]:
            changes.append(Change(section, 'changed', name, old[name], new[name]))
    return changes


def _flat_headers(message: HttpMessage, ignored: set[str]) -> dict[str, str]:
    return {
        name.casefold(): ', '.join(values)
        for name, values in message.headers.items()
        if name.casefold() not in ignored
    }


def _body_changes(section: str, before: Body, after: Body, options: DiffOptions) -> list[Change]:
    if before.text == after.text:
        return []
    if before.kind == 'empty':
        return [Change(section, 'added', after=_truncate(after.text))]
    if after.kind == 'empty':
        return [Change(section, 'removed', before=_truncate(before.text))]
    if before.kind == 'json' and after.kind == 'json':
        changes = json_changes(
            json.loads(before.text),
            json.loads(after.text),
            options.ignore_fields,
        )
        return [Change(section, c.kind, c.path, c.before, c.after) for c in changes]
    return [Change(section, 'changed', lines=_text_diff(before.text, after.text, options))]


def _text_diff(before: str, after: str, options: DiffOptions) -> tuple[str, ...]:
    lines = [
        line
        for line in difflib.unified_diff(
            before.splitlines(),
            after.splitlines(),
            lineterm='',
            n=1,
        )
        if not line.startswith(('---', '+++'))
    ]
    if len(lines) > options.max_text_lines:
        hidden = len(lines) - options.max_text_lines
        lines = [*lines[: options.max_text_lines], f'... {hidden} more diff lines']
    return tuple(lines)


def _show(value: object) -> str:
    return _truncate(json.dumps(value, ensure_ascii=False, sort_keys=True))


def _truncate(text: str) -> str:
    flat = ' '.join(text.split())
    return flat if len(flat) <= _VALUE_WIDTH else f'{flat[: _VALUE_WIDTH - 3]}...'


def describe_change(change: Change) -> str:
    """Render one change as a single line (text diffs excluded).

    Returns:
        e.g. ``~ response.body $.user.name: "Ann" -> "Anne"``.
    """
    target = f'{change.section} {change.path}'.strip()
    if change.kind == 'added':
        return f'+ {target}: {change.after}'
    if change.kind == 'removed':
        return f'- {target}: {change.before}'
    if change.lines:
        return f'~ {target}'
    return f'~ {target}: {change.before} -> {change.after}'


def render_diffs(diffs: Sequence[CassetteDiff], root: Path) -> str:
    """Render cassette diffs as plain text for the CLI.

    Returns:
        The multi-line report, or a one-line note when nothing changed.
    """
    shown = [d for d in diffs if not d.is_empty]
    if not shown:
        return 'No cassette changes.'
    lines: list[str] = []
    for diff in shown:
        lines.extend((_file_heading(diff, root), *_diff_lines(diff), ''))
    lines.append(f'{len(shown)} cassette(s) changed')
    return '\n'.join(lines)


def _file_heading(diff: CassetteDiff, root: Path) -> str:
    counts = (
        f'{len(diff.changed)} changed, {len(diff.added)} added, '
        f'{len(diff.removed)} removed, {diff.unchanged} unchanged'
    )
    return f'{_relative(diff.path, root)} ({diff.status}): {counts}'


def _diff_lines(diff: CassetteDiff) -> list[str]:
    lines: list[str] = []
    for item in diff.changed:
        moved = f'  (was #{item.old.index})' if item.old.index != item.new.index else ''
        lines.append(f'  ~ #{item.new.index} {item.new.method} {item.new.uri}{moved}')
        for change in item.changes:
            lines.append(f'      {describe_change(change)}')
            lines.extend(f'        {line}' for line in change.lines)
    lines.extend(f'  + #{i.index} {i.method} {i.uri}  {i.status}' for i in diff.added)
    lines.extend(f'  - #{i.index} {i.method} {i.uri}  {i.status}' for i in diff.removed)
    return lines


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def diffs_to_dict(diffs: Sequence[CassetteDiff], root: Path) -> list[dict[str, object]]:
    """Convert cassette diffs to JSON-ready data, skipping files with no changes.

    Returns:
        One dict per changed cassette.
    """

    def summary(i: Interaction) -> dict[str, object]:
        return {'index': i.index, 'method': i.method, 'uri': i.uri, 'status': i.status_code}

    def change(c: Change) -> dict[str, object]:
        return {
            'section': c.section,
            'kind': c.kind,
            'path': c.path,
            'before': c.before,
            'after': c.after,
            'lines': list(c.lines),
        }

    return [
        {
            'path': _relative(d.path, root),
            'status': d.status,
            'unchanged': d.unchanged,
            'added': [summary(i) for i in d.added],
            'removed': [summary(i) for i in d.removed],
            'changed': [
                {
                    'old_index': item.old.index,
                    **summary(item.new),
                    'changes': [change(c) for c in item.changes],
                }
                for item in d.changed
            ],
        }
        for d in diffs
        if not d.is_empty
    ]
