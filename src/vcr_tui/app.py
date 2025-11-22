"""Main Textual TUI application."""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Footer, Header, Static

from vcr_tui.config.loader import load_config
from vcr_tui.preview.engine import PreviewEngine
from vcr_tui.ui.file_list import FileList
from vcr_tui.ui.preview_panel import PreviewPanel
from vcr_tui.ui.yaml_viewer import YAMLViewer


class VCRTUIApp(App[None]):
    """Main TUI application for VCR cassette inspection.

    A Textual-based terminal user interface for browsing and previewing
    VCR cassettes and other structured YAML files.
    """

    CSS = """
    Screen {
        layout: grid;
        grid-size: 2 2;
        grid-rows: 1fr auto;
    }

    #file-list {
        column-span: 1;
        row-span: 1;
        border: solid $primary;
    }

    #preview-container {
        column-span: 1;
        row-span: 1;
        layout: vertical;
    }

    #yaml-viewer {
        height: 1fr;
        border: solid $accent;
    }

    #preview-panel {
        height: 2fr;
        border: solid $success;
    }

    #metadata-bar {
        height: auto;
        border: solid $warning;
        padding: 0 1;
    }

    Footer {
        column-span: 2;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("?", "help", "Help"),
    ]

    def __init__(
        self,
        directory: Path | None = None,
        channel: str | None = None,
    ) -> None:
        """Initialize the TUI application.

        Args:
            directory: Directory to search for files (default: current directory)
            channel: Channel to use for file discovery and extraction
        """
        super().__init__()
        self.directory = directory or Path.cwd()
        self.channel = channel

        # Load configuration and create preview engine
        self.config = load_config(self.directory)
        self.engine = PreviewEngine(self.config)

        # State
        self.current_file: Path | None = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()

        # File list on the left
        yield FileList(id="file-list")

        # Preview area on the right
        with Vertical(id="preview-container"):
            yield YAMLViewer(label="Keys", id="yaml-viewer")
            yield PreviewPanel(id="preview-panel")
            yield Static("Metadata will appear here", id="metadata-bar")

        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts."""
        # Discover files and populate file list
        files = self.engine.discover_files(self.directory, self.channel)
        file_list = self.query_one("#file-list", FileList)
        file_list.set_files(files)

    def on_file_list_selected(self, event: FileList.Selected) -> None:
        """Handle file selection from FileList widget.

        Args:
            event: ListView.Selected event
        """
        file_list = self.query_one("#file-list", FileList)
        selected_file = file_list.get_selected_file()

        if selected_file:
            self.current_file = selected_file
            self._load_file_keys(selected_file)

    def _load_file_keys(self, file_path: Path) -> None:
        """Load and display keys from a YAML file.

        Args:
            file_path: Path to the YAML file
        """
        try:
            keys = self.engine.get_yaml_keys(file_path)
            yaml_viewer = self.query_one("#yaml-viewer", YAMLViewer)
            yaml_viewer.set_keys(keys)

            # Clear preview panel when loading new file
            preview_panel = self.query_one("#preview-panel", PreviewPanel)
            preview_panel.clear_content()
        except (FileNotFoundError, ValueError):
            # Handle errors silently or show in status bar
            pass

    def on_yaml_viewer_selected(self, event: YAMLViewer.NodeSelected) -> None:
        """Handle key selection from YAMLViewer widget.

        Args:
            event: Tree.NodeSelected event
        """
        if not self.current_file:
            return

        yaml_viewer = self.query_one("#yaml-viewer", YAMLViewer)
        selected_key = yaml_viewer.get_selected_key()

        if selected_key:
            self._preview_key(self.current_file, selected_key)

    def _preview_key(self, file_path: Path, key: str) -> None:
        """Preview a specific key from a file.

        Args:
            file_path: Path to the YAML file
            key: Key path to preview
        """
        try:
            result = self.engine.preview_key(file_path, key, self.channel)

            if result:
                preview_panel = self.query_one("#preview-panel", PreviewPanel)
                preview_panel.set_content(result.content, result.formatter)
        except (FileNotFoundError, ValueError):
            # Handle errors silently or show in status bar
            pass


def run_tui(directory: Path | None = None, channel: str | None = None) -> None:
    """Run the TUI application.

    Args:
        directory: Directory to search for files
        channel: Channel to use
    """
    app = VCRTUIApp(directory=directory, channel=channel)
    app.run()
