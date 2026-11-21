# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""Parsing syrupy amber snapshot files, diffing them, and finding them."""

import json
from pathlib import Path

import pytest

from tests.test_preview.test_diff import _git
from vcr_tui.config.defaults import get_default_config
from vcr_tui.preview.amber import (
    AmberSnapshot,
    format_snapshot_row,
    is_amber_path,
    parse_amber,
)
from vcr_tui.preview.diff import diff_snapshots, diffs_to_dict, render_diffs
from vcr_tui.preview.engine import PreviewEngine

FIXTURES = Path(__file__).parents[2] / 'fixtures' / 'snapshots'
AMBER = FIXTURES / '__snapshots__' / 'test_example.ambr'
ROOT = Path('/suite')


def _amber(*blocks: tuple[str, str]) -> str:
    lines = ['# serializer version: 1']
    for name, body in blocks:
        lines.append(f'# name: {name}')
        lines.extend(f'  {line}' if line else '' for line in body.splitlines())
        lines.append('# ---')
    return '\n'.join(lines) + '\n'


class TestParseAmber:
    def test_fixture(self):
        snapshots = parse_amber(AMBER.read_text(encoding='utf-8'))

        assert [s.name for s in snapshots] == [
            'TestUsers.test_get[admin]',
            'test_greeting',
            'test_report',
        ]
        first, second, third = snapshots
        assert first.line == 2
        assert first.body.splitlines()[0] == 'dict({'
        assert "  'id': 1," in first.body.splitlines()
        assert (first.kind, second.kind, third.kind) == ('dict', 'str', 'str')
        assert second.body == "'Hello, Ann!'"
        assert third.body.splitlines()[1:3] == ['Total: 3', 'Failed: 0']

    def test_unterminated_last_block_is_kept(self):
        snapshots = parse_amber('# name: test_a\n  1\n# ---\n# name: test_b\n  2\n')
        assert [(s.name, s.body) for s in snapshots] == [('test_a', '1'), ('test_b', '2')]

    def test_text_without_blocks(self):
        assert parse_amber('# serializer version: 1\n') == []
        assert parse_amber('') == []

    @pytest.mark.parametrize(
        ('name', 'expected'),
        [
            ('test_plain', 'test_plain'),
            ('test_param[case-1]', 'test_param'),
            ('TestClass.test_method', 'test_method'),
            ('TestClass.test_method[x.y]', 'test_method'),
            ('test_multi.1', 'test_multi'),
        ],
    )
    def test_test_name(self, name, expected):
        assert AmberSnapshot(0, name, '', 1).test_name == expected

    @pytest.mark.parametrize(
        ('body', 'kind'),
        [
            ('list([\n])', 'list'),
            ('tuple(\n)', 'tuple'),
            ("b'raw'", 'bytes'),
            ('42', 'number'),
            ('-1.5', 'number'),
            ("<class 'Foo'>", 'object'),
            ('None', 'other'),
            ('', 'other'),
        ],
    )
    def test_kind(self, body, kind):
        assert AmberSnapshot(0, 'test_x', body, 1).kind == kind

    def test_row_and_line_count(self):
        snapshot = parse_amber(AMBER.read_text(encoding='utf-8'))[0]
        assert snapshot.line_count == 8
        assert format_snapshot_row(snapshot).split() == [
            '0',
            'dict',
            '8L',
            'TestUsers.test_get[admin]',
        ]
        assert AmberSnapshot(0, 'test_x', '', 1).line_count == 0

    def test_is_amber_path(self):
        assert is_amber_path(AMBER)
        assert not is_amber_path(Path('cassette.yaml'))


class TestDiffSnapshots:
    def test_added_removed_changed(self):
        old = parse_amber(_amber(('test_a', "'one'"), ('test_b', 'dict({\n  "x": 1,\n})')))
        new = parse_amber(_amber(('test_b', 'dict({\n  "x": 2,\n})'), ('test_c', "'new'")))

        diff = diff_snapshots(ROOT / 's.ambr', old, new)

        assert diff.status == 'modified'
        assert diff.added == ('test_c',)
        assert diff.removed == ('test_a',)
        (change,) = diff.changed
        assert change.name == 'test_b'
        assert '-  "x": 1,' in change.lines
        assert '+  "x": 2,' in change.lines
        assert diff.unchanged == 0

    def test_identical_and_whole_file(self):
        same = parse_amber(_amber(('test_a', '1')))
        assert diff_snapshots(ROOT / 's.ambr', same, same).is_empty
        assert diff_snapshots(ROOT / 's.ambr', None, same).added == ('test_a',)
        assert diff_snapshots(ROOT / 's.ambr', same, None).removed == ('test_a',)

    def test_render_and_dict(self):
        old = parse_amber(_amber(('test_a', '1'), ('test_gone', '2')))
        new = parse_amber(_amber(('test_a', '3')))
        diff = diff_snapshots(ROOT / 's.ambr', old, new)

        lines = render_diffs([diff], ROOT).splitlines()
        data = json.loads(json.dumps(diffs_to_dict([diff], ROOT)))

        assert lines[0] == 's.ambr (modified): 1 changed, 0 added, 1 removed, 0 unchanged'
        assert lines[1] == '  ~ test_a'
        assert '      -1' in lines
        assert '      +3' in lines
        assert '  - test_gone' in lines
        assert data[0]['kind'] == 'snapshots'
        assert data[0]['changed'][0]['name'] == 'test_a'


class TestEngine:
    def test_get_snapshots(self):
        assert len(PreviewEngine.get_snapshots(AMBER) or []) == 3
        assert PreviewEngine.get_snapshots(Path('x.yaml')) is None

    def test_syrupy_channel_discovers_amber_files(self):
        engine = PreviewEngine(get_default_config())
        assert engine.discover_files(FIXTURES, 'syrupy') == [AMBER]
        assert engine.discover_files(FIXTURES, 'vcr') == []

    def test_audit_skips_amber_files(self):
        engine = PreviewEngine(get_default_config())
        assert engine.load_cassettes(FIXTURES, 'syrupy') == ([], [])

    def test_diff_against_includes_amber_without_a_channel(self, tmp_path: Path):
        repo = tmp_path / 'repo'
        snapshots = repo / 'tests' / '__snapshots__'
        snapshots.mkdir(parents=True)
        path = snapshots / 'test_api.ambr'
        path.write_text(_amber(('test_a', "'old'")), encoding='utf-8')
        _git(repo, 'init', '-q')
        _git(repo, 'add', '.')
        _git(repo, 'commit', '-q', '-m', 'init')
        path.write_text(_amber(('test_a', "'new'")), encoding='utf-8')

        engine = PreviewEngine(get_default_config())
        all_channels, _ = engine.diff_against(repo, 'HEAD')
        vcr_only, _ = engine.diff_against(repo, 'HEAD', 'vcr')

        (diff,) = all_channels
        assert diff.path.name == 'test_api.ambr'
        assert [c.name for c in diff.changed] == ['test_a']
        assert vcr_only == []
