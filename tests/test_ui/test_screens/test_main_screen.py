"""Reload binding re-runs background file discovery."""

import shutil
from pathlib import Path

from vcr_tui.app import VCRTUIApp
from vcr_tui.config.defaults import get_default_config
from vcr_tui.ui.screens.main_screen import MainScreen
from vcr_tui.ui.widgets import FileListWidget

CASSETTES = Path(__file__).parent.parent.parent.parent / 'fixtures' / 'cassettes'


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
