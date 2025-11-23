"""Main Textual TUI application."""

from __future__ import annotations

from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Label, Static

from vcr_tui.config.loader import load_config
from vcr_tui.preview.engine import PreviewEngine
from vcr_tui.ui.file_list import FileList
from vcr_tui.ui.preview_panel import PreviewPanel
from vcr_tui.ui.yaml_viewer import YAMLViewer


class HelpScreen(ModalScreen[None]):
    """Modal screen showing keyboard shortcuts."""

    CSS = """
    HelpScreen {
        align: center middle;
    }

    #help-dialog {
        width: 60;
        height: auto;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }

    #help-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .help-section {
        margin-top: 1;
    }

    .help-section-title {
        text-style: bold;
        color: $primary;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Close", show=False),
        Binding("q", "dismiss", "Close", show=False),
    ]

    def compose(self) -> ComposeResult:
        """Compose the help screen."""
        with Vertical(id="help-dialog"):
            yield Label("Keyboard Shortcuts", id="help-title")
            yield Label("Navigation:", classes="help-section-title")
            yield Label("  Tab         - Cycle focus forward")
            yield Label("  Shift+Tab   - Cycle focus backward")
            yield Label("  ↑/↓ or j/k  - Navigate items")
            yield Label("  Enter       - Select item")
            yield Label("  Space       - Toggle expand/collapse", classes="help-section")
            yield Label("File List:", classes="help-section-title help-section")
            yield Label("  ↑/↓         - Browse files")
            yield Label("  Enter       - Load file keys", classes="help-section")
            yield Label("Preview Panel:", classes="help-section-title help-section")
            yield Label("  Page Up/Dn  - Scroll preview")
            yield Label("  Home/End    - Jump to top/bottom", classes="help-section")
            yield Label("General:", classes="help-section-title help-section")
            yield Label("  ?           - Show this help")
            yield Label("  q           - Quit application")
            yield Label("  Esc         - Close help")

    def action_dismiss(self) -> None:
        """Dismiss the help screen."""
        self.app.pop_screen()


class VCRTUIApp(App[None]):
    """Main TUI application for VCR cassette inspection.

    A Textual-based terminal user interface for browsing and previewing
    VCR cassettes and other structured YAML files.
    """

    CSS = """
    Screen {
        layout: grid;
        grid-size: 2;
        grid-rows: auto 1fr auto;
    }

    #file-list {
        width: 40%;
        border: solid $primary;
        &:focus-within {
            border: thick $primary;
        }
    }

    #preview-container {
        width: 60%;
        layout: vertical;
    }

    #yaml-viewer {
        height: 1fr;
        border: solid $accent;
        &:focus-within {
            border: thick $accent;
        }
    }

    #preview-panel {
        height: 2fr;
        border: solid $success;
        &:focus-within {
            border: thick $success;
        }
    }

    #metadata-bar {
        height: 3;
        background: $boost;
        border-top: solid $primary;
        padding: 1 2;
    }

    .metadata-label {
        color: $text;
    }

    .metadata-value {
        color: $accent;
        text-style: bold;
    }

    .error-message {
        color: $error;
        text-style: bold;
    }

    Footer {
        column-span: 2;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("question_mark", "help", "Help", key_display="?"),
        Binding("tab", "focus_next", "Next", show=False),
        Binding("shift+tab", "focus_previous", "Previous", show=False),
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
        self.current_key: str | None = None
        self.file_count: int = 0

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()

        # Main content area
        with Grid():
            # File list on the left
            yield FileList(id="file-list")

            # Preview area on the right
            with Vertical(id="preview-container"):
                yield YAMLViewer(label="Keys", id="yaml-viewer")
                yield PreviewPanel(id="preview-panel")

        # Metadata bar at bottom
        yield Static("", id="metadata-bar", classes="metadata-label")

        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts."""
        # Discover files and populate file list
        try:
            files = self.engine.discover_files(self.directory, self.channel)
            self.file_count = len(files)
            file_list = self.query_one("#file-list", FileList)
            file_list.set_files(files)

            # Set initial focus to file list
            file_list.focus()

            # Update metadata bar
            self._update_metadata(f"Found {self.file_count} file(s). Press ? for help.")
        except Exception as e:
            self._show_error(f"Error discovering files: {e}")

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

            # Update metadata bar
            self._update_metadata(
                f"File: {file_path.name} | Keys: {len(keys)} | "
                f"Select a key to preview"
            )

            # Focus on YAML viewer for navigation
            yaml_viewer.focus()
        except FileNotFoundError:
            self._show_error(f"File not found: {file_path}")
        except ValueError as e:
            self._show_error(f"Invalid YAML: {e}")
        except Exception as e:
            self._show_error(f"Error loading file: {e}")

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

                # Store current key
                self.current_key = key

                # Update metadata bar with content info
                content_size = len(result.content)
                size_display = (
                    f"{content_size} bytes"
                    if content_size < 1024
                    else f"{content_size / 1024:.1f} KB"
                )
                formatter_display = result.formatter or "text"
                self._update_metadata(
                    f"File: {file_path.name} | Key: {key} | "
                    f"Size: {size_display} | Format: {formatter_display}"
                )

                # Focus on preview panel for scrolling
                preview_panel.focus()
            else:
                self._show_error(f"No preview available for key: {key}")
        except FileNotFoundError:
            self._show_error(f"File not found: {file_path}")
        except ValueError as e:
            self._show_error(f"Error extracting key: {e}")
        except Exception as e:
            self._show_error(f"Error previewing key: {e}")

    def _update_metadata(self, message: str) -> None:
        """Update the metadata bar with a message.

        Args:
            message: Message to display
        """
        metadata_bar = self.query_one("#metadata-bar", Static)
        metadata_bar.update(message)
        metadata_bar.remove_class("error-message")
        metadata_bar.add_class("metadata-label")

    def _show_error(self, message: str) -> None:
        """Show an error message in the metadata bar.

        Args:
            message: Error message to display
        """
        metadata_bar = self.query_one("#metadata-bar", Static)
        metadata_bar.update(f"Error: {message}")
        metadata_bar.remove_class("metadata-label")
        metadata_bar.add_class("error-message")

    def action_help(self) -> None:
        """Show the help screen."""
        self.push_screen(HelpScreen())


def run_tui(directory: Path | None = None, channel: str | None = None) -> None:
    """Run the TUI application.

    Args:
        directory: Directory to search for files
        channel: Channel to use
    """
    app = VCRTUIApp(directory=directory, channel=channel)
    app.run()
