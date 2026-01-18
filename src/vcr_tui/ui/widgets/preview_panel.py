from textual.widgets import Static
from rich.syntax import Syntax

from vcr_tui.preview.types import PreviewResult

LEXER_MAP = {
    "json": "json",
    "yaml": "yaml",
    "html": "html",
    "text": "text",
    "toml": "toml",
}


class PreviewPanelWidget(Static):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._result: PreviewResult | None = None

    def set_preview(self, result: PreviewResult) -> None:
        self._result = result
        lexer = LEXER_MAP.get(result.formatter, "text")

        syntax = Syntax(
            result.content,
            lexer,
            theme="monokai",
            line_numbers=True,
            word_wrap=True,
        )
        self.update(syntax)

    def clear_preview(self) -> None:
        self._result = None
        self.update("")
