from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

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


class MainScreen(Screen):
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("tab", "focus_next", "Next Panel", show=False),
        Binding("shift+tab", "focus_previous", "Prev Panel", show=False),
    ]

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
        with Horizontal(id="main-container"):
            yield FileListWidget(id="file-list")
            with Vertical(id="content-container"):
                yield YAMLViewerWidget(id="yaml-viewer")
                yield PreviewPanelWidget(id="preview-panel")
                yield MetadataBarWidget(id="metadata-bar")
        yield Footer()

    def on_mount(self) -> None:
        self._load_files()
        self.query_one("#file-list").focus()

    def _load_files(self) -> None:
        files = self.engine.discover_files(self.directory, self.channel)
        file_list = self.query_one("#file-list", FileListWidget)
        file_list.set_files(files)

        if files:
            self._current_file = files[0]
            self._load_keys(files[0])

    def _load_keys(self, file_path: Path) -> None:
        keys = self.engine.get_keys(file_path)
        yaml_viewer = self.query_one("#yaml-viewer", YAMLViewerWidget)
        yaml_viewer.set_keys(keys)

    def on_file_selected(self, event: FileSelected) -> None:
        self._current_file = event.file_path
        self._load_keys(event.file_path)

        preview_panel = self.query_one("#preview-panel", PreviewPanelWidget)
        metadata_bar = self.query_one("#metadata-bar", MetadataBarWidget)
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

        preview_panel = self.query_one("#preview-panel", PreviewPanelWidget)
        metadata_bar = self.query_one("#metadata-bar", MetadataBarWidget)

        preview_panel.set_preview(result)
        metadata_bar.set_metadata(result.metadata)

    def action_quit(self) -> None:
        self.app.exit()
