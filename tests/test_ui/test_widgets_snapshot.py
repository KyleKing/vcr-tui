"""Golden snapshot tests for the individual widgets."""

from pathlib import Path
from typing import Any

import pytest

from vcr_tui.config.models import Config
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
    engine = PreviewEngine(Config())
    return engine.get_keys(CASSETTE)


def test_file_list_widget(snap_compare: Any, cassette_keys: list[YAMLKey]) -> None:
    widget = FileListWidget(id='file-list')
    widget.set_files([CASSETTE, CASSETTE.with_name('other_api.yaml')])
    assert snap_compare(_Harness(widget)())


def test_yaml_viewer_widget(snap_compare: Any, cassette_keys: list[YAMLKey]) -> None:
    widget = YAMLViewerWidget(id='yaml-viewer')
    widget.set_keys(cassette_keys)
    assert snap_compare(_Harness(widget)())


def test_preview_panel_widget(snap_compare: Any) -> None:
    engine = PreviewEngine(Config())
    result = engine.preview_key(CASSETTE, 'interactions[0].response.body.string')
    widget = PreviewPanelWidget(id='preview-panel')
    widget.set_preview(result)
    assert snap_compare(_Harness(widget)())


def test_metadata_bar_widget(snap_compare: Any) -> None:
    engine = PreviewEngine(Config())
    result = engine.preview_key(CASSETTE, 'interactions[0].response.body.string')
    widget = MetadataBarWidget(id='metadata-bar')
    widget.set_metadata(result.metadata)
    assert snap_compare(_Harness(widget)())
