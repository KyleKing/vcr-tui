# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""Widget listing a cassette's recorded HTTP interactions, one row each."""

from typing import Any, ClassVar

from textual.binding import Binding
from textual.message import Message
from textual.widgets import OptionList
from textual.widgets.option_list import Option

from vcr_tui.preview.cassette import Interaction, format_row


class InteractionSelected(Message):
    """Posted when the user highlights or picks an interaction."""

    def __init__(self, interaction: Interaction) -> None:
        """Carry the selected interaction."""
        self.interaction = interaction
        super().__init__()


class InteractionListWidget(OptionList):
    """Interaction rows with display-only substring filtering (case-insensitive, on the row)."""

    BINDINGS: ClassVar[list[Binding]] = [
        Binding('j', 'cursor_down', 'Down', show=False),
        Binding('k', 'cursor_up', 'Up', show=False),
    ]

    def __init__(self, **kwargs: Any) -> None:
        """Set up the empty list with no filter."""
        super().__init__(**kwargs)
        self._interactions: list[Interaction] = []
        self._filter: str | None = None

    @property
    def filter(self) -> str | None:
        """The active filter, or None when unfiltered."""
        return self._filter

    def set_interactions(self, interactions: list[Interaction]) -> None:
        """Replace the full interaction list and reapply the filter."""
        self._interactions = interactions
        self._apply_filter()

    def set_filter(self, text: str | None) -> None:
        """Set the display filter; None or '' clears it (full set is kept)."""
        self._filter = text or None
        highlighted_id = None
        if self.highlighted is not None:
            option = self.get_option_at_index(self.highlighted)
            highlighted_id = option.id if option else None
        self._apply_filter()
        if highlighted_id is not None:
            for index, interaction in enumerate(self._visible_interactions()):
                if str(interaction.index) == highlighted_id:
                    self.highlighted = index
                    break

    def _visible_interactions(self) -> list[Interaction]:
        if self._filter is None:
            return self._interactions
        needle = self._filter.casefold()
        return [i for i in self._interactions if needle in format_row(i).casefold()]

    def _apply_filter(self) -> None:
        self.clear_options()
        for interaction in self._visible_interactions():
            self.add_option(Option(format_row(interaction), id=str(interaction.index)))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Post InteractionSelected when a row is chosen."""
        if interaction := self._find(event.option.id):
            self.post_message(InteractionSelected(interaction))

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        """Post InteractionSelected as the highlight moves."""
        if interaction := self._find(event.option.id):
            self.post_message(InteractionSelected(interaction))

    def _find(self, option_id: str | None) -> Interaction | None:
        if option_id is None:
            return None
        return next((i for i in self._interactions if str(i.index) == option_id), None)
