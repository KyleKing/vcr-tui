# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""`a` audits every discovered cassette and opens the report screen."""

import shutil
from pathlib import Path

from rich.console import Console, Group

from vcr_tui.app import VCRTUIApp
from vcr_tui.config.defaults import get_default_config
from vcr_tui.preview.audit import audit
from vcr_tui.preview.engine import PreviewEngine
from vcr_tui.ui.screens import AuditScreen, MainScreen
from vcr_tui.ui.screens.audit_screen import render_audit

CASSETTES = Path(__file__).parent.parent.parent.parent / 'fixtures' / 'cassettes'


def _plain(renderable: Group) -> str:
    console = Console(width=160, record=True, color_system=None)
    console.print(renderable)
    return console.export_text()


def test_render_audit_lists_endpoints_and_findings() -> None:
    cassettes, unreadable = PreviewEngine(get_default_config()).load_cassettes(CASSETTES)
    text = _plain(render_audit(audit(cassettes, unreadable=unreadable), CASSETTES))

    assert '1 cassettes, 2 interactions, 1 hosts' in text
    assert '0 error' in text
    assert 'api.example.com/users/{id}' in text
    assert '201x1' in text
    assert 'example_api.yaml#0' in text


async def test_a_opens_audit_and_escape_returns(tmp_path: Path) -> None:
    directory = tmp_path / 'cassettes'
    shutil.copytree(CASSETTES, directory)

    app = VCRTUIApp(directory, get_default_config())
    async with app.run_test() as pilot:
        await pilot.app.workers.wait_for_complete()
        await pilot.pause()

        await pilot.press('a')
        await pilot.app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.pause()

        screen = pilot.app.screen
        assert isinstance(screen, AuditScreen)
        assert screen.report.interactions == 2
        assert screen.sub_title == 'audit: 0 error, 0 warning, 3 info'

        await pilot.press('escape')
        await pilot.pause()
        assert isinstance(pilot.app.screen, MainScreen)
