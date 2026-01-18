from pathlib import Path

from textual.message import Message
from textual.reactive import reactive
from textual.widgets import OptionList
from textual.widgets.option_list import Option


class FileSelected(Message):
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        super().__init__()


class FileListWidget(OptionList):
    files: reactive[list[Path]] = reactive(list, init=False)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._files: list[Path] = []

    def set_files(self, files: list[Path]) -> None:
        self._files = files
        self.clear_options()
        for file_path in files:
            self.add_option(Option(file_path.name, id=str(file_path)))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option.id:
            file_path = Path(event.option.id)
            self.post_message(FileSelected(file_path))

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        if event.option.id:
            file_path = Path(event.option.id)
            self.post_message(FileSelected(file_path))
