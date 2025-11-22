"""Preview panel widget for displaying formatted content."""

from __future__ import annotations

from rich.syntax import Syntax
from textual.widgets import Static


class PreviewPanel(Static):
    """Widget for displaying formatted preview content.

    Displays formatted content (JSON, YAML, HTML, text) from the preview engine.
    Content is scrollable and can be updated when a new key is selected.
    """

    def __init__(
        self,
        content: str = "",
        *,
        formatter: str | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the preview panel widget.

        Args:
            content: Initial content to display
            formatter: Type of content formatter (json, yaml, html, text)
            name: Widget name
            id: Widget ID for CSS
            classes: CSS classes
        """
        super().__init__(
            content,
            name=name,
            id=id,
            classes=classes,
        )
        self._content = content
        self._formatter = formatter
        self.can_focus = True

    def set_content(
        self,
        content: str,
        formatter: str | None = None,
    ) -> None:
        """Update the displayed content.

        Args:
            content: New content to display
            formatter: Type of content formatter (json, yaml, html, text, toml)
        """
        self._content = content
        self._formatter = formatter

        # Use Rich Syntax highlighting if formatter is specified
        if formatter and formatter in ("json", "yaml", "html", "toml", "xml"):
            try:
                syntax = Syntax(
                    content,
                    formatter,
                    theme="monokai",
                    line_numbers=False,
                    word_wrap=True,
                )
                self.update(syntax)
            except Exception:
                # Fallback to plain text if syntax highlighting fails
                self.update(content)
        else:
            # Plain text
            self.update(content)

    def clear_content(self) -> None:
        """Clear the displayed content."""
        self._content = ""
        self._formatter = None
        self.update("")

    @property
    def content(self) -> str:
        """Get the current content.

        Returns:
            Current content string
        """
        return self._content

    @property
    def formatter(self) -> str | None:
        """Get the current formatter type.

        Returns:
            Current formatter type or None
        """
        return self._formatter
