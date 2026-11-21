# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""Screen showing how each changed cassette differs from a git ref, interaction by interaction."""

from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar

from rich.console import Group, RenderableType
from rich.rule import Rule
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from vcr_tui.preview.cassette import Interaction
from vcr_tui.preview.diff import CassetteDiff, Change, describe_change

KIND_STYLES = {'added': 'green', 'removed': 'red', 'changed': 'yellow'}


def render_diff_report(
    diffs: Sequence[CassetteDiff],
    root: Path,
    ref: str,
    unreadable: Sequence[tuple[Path, str]] = (),
) -> Group:
    """Build the rich renderable for a set of cassette diffs.

    Returns:
        One section per changed cassette, or a note when nothing changed.
    """
    shown = [d for d in diffs if not d.is_empty]
    parts: list[RenderableType] = [
        Text(f'{len(shown)} cassette(s) changed since {ref}', style='bold'),
    ]
    parts.extend(
        Text(f'could not parse {_relative(path, root)}: {reason}', style='red')
        for path, reason in unreadable
    )
    for diff in shown:
        heading = (
            f'{_relative(diff.path, root)} ({diff.status}): {len(diff.changed)} changed, '
            f'{len(diff.added)} added, {len(diff.removed)} removed, {diff.unchanged} unchanged'
        )
        parts.append(Rule(heading, align='left', style='dim'))
        for item in diff.changed:
            moved = f'  (was #{item.old.index})' if item.old.index != item.new.index else ''
            parts.append(Text(f'~ {_summary(item.new)}{moved}', style='bold yellow'))
            parts.extend(_change_lines(change) for change in item.changes)
        parts.extend(
            Text(f'+ {_summary(i)}  {i.status}', style='bold green') for i in diff.added
        )
        parts.extend(Text(f'- {_summary(i)}  {i.status}', style='bold red') for i in diff.removed)
    return Group(*parts)


def _summary(interaction: Interaction) -> str:
    return f'#{interaction.index} {interaction.method} {interaction.uri}'


def _change_lines(change: Change) -> Text:
    text = Text(f'    {describe_change(change)}', style=KIND_STYLES[change.kind])
    for line in change.lines:
        style = 'green' if line.startswith('+') else 'red' if line.startswith('-') else 'dim'
        text.append(f'\n      {line}', style=style)
    return text


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


class DiffScreen(Screen[None]):
    """Read-only view of cassette changes against a git ref."""

    BINDINGS: ClassVar[list[Binding]] = [
        Binding('escape', 'app.pop_screen', 'Back'),
        Binding('d', 'app.pop_screen', 'Back', show=False),
    ]

    def __init__(
        self,
        diffs: Sequence[CassetteDiff],
        root: Path,
        ref: str,
        unreadable: Sequence[tuple[Path, str]] = (),
    ) -> None:
        """Keep the diffs and the context they are rendered in."""
        super().__init__()
        self.diffs = list(diffs)
        self.root = root
        self.ref = ref
        self.unreadable = list(unreadable)

    def compose(self) -> ComposeResult:
        """Lay out the scrolling diff between the header and footer.

        Yields:
            The widgets of the diff screen.
        """
        yield Header()
        with VerticalScroll(id='diff-scroll'):
            report = render_diff_report(self.diffs, self.root, self.ref, self.unreadable)
            yield Static(report, id='diff-report')
        yield Footer()

    def on_mount(self) -> None:
        """Title the screen with the ref and focus the scroll area."""
        changed = sum(1 for d in self.diffs if not d.is_empty)
        self.sub_title = f'diff vs {self.ref}: {changed} cassette(s) changed'
        self.query_one('#diff-scroll').focus()
