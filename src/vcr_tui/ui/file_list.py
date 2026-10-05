"""File list widget for displaying discovered files."""

from __future__ import annotations

from pathlib import Path

from textual.widgets import Label, ListItem, ListView


class FileList(ListView):
    """Widget for displaying a list of files.

    Displays files discovered by the preview engine with keyboard navigation
    and selection support. Emits ListView.Selected messages when a file is chosen.
    """

    def __init__(
        self,
        files: list[Path] | None = None,
        *,
        initial_index: int | None = 0,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the file list widget.

        Args:
            files: Initial list of files to display
            initial_index: Starting highlighted position
            name: Widget name
            id: Widget ID for CSS
            classes: CSS classes
        """
        super().__init__(
            initial_index=initial_index,
            name=name,
            id=id,
            classes=classes,
        )
        self._files: list[Path] = files or []

    def on_mount(self) -> None:
        """Called when widget is mounted to the app."""
        self._populate_list()

    def _populate_list(self) -> None:
        """Populate the ListView with file items."""
        self.clear()
        for file in self._files:
            item = ListItem(Label(file.name))
            self.append(item)

    def set_files(self, files: list[Path]) -> None:
        """Update the list of files.

        Args:
            files: New list of files to display
        """
        self._files = files
        self._populate_list()

    def get_selected_file(self) -> Path | None:
        """Get the currently highlighted file.

        Returns:
            Path of highlighted file or None if no selection
        """
        if self.index is None or not self._files:
            return None

        # Ensure index is within bounds
        index = max(0, min(self.index, len(self._files) - 1))
        return self._files[index]

    @property
    def files(self) -> list[Path]:
        """Get the current list of files.

        Returns:
            List of file paths
        """
        return self._files.copy()

    @property
    def file_count(self) -> int:
        """Get the number of files in the list.

        Returns:
            Count of files
        """
        return len(self._files)
