# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""Widget rendering the formatted preview with syntax highlighting."""

from rich.console import Group, RenderableType
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from textual.widgets import Static

from vcr_tui.preview.cassette import HttpMessage, Interaction, body_summary
from vcr_tui.preview.types import PreviewResult

LEXER_MAP = {
    'json': 'json',
    'yaml': 'yaml',
    'html': 'html',
    'xml': 'xml',
    'text': 'text',
    'toml': 'toml',
    'python': 'python',
}

_STATUS_STYLES = (
    (500, 'bold red'),
    (400, 'bold yellow'),
    (300, 'bold cyan'),
    (200, 'bold green'),
)


def status_style(code: int | None) -> str:
    """Pick a style for a status code: green 2xx, cyan 3xx, yellow 4xx, red 5xx."""
    if code is None:
        return 'dim'
    return next((style for floor, style in _STATUS_STYLES if code >= floor), 'dim')


class PreviewPanelWidget(Static):
    """Static panel showing a Syntax-rendered preview or one HTTP interaction."""

    _result: PreviewResult | None = None

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

    def set_interaction(self, interaction: Interaction) -> None:
        """Render an interaction: summary line, then request and response sections."""
        self._result = None
        title = Text.assemble(
            (interaction.method, 'bold'),
            ' ',
            interaction.uri,
            '  ',
            (interaction.status, status_style(interaction.status_code)),
        )
        parts: list[RenderableType] = [title]
        if interaction.recorded_at:
            parts.append(Text(f'recorded at {interaction.recorded_at}', style='dim'))
        parts.extend(_message_section('Request', interaction.request))
        parts.extend(_message_section('Response', interaction.response))
        self.update(Group(*parts))

    def clear_preview(self) -> None:
        """Blank the panel."""
        self._result = None
        self.update('')


def _message_section(title: str, message: HttpMessage) -> list[RenderableType]:
    parts: list[RenderableType] = [
        Rule(f'{title} - {body_summary(message.body)}', align='left', style='dim'),
    ]
    if message.headers:
        headers = Table.grid(padding=(0, 1))
        headers.add_column(style='cyan', no_wrap=True)
        headers.add_column()
        for name, values in message.headers.items():
            for value in values:
                headers.add_row(f'{name}:', value)
        parts.append(headers)
    if message.body.kind != 'empty':
        syntax = Syntax(
            message.body.text,
            LEXER_MAP.get(message.body.kind, 'text'),
            theme='monokai',
            word_wrap=True,
        )
        parts.extend((Text(''), syntax))
    return parts
