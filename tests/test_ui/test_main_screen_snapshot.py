"""Golden snapshot tests for the TUI (run `pytest --snapshot-update` to refresh)."""

from pathlib import Path
from typing import Any

from vcr_tui.app import VCRTUIApp
from vcr_tui.config.defaults import get_default_config

CASSETTES = Path(__file__).parent.parent.parent / 'fixtures' / 'cassettes'


def _app(directory: Path = CASSETTES) -> VCRTUIApp:
    return VCRTUIApp(directory, get_default_config())


def test_main_screen_initial(snap_compare: Any) -> None:
    """Main screen on mount: file list populated, first file's keys shown."""
    assert snap_compare(_app())


def test_main_screen_preview_response_body(snap_compare: Any) -> None:
    """Selecting interactions[0].response.body.string renders the JSON preview."""
    # Key index 13 in the fixture is interactions[0].response.body.string.
    assert snap_compare(_app(), press=['tab', *['j'] * 13, 'enter'])


def test_main_screen_metadata_bar_populated(snap_compare: Any) -> None:
    """The metadata bar shows interaction-level metadata for the selected key.

    The bar sits on the last terminal rows; assertions on it need the taller
    default terminal, so drive selection to the same key as the preview test.
    """
    # interactions[1].request.body.string (key index 35): metadata comes from the
    # second interaction (POST https://api.example.com/users).
    keys = ['tab', *['j'] * 35, 'enter']
    assert snap_compare(_app(), press=keys)
