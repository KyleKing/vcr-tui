# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""Main screen wiring the panes, filtering, and preview flow together."""

from pathlib import Path
from typing import ClassVar

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

MIN_CHANNELS_TO_CYCLE = 2


class FilesDiscovered(Message):
    """Posted when the background file scan finishes."""

    def __init__(self, files: list[Path]) -> None:
        """Carry the discovered files."""
        self.files = files
        super().__init__()


class MainScreen(Screen[None]):
    """Primary screen hosting the file, key, preview, and metadata panes."""

    # NOTE: Screen already binds tab/shift+tab to app.focus_next/app.focus_previous;
    # do not override them with a bare 'focus_next' action — that action does not
    # exist on Screen and Tab silently stops moving focus.
    BINDINGS: ClassVar[list[Binding]] = [
        Binding('q', 'quit', 'Quit'),
        Binding('r', 'reload_files', 'Rescan'),
        Binding('/', 'filter_panes', 'Filter'),
        Binding('c', 'cycle_channel', 'Cycle channel'),
    ]

    FILTER_INPUT_ID = 'filter-input'
    FILES_PANE = 'files'
    KEYS_PANE = 'keys'

    def __init__(
        self,
        directory: Path,
        config: Config,
        channel: str | None = None,
    ) -> None:
        """Store the browsing context and build the preview engine."""
        super().__init__()
        self.directory = directory
        self.config = config
        self.channel = channel
        self.engine = PreviewEngine(config)
        self._current_file: Path | None = None
        self._filter_target: str = self.FILES_PANE

    @property
    def filter_target(self) -> str:
        """The pane the filter input currently targets."""
        return self._filter_target

    def compose(self) -> ComposeResult:
        """Lay out the header, sidebar, content panes, and footer.

        Yields:
            The widgets of the main screen.
        """
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
        """Title the screen, start the scan, and focus the file list."""
        self._update_header_title()
        self._discover_files()
        self.query_one('#file-list').focus()

    def action_reload_files(self) -> None:
        """Rescan the directory for files."""
        self._discover_files()

    def action_cycle_channel(self) -> None:
        """Switch to the next enabled channel and rediscover files."""
        enabled = [ch.name for ch in self.config.channels if ch.enabled]
        if len(enabled) < MIN_CHANNELS_TO_CYCLE:
            return
        current = self._resolved_channel_name()
        try:
            index = enabled.index(current) if current is not None else -1
        except ValueError:
            index = -1
        self.channel = enabled[(index + 1) % len(enabled)]
        self._update_header_title()
        self._discover_files()

    def _resolved_channel_name(self) -> str | None:
        channel = self.config.get_channel(self.channel)
        return channel.name if channel is not None else None

    def _update_header_title(self) -> None:
        name = self._resolved_channel_name()
        self.sub_title = f'channel: {name}' if name else None

    def action_filter_panes(self) -> None:
        """Focus the filter input, aimed at whichever pane currently has focus."""
        if self.focused is not None and self.focused.id == 'yaml-viewer':
            self._filter_target = self.KEYS_PANE
        else:
            self._filter_target = self.FILES_PANE
        filter_input = self.query_one(f'#{self.FILTER_INPUT_ID}', Input)
        filter_input.placeholder = (
            'Filter YAML keys…' if self._filter_target == self.KEYS_PANE else 'Filter files…'
        )
        filter_input.focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Forward filter input changes to the targeted pane."""
        if event.input.id == self.FILTER_INPUT_ID:
            self._set_filter(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Apply the filter and return focus to the pane."""
        if event.input.id == self.FILTER_INPUT_ID:
            self._set_filter(event.value)
            self._filtered_pane().focus()

    def on_key(self, event: events.Key) -> None:
        """Clear the filter on escape when a filter is active."""
        if event.key != 'escape':
            return
        pane = self._filtered_pane()
        input_focused = self.focused is not None and self.focused.id == self.FILTER_INPUT_ID
        if input_focused or pane.filter is not None:
            event.stop()
            self._clear_filter()

    def _filtered_pane(self) -> FileListWidget | YAMLViewerWidget:
        if self._filter_target == self.KEYS_PANE:
            return self.query_one('#yaml-viewer', YAMLViewerWidget)
        return self.query_one('#file-list', FileListWidget)

    def _set_filter(self, value: str | None) -> None:
        self._filtered_pane().set_filter(value)

    def _clear_filter(self) -> None:
        filter_input = self.query_one(f'#{self.FILTER_INPUT_ID}', Input)
        filter_input.value = ''
        self._set_filter(None)
        self._filtered_pane().focus()

    @work(thread=True, exclusive=True)
    def _discover_files(self) -> None:
        files = self.engine.discover_files(self.directory, self.channel)
        self.post_message(FilesDiscovered(files))

    def on_files_discovered(self, event: FilesDiscovered) -> None:
        """Populate the file list once the scan finishes."""
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
        """Load the selected file's keys and clear the old preview."""
        self._current_file = event.file_path
        self._load_keys(event.file_path)

        preview_panel = self.query_one('#preview-panel', PreviewPanelWidget)
        metadata_bar = self.query_one('#metadata-bar', MetadataBarWidget)
        preview_panel.clear_preview()
        metadata_bar.clear_metadata()

    def on_key_selected(self, event: KeySelected) -> None:
        """Preview the selected key into the preview and metadata panes."""
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
        """Exit the application."""
        self.app.exit()
