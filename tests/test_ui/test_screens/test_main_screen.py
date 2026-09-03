"""Filter binding narrows the file list and escape restores it."""

import shutil
from pathlib import Path

from textual.widgets._header import HeaderTitle

from vcr_tui.app import VCRTUIApp
from vcr_tui.config.defaults import get_default_config
from vcr_tui.ui.screens.main_screen import MainScreen
from vcr_tui.ui.widgets import FileListWidget

CASSETTES = Path(__file__).parent.parent.parent.parent / 'fixtures' / 'cassettes'


async def test_filter_narrows_list_and_escape_restores(tmp_path: Path) -> None:
    directory = tmp_path / 'cassettes'
    shutil.copytree(CASSETTES, directory)
    (directory / 'other_cassette.yaml').write_text('interactions: []\n', encoding='utf-8')
    initial = sorted(p.name for p in directory.glob('*.yaml'))
    assert len(initial) == 2
    target = 'example_api.yaml'
    assert target in initial

    app = VCRTUIApp(directory, get_default_config())
    async with app.run_test() as pilot:
        screen = pilot.app.screen
        assert isinstance(screen, MainScreen)
        file_list = screen.query_one('#file-list', FileListWidget)

        await pilot.app.workers.wait_for_complete()
        await pilot.pause()
        assert [p.name for p in file_list._files] == initial

        await pilot.press('/')
        await pilot.pause()
        assert screen.focused.id == screen.FILTER_INPUT_ID

        await pilot.press(*'example')
        await pilot.pause()
        assert [p.name for p in file_list._visible_files()] == [target]
        assert file_list.option_count == 1

        await pilot.press('escape')
        await pilot.pause()
        assert [p.name for p in file_list._visible_files()] == initial
        assert file_list.option_count == 2
        assert screen.focused is file_list


async def test_escape_without_filter_leaves_focus_untouched(tmp_path: Path) -> None:
    """Escape with no filter set must not steal focus from other widgets."""
    directory = tmp_path / 'cassettes'
    shutil.copytree(CASSETTES, directory)

    app = VCRTUIApp(directory, get_default_config())
    async with app.run_test() as pilot:
        screen = pilot.app.screen
        assert isinstance(screen, MainScreen)
        file_list = screen.query_one('#file-list', FileListWidget)
        await pilot.app.workers.wait_for_complete()
        await pilot.pause()
        assert file_list.filter is None

        await pilot.press('tab')
        await pilot.pause()
        yaml_viewer = screen.query_one('#yaml-viewer')
        assert screen.focused is yaml_viewer

        await pilot.press('escape')
        await pilot.pause()
        assert screen.focused is yaml_viewer


async def test_reload_picks_up_new_files(tmp_path: Path) -> None:
    directory = tmp_path / 'cassettes'
    shutil.copytree(CASSETTES, directory)
    initial = sorted(p.name for p in directory.glob('*.yaml'))

    app = VCRTUIApp(directory, get_default_config())
    async with app.run_test() as pilot:
        screen = pilot.app.screen
        assert isinstance(screen, MainScreen)
        file_list = screen.query_one('#file-list', FileListWidget)

        await pilot.app.workers.wait_for_complete()
        await pilot.pause()
        assert [p.name for p in file_list._files] == initial

        new_file = directory / 'zz_added.yaml'
        new_file.write_text('interactions: []\n', encoding='utf-8')

        await pilot.press('r')
        await pilot.app.workers.wait_for_complete()
        await pilot.pause()

        names = [p.name for p in file_list._files]
        assert len(names) == len(initial) + 1
        assert new_file.name in names


async def test_cycle_channel_switches_discovery(tmp_path: Path) -> None:
    """`c` cycles to the next enabled channel and rediscovers off the UI thread.

    The default vcr channel only matches files under a cassettes/ directory,
    while the yaml channel matches any *.yaml file; a file outside any
    cassettes/ directory appears only after switching channels.
    """
    directory = tmp_path / 'tree'
    (directory / 'cassettes').mkdir(parents=True)
    (directory / 'cassettes' / 'example_api.yaml').write_text(
        'interactions: []\n', encoding='utf-8'
    )
    standalone = directory / 'standalone_doc.yaml'
    standalone.write_text('key: value\n', encoding='utf-8')

    app = VCRTUIApp(directory, get_default_config())
    async with app.run_test() as pilot:
        screen = pilot.app.screen
        assert isinstance(screen, MainScreen)
        file_list = screen.query_one('#file-list', FileListWidget)
        header = screen.query_one(HeaderTitle)

        await pilot.app.workers.wait_for_complete()
        await pilot.pause()
        assert screen._resolved_channel_name() == 'vcr'
        names = [p.name for p in file_list._files]
        assert standalone.name not in names

        await pilot.press('c')
        await pilot.app.workers.wait_for_complete()
        await pilot.pause()

        assert screen.channel == 'yaml'
        assert 'channel: yaml' in str(header.content)
        names = [p.name for p in file_list._files]
        assert standalone.name in names

        # Selection is kept when the previously selected file survives the
        # channel switch (example_api.yaml is matched by both channels).
        assert file_list.highlighted == names.index('example_api.yaml')

        # Cycling wraps back to the first enabled channel.
        await pilot.press('c')
        await pilot.app.workers.wait_for_complete()
        await pilot.pause()
        assert screen._resolved_channel_name() == 'vcr'
        assert standalone.name not in [p.name for p in file_list._files]
