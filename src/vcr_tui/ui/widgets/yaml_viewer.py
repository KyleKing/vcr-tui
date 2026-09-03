"""Widget listing the selectable keys of the loaded YAML file."""

from typing import Any, ClassVar

from textual.binding import Binding
from textual.message import Message
from textual.widgets import OptionList
from textual.widgets.option_list import Option

from vcr_tui.preview.types import YAMLKey


class KeySelected(Message):
    """Posted when the user picks a YAML key."""

    def __init__(self, key: YAMLKey) -> None:
        """Carry the selected key."""
        self.key = key
        super().__init__()


class YAMLViewerWidget(OptionList):
    """Key list with display-only substring filtering (case-insensitive, on path)."""

    BINDINGS: ClassVar[list[Binding]] = [
        Binding('j', 'cursor_down', 'Down', show=False),
        Binding('k', 'cursor_up', 'Up', show=False),
    ]

    def __init__(self, **kwargs: Any) -> None:
        """Set up the empty key list with no filter."""
        super().__init__(**kwargs)
        self._keys: list[YAMLKey] = []
        self._filter: str | None = None

    @property
    def filter(self) -> str | None:
        """The active filter, or None when unfiltered."""
        return self._filter

    def set_keys(self, keys: list[YAMLKey]) -> None:
        """Replace the full key list and reapply the filter."""
        self._keys = keys
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
            for index, key in enumerate(self._visible_keys()):
                if key.path == highlighted_id:
                    self.highlighted = index
                    break

    def _visible_keys(self) -> list[YAMLKey]:
        if self._filter is None:
            return self._keys
        needle = self._filter.casefold()
        return [k for k in self._keys if needle in k.path.casefold()]

    def _apply_filter(self) -> None:
        self.clear_options()
        for key in self._visible_keys():
            indent = '  ' * key.depth
            display = f'{indent}{key.display}'
            self.add_option(Option(display, id=key.path))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Post KeySelected when a key is chosen."""
        if key := self._find_key(event.option.id):
            self.post_message(KeySelected(key))

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        """Post KeySelected as the highlight moves."""
        if key := self._find_key(event.option.id):
            self.post_message(KeySelected(key))

    def _find_key(self, path: str | None) -> YAMLKey | None:
        if not path:
            return None
        return next((k for k in self._keys if k.path == path), None)
