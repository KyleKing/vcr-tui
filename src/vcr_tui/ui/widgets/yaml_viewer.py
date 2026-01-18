from textual.binding import Binding
from textual.message import Message
from textual.widgets import OptionList
from textual.widgets.option_list import Option

from vcr_tui.preview.types import YAMLKey


class KeySelected(Message):
    def __init__(self, key: YAMLKey) -> None:
        self.key = key
        super().__init__()


class YAMLViewerWidget(OptionList):
    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._keys: list[YAMLKey] = []

    def set_keys(self, keys: list[YAMLKey]) -> None:
        self._keys = keys
        self.clear_options()
        for key in keys:
            indent = "  " * key.depth
            display = f"{indent}{key.display}"
            self.add_option(Option(display, id=key.path))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if (key := self._find_key(event.option.id)):
            self.post_message(KeySelected(key))

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        if (key := self._find_key(event.option.id)):
            self.post_message(KeySelected(key))

    def _find_key(self, path: str | None) -> YAMLKey | None:
        if not path:
            return None
        return next((k for k in self._keys if k.path == path), None)
