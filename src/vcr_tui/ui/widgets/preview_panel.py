"""Widget rendering the formatted preview with syntax highlighting."""

from typing import Any

from rich.syntax import Syntax
from textual.widgets import Static

from vcr_tui.preview.types import PreviewResult

LEXER_MAP = {
    'json': 'json',
    'yaml': 'yaml',
    'html': 'html',
    'text': 'text',
    'toml': 'toml',
}


class PreviewPanelWidget(Static):
    """Static panel showing a Syntax-rendered preview."""

    def __init__(self, **kwargs: Any) -> None:
        """Start with no preview loaded."""
        super().__init__(**kwargs)
        self._result: PreviewResult | None = None

    def set_preview(self, result: PreviewResult) -> None:
        """Render a preview result with the lexer matching its formatter."""
        self._result = result
        lexer = LEXER_MAP.get(result.formatter, 'text')

        syntax = Syntax(
            result.content,
            lexer,
            theme='monokai',
            line_numbers=True,
            word_wrap=True,
        )
        self.update(syntax)

    def clear_preview(self) -> None:
        """Blank the panel."""
        self._result = None
        self.update('')
