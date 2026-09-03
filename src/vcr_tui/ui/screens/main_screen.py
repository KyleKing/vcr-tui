from pathlib import Path

from textual import events, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Footer, Header, Input

from vcr_tui.config import Config
from vcr_tui.preview import PreviewEngine
from vcr_tui.ui.widgets import (
    FileListWidget,
    FileSelected,
    KeySelected,
    MetadataBarWidget,
    PreviewPanelWidget,
    YAMLViewerWidget,
)


class FilesDiscovered(Message):
    def __init__(self, files: list[Path]) -> None:
        self.files = files
        super().__init__()


class MainScreen(Screen[None]):
    # NOTE: Screen already binds tab/shift+tab to app.focus_next/app.focus_previous;
    # do not override them with a bare 'focus_next' action — that action does not
    # exist on Screen and Tab silently stops moving focus.
    BINDINGS = [
        Binding('q', 'quit', 'Quit'),
        Binding('r', 'reload_files', 'Reload files'),
        Binding('/', 'filter_files', 'Filter files'),
    ]

    FILTER_INPUT_ID = 'filter-input'

    def __init__(
        self,
        directory: Path,
        config: Config,
        channel: str | None = None,
    ) -> None:
        super().__init__()
        self.directory = directory
        self.config = config
        self.channel = channel
        self.engine = PreviewEngine(config)
        self._current_file: Path | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id='main-container'):
            with Vertical(id='sidebar'):
                yield Input(placeholder='Filter files…', id=self.FILTER_INPUT_ID)
                yield FileListWidget(id='file-list')
            with Vertical(id='content-container'):
                yield YAMLViewerWidget(id='yaml-viewer')
                yield PreviewPanelWidget(id='preview-panel')
                yield MetadataBarWidget(id='metadata-bar')
        yield Footer()

    def on_mount(self) -> None:
        self._discover_files()
        self.query_one('#file-list').focus()

    def action_reload_files(self) -> None:
        self._discover_files()

    def action_filter_files(self) -> None:
        self.query_one(f'#{self.FILTER_INPUT_ID}', Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == self.FILTER_INPUT_ID:
            self.query_one('#file-list', FileListWidget).set_filter(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == self.FILTER_INPUT_ID:
            self.query_one('#file-list', FileListWidget).set_filter(event.value)
            self.query_one('#file-list', FileListWidget).focus()

    def on_key(self, event: events.Key) -> None:
        if event.key != 'escape':
            return
        file_list = self.query_one('#file-list', FileListWidget)
        input_focused = self.focused is not None and self.focused.id == self.FILTER_INPUT_ID
        if input_focused or file_list.filter is not None:
            event.stop()
            self._clear_filter()

    def _clear_filter(self) -> None:
        filter_input = self.query_one(f'#{self.FILTER_INPUT_ID}', Input)
        filter_input.value = ''
        self.query_one('#file-list', FileListWidget).set_filter(None)
        self.query_one('#file-list', FileListWidget).focus()

    @work(thread=True, exclusive=True)
    def _discover_files(self) -> None:
        files = self.engine.discover_files(self.directory, self.channel)
        self.post_message(FilesDiscovered(files))

    def on_files_discovered(self, event: FilesDiscovered) -> None:
        files = event.files
        file_list = self.query_one('#file-list', FileListWidget)
        file_list.set_files(files)

        if not files:
            self._current_file = None
            return

        current = self._current_file
        selected = current if current is not None and current in files else files[0]
        self._current_file = selected
        file_list.highlighted = files.index(selected)
        self._load_keys(selected)

    def _load_keys(self, file_path: Path) -> None:
        keys = self.engine.get_keys(file_path)
        yaml_viewer = self.query_one('#yaml-viewer', YAMLViewerWidget)
        yaml_viewer.set_keys(keys)

    def on_file_selected(self, event: FileSelected) -> None:
        self._current_file = event.file_path
        self._load_keys(event.file_path)

        preview_panel = self.query_one('#preview-panel', PreviewPanelWidget)
        metadata_bar = self.query_one('#metadata-bar', MetadataBarWidget)
        preview_panel.clear_preview()
        metadata_bar.clear_metadata()

    def on_key_selected(self, event: KeySelected) -> None:
        if not self._current_file:
            return

        result = self.engine.preview_key(
            self._current_file,
            event.key.path,
            self.channel,
        )

        preview_panel = self.query_one('#preview-panel', PreviewPanelWidget)
        metadata_bar = self.query_one('#metadata-bar', MetadataBarWidget)

        preview_panel.set_preview(result)
        metadata_bar.set_metadata(result.metadata)

    def action_quit(self) -> None:
        self.app.exit()
