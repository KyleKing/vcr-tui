# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""Syrupy amber files open as a list of named snapshots with their bodies previewed."""

import shutil
from pathlib import Path

from rich.syntax import Syntax

from vcr_tui.app import VCRTUIApp
from vcr_tui.config.defaults import get_default_config
from vcr_tui.ui.screens.main_screen import MainScreen
from vcr_tui.ui.widgets import (
    InteractionListWidget,
    MetadataBarWidget,
    PreviewPanelWidget,
    SnapshotListWidget,
    YAMLViewerWidget,
)

SNAPSHOTS = Path(__file__).parents[3] / 'fixtures' / 'snapshots'


async def test_amber_file_opens_as_snapshot_list(tmp_path: Path) -> None:
    directory = tmp_path / 'tests'
    shutil.copytree(SNAPSHOTS, directory)

    app = VCRTUIApp(directory, get_default_config(), channel='syrupy')
    async with app.run_test() as pilot:
        await pilot.app.workers.wait_for_complete()
        await pilot.pause()
        screen = pilot.app.screen
        assert isinstance(screen, MainScreen)
        snapshot_list = screen.query_one('#snapshot-list', SnapshotListWidget)

        assert snapshot_list.display
        assert not screen.query_one('#interaction-list', InteractionListWidget).display
        assert not screen.query_one('#yaml-viewer', YAMLViewerWidget).display
        assert snapshot_list.option_count == 3

        await pilot.press('tab', 'j', 'j')
        await pilot.pause()
        assert screen.focused is snapshot_list

        content = screen.query_one('#preview-panel', PreviewPanelWidget).content
        assert isinstance(content, Syntax)
        assert content.code == "'Hello, Ann!'"
        bar = screen.query_one('#metadata-bar', MetadataBarWidget).content
        assert isinstance(bar, str)
        assert 'snapshot: 2/3' in bar
        assert 'name: test_greeting' in bar

        await pilot.press('/', *'report')
        await pilot.pause()
        assert screen.filter_target == MainScreen.SNAPSHOTS_PANE
        assert [s.name for s in snapshot_list._visible_snapshots()] == ['test_report']

        await pilot.press('escape')
        await pilot.pause()
        assert snapshot_list.option_count == 3
        assert screen.focused is snapshot_list
