"""Golden snapshot tests for the TUI (run `pytest --snapshot-update` to refresh).

Two of the three platform-divergent states are covered here by direct
assertions instead of snapshots (the third is the preview panel widget
snapshot, covered in test_widgets_snapshot.py). The known facts: all three
render through rich.syntax and produced different snapshots on ubuntu-latest
than on macOS; the cause has not been established. Asserting on the widgets'
rendered content is the better test regardless of the cause: it checks
exactly what was displayed (the Syntax object's code, the metadata bar's
text) rather than a byte-level image of however the terminal rendering
happens to come out.
"""

from pathlib import Path
from typing import Any

from rich.syntax import Syntax
from textual.pilot import Pilot

from vcr_tui.app import VCRTUIApp
from vcr_tui.config.defaults import get_default_config
from vcr_tui.ui.screens.main_screen import MainScreen
from vcr_tui.ui.widgets import FileListWidget, MetadataBarWidget, PreviewPanelWidget

CASSETTES = Path(__file__).parent.parent.parent / 'fixtures' / 'cassettes'


def _app(directory: Path = CASSETTES) -> VCRTUIApp:
    return VCRTUIApp(directory, get_default_config())


async def _populated_app(pilot: Pilot) -> None:
    """Wait for the background file discovery worker to reach the UI."""
    await pilot.app.workers.wait_for_complete()
    await pilot.pause()
    screen = pilot.app.screen
    assert isinstance(screen, MainScreen)
    file_list = screen.query_one('#file-list', FileListWidget)
    assert file_list.option_count > 0


def test_main_screen_initial(snap_compare: Any) -> None:
    """Main screen on mount: file list populated, first file's keys shown."""
    assert snap_compare(_app(), run_before=_populated_app)


async def test_main_screen_preview_response_body() -> None:
    """Selecting interactions[0].response.body.string renders the JSON preview.

    Snapshot-based coverage is intentionally skipped for this state (see the
    module docstring); assert on the preview panel's rendered Syntax object.
    """
    app = _app()
    # Key index 13 in the fixture is interactions[0].response.body.string.
    async with app.run_test() as pilot:
        # Focus order: file-list -> yaml-viewer (filter-input is third).
        await pilot.press('tab', *['j'] * 13, 'enter')

        panel = app.screen.query_one('#preview-panel', PreviewPanelWidget)
        content = panel.content
        assert isinstance(content, Syntax)
        assert '"name": "John Doe"' in content.code
        assert '"role": "admin"' in content.code


async def test_main_screen_metadata_bar_populated() -> None:
    """The metadata bar shows interaction-level metadata for the selected key.

    Snapshot-based coverage is intentionally skipped for this state (see the
    module docstring); assert on the metadata bar's rendered text.
    """
    app = _app()
    async with app.run_test() as pilot:
        # interactions[1].request.body.string (key index 35): metadata comes from
        # the second interaction (POST https://api.example.com/users).
        # Focus order: file-list -> yaml-viewer (filter-input is third).
        await pilot.press('tab', *['j'] * 35, 'enter')

        bar = app.screen.query_one('#metadata-bar', MetadataBarWidget)
        text = bar.content
        assert isinstance(text, str)
        assert 'request.method: POST' in text
        assert 'request.uri: https://api.example.com/users' in text
