# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""`d` compares changed cassettes with HEAD and opens the diff screen."""

from pathlib import Path

from rich.console import Console, Group

from tests.test_preview.test_diff import _entry, _git, _interactions, _write
from vcr_tui.app import VCRTUIApp
from vcr_tui.config.defaults import get_default_config
from vcr_tui.preview.diff import diff_cassette
from vcr_tui.ui.screens import DiffScreen, MainScreen
from vcr_tui.ui.screens.diff_screen import render_diff_report


def _plain(renderable: Group) -> str:
    console = Console(width=160, record=True, color_system=None)
    console.print(renderable)
    return console.export_text()


def test_render_diff_report() -> None:
    root = Path('/suite')
    old = _interactions(_entry(), _entry(uri='https://api.test/gone', method='DELETE'))
    new = _interactions(_entry(body='{"id": 1, "name": "Anne"}'))
    diff = diff_cassette(root / 'c.yaml', old, new)

    text = _plain(render_diff_report([diff], root, 'main', [(root / 'bad.yaml', 'oops')]))

    assert '1 file(s) changed since main' in text
    assert 'could not parse bad.yaml: oops' in text
    assert 'c.yaml (modified): 1 changed, 0 added, 1 removed, 0 unchanged' in text
    assert '~ #0 GET https://api.test/users/1' in text
    assert '~ response.body $.name: "Ann" -> "Anne"' in text
    assert '- #1 DELETE https://api.test/gone  200 OK' in text


def test_render_text_body_lines() -> None:
    root = Path('/suite')
    old = _interactions(_entry(body='one\ntwo', response_headers={}))
    new = _interactions(_entry(body='one\n2', response_headers={}))
    text = _plain(render_diff_report([diff_cassette(root / 'c.yaml', old, new)], root, 'HEAD'))
    assert '-two' in text
    assert '+2' in text


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / 'repo'
    root.mkdir()
    _git(root, 'init', '-q')
    _write(root / 'cassettes' / 'api.yaml', _entry(body='{"v": 1}'))
    _git(root, 'add', '.')
    _git(root, 'commit', '-q', '-m', 'init')
    _write(root / 'cassettes' / 'api.yaml', _entry(body='{"v": 2}'))
    return root


async def test_d_opens_diff_and_escape_returns(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    app = VCRTUIApp(repo, get_default_config())
    async with app.run_test() as pilot:
        await pilot.app.workers.wait_for_complete()
        await pilot.pause()

        await pilot.press('d')
        await pilot.app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.pause()

        screen = pilot.app.screen
        assert isinstance(screen, DiffScreen)
        assert screen.sub_title == 'diff vs HEAD: 1 file(s) changed'
        assert [d.path.name for d in screen.diffs] == ['api.yaml']

        await pilot.press('escape')
        await pilot.pause()
        assert isinstance(pilot.app.screen, MainScreen)


async def test_d_outside_git_notifies(tmp_path: Path) -> None:
    directory = tmp_path / 'cassettes'
    directory.mkdir()
    _write(directory / 'api.yaml', _entry())
    app = VCRTUIApp(directory, get_default_config())
    async with app.run_test() as pilot:
        await pilot.app.workers.wait_for_complete()
        await pilot.pause()

        await pilot.press('d')
        await pilot.app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.pause()

        assert isinstance(pilot.app.screen, MainScreen)
        assert any('git diff failed' in n.message for n in pilot.app._notifications)
