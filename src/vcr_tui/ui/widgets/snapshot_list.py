# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""Widget listing the named snapshots in a syrupy amber file, one row each."""

from typing import Any, ClassVar

from textual.binding import Binding
from textual.message import Message
from textual.widgets import OptionList
from textual.widgets.option_list import Option

from vcr_tui.preview.amber import AmberSnapshot, format_snapshot_row


class SnapshotSelected(Message):
    """Posted when the user highlights or picks a snapshot."""

    def __init__(self, snapshot: AmberSnapshot) -> None:
        """Carry the selected snapshot."""
        self.snapshot = snapshot
        super().__init__()


class SnapshotListWidget(OptionList):
    """Snapshot rows with display-only substring filtering (case-insensitive, on the row)."""

    BINDINGS: ClassVar[list[Binding]] = [
        Binding('j', 'cursor_down', 'Down', show=False),
        Binding('k', 'cursor_up', 'Up', show=False),
    ]

    def __init__(self, **kwargs: Any) -> None:
        """Set up the empty list with no filter."""
        super().__init__(**kwargs)
        self._snapshots: list[AmberSnapshot] = []
        self._filter: str | None = None

    @property
    def filter(self) -> str | None:
        """The active filter, or None when unfiltered."""
        return self._filter

    def set_snapshots(self, snapshots: list[AmberSnapshot]) -> None:
        """Replace the full snapshot list and reapply the filter."""
        self._snapshots = snapshots
        self._apply_filter()

    def set_filter(self, text: str | None) -> None:
        """Set the display filter; None or '' clears it (full set is kept)."""
        self._filter = text or None
        self._apply_filter()

    def _visible_snapshots(self) -> list[AmberSnapshot]:
        if self._filter is None:
            return self._snapshots
        needle = self._filter.casefold()
        return [s for s in self._snapshots if needle in format_snapshot_row(s).casefold()]

    def _apply_filter(self) -> None:
        self.clear_options()
        for snapshot in self._visible_snapshots():
            self.add_option(Option(format_snapshot_row(snapshot), id=str(snapshot.index)))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Post SnapshotSelected when a row is chosen."""
        if snapshot := self._find(event.option.id):
            self.post_message(SnapshotSelected(snapshot))

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        """Post SnapshotSelected as the highlight moves."""
        if snapshot := self._find(event.option.id):
            self.post_message(SnapshotSelected(snapshot))

    def _find(self, option_id: str | None) -> AmberSnapshot | None:
        if option_id is None:
            return None
        return next((s for s in self._snapshots if str(s.index) == option_id), None)
