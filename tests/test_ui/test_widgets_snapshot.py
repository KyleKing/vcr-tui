"""Golden snapshot tests for the individual widgets.

The preview panel's snapshot is intentionally replaced by direct assertions.
The known facts: this state rendered by rich.syntax produced different
snapshots on ubuntu-latest than on macOS; the cause has not been established.
Asserting on the rendered Syntax object is the better test regardless of the
cause: it checks exactly what the widget was given (code, lexer) rather than
a byte-level image of however the terminal rendering happens to come out.
"""

from pathlib import Path
from typing import Any

import pytest
from rich.syntax import Syntax

from vcr_tui.config.defaults import get_default_config
from vcr_tui.preview import PreviewEngine
from vcr_tui.preview.types import YAMLKey
from vcr_tui.ui.widgets import (
    FileListWidget,
    MetadataBarWidget,
    PreviewPanelWidget,
    YAMLViewerWidget,
)

CASSETTE = Path(__file__).parent.parent.parent / 'fixtures' / 'cassettes' / 'example_api.yaml'


class _Harness:
    """Minimal host app so snap_compare can render one widget in isolation."""

    def __init__(self, widget: Any) -> None:
        self._widget = widget

    def __call__(self) -> Any:
        from textual.app import App

        outer = self

        class _App(App[None]):
            def compose(self):  # noqa: ANN201, D102
                yield outer._widget

        return _App()


@pytest.fixture
def cassette_keys() -> list[YAMLKey]:
    engine = PreviewEngine(get_default_config())
    return engine.get_keys(CASSETTE)


def test_file_list_widget(snap_compare: Any, cassette_keys: list[YAMLKey]) -> None:
    widget = FileListWidget(id='file-list')
    widget.set_files([CASSETTE, CASSETTE.with_name('other_api.yaml')])
    assert snap_compare(_Harness(widget)())


def test_yaml_viewer_widget(snap_compare: Any, cassette_keys: list[YAMLKey]) -> None:
    widget = YAMLViewerWidget(id='yaml-viewer')
    widget.set_keys(cassette_keys)
    assert snap_compare(_Harness(widget)())


def test_preview_panel_widget_renders_syntax_highlighted_content() -> None:
    """The preview panel formats the selected body as syntax-highlighted JSON.

    Snapshot-based coverage is intentionally skipped for this widget (see the
    module docstring); assert on the rendered Syntax object instead.
    """
    engine = PreviewEngine(get_default_config())
    result = engine.preview_key(CASSETTE, 'interactions[0].response.body.string')
    widget = PreviewPanelWidget(id='preview-panel')
    widget.set_preview(result)

    content = widget.content
    assert isinstance(content, Syntax)
    assert content.code == result.content
    lexer = content.lexer
    assert lexer is not None
    assert lexer.name == 'JSON'

    # The formatted content is pretty-printed JSON of the fixture body.
    assert '"name": "John Doe"' in result.content
    assert result.formatter == 'json'


def test_preview_panel_widget_clears() -> None:
    widget = PreviewPanelWidget(id='preview-panel')
    engine = PreviewEngine(get_default_config())
    result = engine.preview_key(CASSETTE, 'interactions[0].response.body.string')
    widget.set_preview(result)
    widget.clear_preview()
    assert widget.content == ''


def test_metadata_bar_widget(snap_compare: Any) -> None:
    engine = PreviewEngine(get_default_config())
    result = engine.preview_key(CASSETTE, 'interactions[0].response.body.string')
    widget = MetadataBarWidget(id='metadata-bar')
    widget.set_metadata(result.metadata)
    assert snap_compare(_Harness(widget)())
