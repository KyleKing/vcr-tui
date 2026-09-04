# Copyright (c) 2026 Kyle King
"""Root Textual application for the VCR-TUI interface."""

from pathlib import Path

from textual.app import App

from vcr_tui.config import Config
from vcr_tui.ui.screens import MainScreen


class VCRTUIApp(App[None]):
    """Textual application hosting the main VCR browsing screen."""

    CSS_PATH = 'ui/styles/app.tcss'
    TITLE = 'VCR-TUI'

    def __init__(
        self,
        directory: Path,
        config: Config,
        channel: str | None = None,
    ) -> None:
        """Store the directory, config, and channel the screen starts from."""
        super().__init__()
        self.directory = directory
        self.config = config
        self.channel = channel

    def on_mount(self) -> None:
        """Open the main screen once the app is ready."""
        self.push_screen(MainScreen(self.directory, self.config, self.channel))
