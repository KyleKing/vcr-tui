from pathlib import Path
from typing import Any

from textual.message import Message
from textual.widgets import OptionList
from textual.widgets.option_list import Option


class FileSelected(Message):
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        super().__init__()


class FileListWidget(OptionList):
    """File list with display-only substring filtering (case-insensitive, on name)."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._files: list[Path] = []
        self._filter: str | None = None

    @property
    def filter(self) -> str | None:
        return self._filter

    def set_files(self, files: list[Path]) -> None:
        self._files = files
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
            for index, file_path in enumerate(self._visible_files()):
                if str(file_path) == highlighted_id:
                    self.highlighted = index
                    break

    def _visible_files(self) -> list[Path]:
        if self._filter is None:
            return self._files
        needle = self._filter.casefold()
        return [f for f in self._files if needle in f.name.casefold()]

    def _apply_filter(self) -> None:
        self.clear_options()
        for file_path in self._visible_files():
            self.add_option(Option(file_path.name, id=str(file_path)))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option.id:
            file_path = Path(event.option.id)
            self.post_message(FileSelected(file_path))

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        if event.option.id:
            file_path = Path(event.option.id)
            self.post_message(FileSelected(file_path))
