# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""Cassettes open as a list of HTTP interactions, with `v` toggling the raw key tree."""

import shutil
from pathlib import Path

import pytest
from rich.console import Group
from rich.syntax import Syntax
from textual.pilot import Pilot
from textual.widgets import Input

from vcr_tui.app import VCRTUIApp
from vcr_tui.config.defaults import get_default_config
from vcr_tui.ui.screens.main_screen import MainScreen
from vcr_tui.ui.widgets import (
    InteractionListWidget,
    MetadataBarWidget,
    PreviewPanelWidget,
    YAMLViewerWidget,
)
from vcr_tui.ui.widgets.preview_panel import status_style

CASSETTES = Path(__file__).parent.parent.parent.parent / 'fixtures' / 'cassettes'


def _cassette_app(tmp_path: Path) -> VCRTUIApp:
    directory = tmp_path / 'cassettes'
    shutil.copytree(CASSETTES, directory)
    return VCRTUIApp(directory, get_default_config())


async def _loaded(pilot: Pilot) -> MainScreen:
    await pilot.app.workers.wait_for_complete()
    await pilot.pause()
    screen = pilot.app.screen
    assert isinstance(screen, MainScreen)
    return screen


def _syntax_codes(panel: PreviewPanelWidget) -> list[str]:
    content = panel.content
    assert isinstance(content, Group)
    return [part.code for part in content.renderables if isinstance(part, Syntax)]


async def test_cassette_opens_as_interaction_list(tmp_path: Path) -> None:
    app = _cassette_app(tmp_path)
    async with app.run_test() as pilot:
        screen = await _loaded(pilot)
        interaction_list = screen.query_one('#interaction-list', InteractionListWidget)
        yaml_viewer = screen.query_one('#yaml-viewer', YAMLViewerWidget)

        assert screen.showing_interactions
        assert interaction_list.display
        assert not yaml_viewer.display
        assert interaction_list.option_count == 2

        await pilot.press('tab')
        await pilot.pause()
        assert screen.focused is interaction_list


async def test_highlight_previews_request_and_response(tmp_path: Path) -> None:
    app = _cassette_app(tmp_path)
    async with app.run_test() as pilot:
        screen = await _loaded(pilot)

        # Nothing starts highlighted, so two presses land on the POST.
        await pilot.press('tab', 'j', 'j')
        await pilot.pause()

        codes = _syntax_codes(screen.query_one('#preview-panel', PreviewPanelWidget))
        assert len(codes) == 2
        assert '"email": "jane@example.com"' in codes[0]
        assert '"created_at": "2024-01-15T10:30:00Z"' in codes[1]

        bar = screen.query_one('#metadata-bar', MetadataBarWidget).content
        assert isinstance(bar, str)
        assert 'interaction: 2/2' in bar
        assert 'status.code: 201' in bar
        assert 'request.method: POST' in bar


async def test_filter_targets_interactions(tmp_path: Path) -> None:
    app = _cassette_app(tmp_path)
    async with app.run_test() as pilot:
        screen = await _loaded(pilot)
        interaction_list = screen.query_one('#interaction-list', InteractionListWidget)

        await pilot.press('tab', '/')
        await pilot.pause()
        assert screen.filter_target == MainScreen.INTERACTIONS_PANE
        filter_input = screen.query_one(f'#{screen.FILTER_INPUT_ID}', Input)
        assert 'Filter requests' in filter_input.placeholder

        await pilot.press(*'post')
        await pilot.pause()
        assert [i.method for i in interaction_list._visible_interactions()] == ['POST']
        assert interaction_list.option_count == 1

        await pilot.press('escape')
        await pilot.pause()
        assert interaction_list.option_count == 2
        assert screen.focused is interaction_list


async def test_toggle_switches_to_raw_keys_and_back(tmp_path: Path) -> None:
    app = _cassette_app(tmp_path)
    async with app.run_test() as pilot:
        screen = await _loaded(pilot)
        interaction_list = screen.query_one('#interaction-list', InteractionListWidget)
        yaml_viewer = screen.query_one('#yaml-viewer', YAMLViewerWidget)

        await pilot.press('tab', 'v')
        await pilot.pause()
        assert not screen.showing_interactions
        assert yaml_viewer.display
        assert not interaction_list.display
        assert screen.focused is yaml_viewer

        await pilot.press('v')
        await pilot.pause()
        assert screen.showing_interactions
        assert screen.focused is interaction_list


async def test_non_cassette_shows_key_tree(tmp_path: Path) -> None:
    directory = tmp_path / 'docs'
    directory.mkdir()
    (directory / 'doc.yaml').write_text('key: value\n', encoding='utf-8')

    app = VCRTUIApp(directory, get_default_config(), channel='yaml')
    async with app.run_test() as pilot:
        screen = await _loaded(pilot)

        assert not screen.showing_interactions
        assert screen.query_one('#yaml-viewer', YAMLViewerWidget).display
        assert not screen.query_one('#interaction-list', InteractionListWidget).display


@pytest.mark.parametrize(
    ('code', 'style'),
    [
        (None, 'dim'),
        (101, 'dim'),
        (204, 'bold green'),
        (302, 'bold cyan'),
        (404, 'bold yellow'),
        (503, 'bold red'),
    ],
)
def test_status_style(code: int | None, style: str) -> None:
    assert status_style(code) == style
