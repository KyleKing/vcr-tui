from pathlib import Path

from textual.app import App

from vcr_tui.config import Config
from vcr_tui.ui.screens import MainScreen


class VCRTUIApp(App):
    CSS_PATH = "ui/styles/app.tcss"
    TITLE = "VCR-TUI"

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

    def on_mount(self) -> None:
        self.push_screen(MainScreen(self.directory, self.config, self.channel))
