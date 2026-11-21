# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""Interaction-level cassette diffs, and the git-backed comparison in the engine."""

import json
import shutil
import subprocess  # noqa: S404
from pathlib import Path

import pytest
from click.testing import CliRunner

from vcr_tui.cli import main
from vcr_tui.config import loader
from vcr_tui.config.defaults import get_default_config
from vcr_tui.preview.cassette import parse_cassette
from vcr_tui.preview.diff import (
    Change,
    DiffOptions,
    compare_interactions,
    describe_change,
    diff_cassette,
    diffs_to_dict,
    json_changes,
    render_diffs,
)
from vcr_tui.preview.engine import PreviewEngine
from vcr_tui.preview.git_source import GitError, changed_files

ROOT = Path('/suite')


def _entry(
    uri='https://api.test/users/1',
    method='GET',
    status=200,
    body='{"id": 1, "name": "Ann"}',
    response_headers=None,
    request_body=None,
):
    return {
        'request': {'method': method, 'uri': uri, 'body': request_body, 'headers': {}},
        'response': {
            'status': {'code': status, 'message': 'OK' if status < 400 else 'Error'},
            'headers': response_headers or {'Content-Type': ['application/json']},
            'body': {'string': body},
        },
    }


def _interactions(*entries):
    return parse_cassette({'interactions': list(entries)})


class TestJsonChanges:
    def test_nested_added_removed_changed(self):
        before = {'user': {'name': 'Ann', 'tags': ['a', 'b']}, 'gone': 1}
        after = {'user': {'name': 'Anne', 'tags': ['a']}, 'new': True}

        changes = json_changes(before, after)

        assert [(c.kind, c.path, c.before, c.after) for c in changes] == [
            ('removed', '$.gone', '1', None),
            ('added', '$.new', None, 'true'),
            ('changed', '$.user.name', '"Ann"', '"Anne"'),
            ('removed', '$.user.tags[1]', '"b"', None),
        ]

    def test_type_change_and_ignored_fields(self):
        changes = json_changes(
            {'count': 1, 'updated_at': 'x'},
            {'count': '1', 'updated_at': 'y'},
            ignore_fields={'updated_at'},
        )
        assert [(c.path, c.before, c.after) for c in changes] == [('$.count', '1', '"1"')]

    def test_bool_is_not_int(self):
        assert len(json_changes({'a': 1}, {'a': True})) == 1

    def test_identical(self):
        assert json_changes({'a': [1, {'b': None}]}, {'a': [1, {'b': None}]}) == []


class TestCompareInteractions:
    def test_status_uri_headers_and_body(self):
        (old,) = _interactions(
            _entry(response_headers={'Content-Type': ['application/json'], 'X-Old': ['1']}),
        )
        (new,) = _interactions(
            _entry(
                uri='https://api.test/users/1?v=2',
                status=404,
                body='{"id": 1, "name": "Anne"}',
                response_headers={'content-type': ['application/json'], 'X-New': ['2']},
            ),
        )

        changes = compare_interactions(old, new)

        assert [describe_change(c) for c in changes] == [
            '~ status: 200 OK -> 404 Error',
            '~ request.uri: https://api.test/users/1 -> https://api.test/users/1?v=2',
            '+ response.headers x-new: 2',
            '- response.headers x-old: 1',
            '~ response.body $.name: "Ann" -> "Anne"',
        ]

    def test_volatile_headers_ignored_by_default(self):
        (old,) = _interactions(_entry(response_headers={'Date': ['Mon'], 'X-Request-Id': ['a']}))
        (new,) = _interactions(_entry(response_headers={'Date': ['Tue'], 'X-Request-Id': ['b']}))
        assert compare_interactions(old, new) == ()
        assert len(compare_interactions(old, new, DiffOptions(ignore_headers=frozenset()))) == 2

    def test_text_body_line_diff(self):
        (old,) = _interactions(_entry(body='line 1\nline 2\nline 3', response_headers={}))
        (new,) = _interactions(_entry(body='line 1\nline two\nline 3', response_headers={}))

        (change,) = compare_interactions(old, new)

        assert change.section == 'response.body'
        assert describe_change(change) == '~ response.body'
        assert '-line 2' in change.lines
        assert '+line two' in change.lines

    def test_text_diff_is_capped(self):
        old_body = '\n'.join(f'a{i}' for i in range(50))
        new_body = '\n'.join(f'b{i}' for i in range(50))
        (old,) = _interactions(_entry(body=old_body, response_headers={}))
        (new,) = _interactions(_entry(body=new_body, response_headers={}))

        (change,) = compare_interactions(old, new, DiffOptions(max_text_lines=5))

        assert len(change.lines) == 6
        assert change.lines[-1].endswith('more diff lines')

    def test_body_appears_and_disappears(self):
        (empty,) = _interactions(_entry(body=''))
        (full,) = _interactions(_entry(body='{"ok": true}'))
        assert compare_interactions(empty, full)[0].kind == 'added'
        assert compare_interactions(full, empty)[0].kind == 'removed'


class TestDiffCassette:
    def test_pairs_in_order_and_reports_added_removed(self):
        old = _interactions(
            _entry(uri='https://api.test/a'),
            _entry(uri='https://api.test/a', body='{"n": 2}'),
            _entry(uri='https://api.test/gone', method='DELETE'),
        )
        new = _interactions(
            _entry(uri='https://api.test/a'),
            _entry(uri='https://api.test/a', body='{"n": 3}'),
            _entry(uri='https://api.test/new', method='POST', status=201),
        )

        diff = diff_cassette(ROOT / 'c.yaml', old, new)

        assert diff.status == 'modified'
        assert diff.unchanged == 1
        assert [(d.old.index, d.new.index) for d in diff.changed] == [(1, 1)]
        assert [i.uri for i in diff.added] == ['https://api.test/new']
        assert [i.uri for i in diff.removed] == ['https://api.test/gone']
        assert not diff.is_empty

    def test_query_change_still_pairs(self):
        old = _interactions(_entry(uri='https://api.test/s?ts=1'))
        new = _interactions(_entry(uri='https://api.test/s?ts=2'))
        diff = diff_cassette(ROOT / 'c.yaml', old, new)
        assert diff.added == diff.removed == ()
        assert diff.changed[0].changes[0].section == 'request.uri'

    def test_whole_file_added_or_deleted(self):
        interactions = _interactions(_entry())
        added = diff_cassette(ROOT / 'c.yaml', None, interactions)
        deleted = diff_cassette(ROOT / 'c.yaml', interactions, None)
        assert (added.status, len(added.added)) == ('added', 1)
        assert (deleted.status, len(deleted.removed)) == ('deleted', 1)

    def test_identical_is_empty(self):
        diff = diff_cassette(ROOT / 'c.yaml', _interactions(_entry()), _interactions(_entry()))
        assert diff.is_empty
        assert diff.unchanged == 1


class TestRendering:
    def _diffs(self):
        old = _interactions(_entry(), _entry(uri='https://api.test/gone', method='DELETE'))
        new = _interactions(
            _entry(uri='https://api.test/new', method='POST', status=201),
            _entry(body='{"id": 1, "name": "Anne"}'),
        )
        same = _interactions(_entry())
        unchanged = diff_cassette(ROOT / 'same.yaml', same, same)
        return [diff_cassette(ROOT / 'tests' / 'c.yaml', old, new), unchanged]

    def test_render_diffs(self):
        text = render_diffs(self._diffs(), ROOT)
        assert text.splitlines() == [
            str(Path('tests') / 'c.yaml')
            + ' (modified): 1 changed, 1 added, 1 removed, 0 unchanged',
            '  ~ #1 GET https://api.test/users/1  (was #0)',
            '      ~ response.body $.name: "Ann" -> "Anne"',
            '  + #0 POST https://api.test/new  201 OK',
            '  - #1 DELETE https://api.test/gone  200 OK',
            '',
            '1 cassette(s) changed',
        ]

    def test_render_nothing(self):
        assert render_diffs([], ROOT) == 'No cassette changes.'

    def test_diffs_to_dict(self):
        data = json.loads(json.dumps(diffs_to_dict(self._diffs(), ROOT)))
        assert len(data) == 1
        (entry,) = data
        assert entry['status'] == 'modified'
        assert entry['changed'][0]['old_index'] == 0
        assert entry['changed'][0]['changes'][0]['path'] == '$.name'
        assert [i['method'] for i in entry['added']] == ['POST']

    def test_describe_added_removed(self):
        assert describe_change(Change('response.headers', 'added', 'x', after='1')) == (
            '+ response.headers x: 1'
        )
        assert describe_change(Change('request.body', 'removed', before='{}')) == (
            '- request.body: {}'
        )


def _git(repo: Path, *args: str) -> str:
    git = shutil.which('git')
    assert git is not None
    return subprocess.run(  # noqa: S603
        [
            git,
            '-c',
            'user.name=Test',
            '-c',
            'user.email=test@example.com',
            '-c',
            'commit.gpgsign=false',
            *args,
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def _write(path: Path, *entries) -> None:
    lines = ['interactions:']
    for entry in entries:
        request, response = entry['request'], entry['response']
        lines.extend([
            '- request:',
            f'    method: {request["method"]}',
            f'    uri: {request["uri"]}',
            '    body: null',
            '    headers: {}',
            '  response:',
            f'    status: {{code: {response["status"]["code"]}, message: OK}}',
            '    headers: {}',
            f'    body: {{string: {json.dumps(response["body"]["string"])}}}',
        ])
    lines.append('version: 1')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / 'repo'
    root.mkdir()
    _git(root, 'init', '-q')
    cassettes = root / 'tests' / 'cassettes'
    _write(cassettes / 'kept.yaml', _entry(body='{"v": 1}'))
    _write(cassettes / 'removed.yaml', _entry(uri='https://api.test/old'))
    _write(cassettes / 'same.yaml', _entry())
    (root / 'notes.yaml').write_text('key: value\n', encoding='utf-8')
    _git(root, 'add', '.')
    _git(root, 'commit', '-q', '-m', 'init')
    return root


class TestGitBacked:
    def test_changed_files_include_untracked(self, repo: Path):
        cassettes = repo / 'tests' / 'cassettes'
        _write(cassettes / 'kept.yaml', _entry(body='{"v": 2}'))
        (cassettes / 'removed.yaml').unlink()
        _write(cassettes / 'fresh.yaml', _entry(uri='https://api.test/fresh'))

        found = {(c.path.name, c.status) for c in changed_files(repo / 'tests', 'HEAD')}

        assert found == {
            ('kept.yaml', 'modified'),
            ('removed.yaml', 'deleted'),
            ('fresh.yaml', 'added'),
        }

    def test_engine_diff_against_head(self, repo: Path):
        cassettes = repo / 'tests' / 'cassettes'
        _write(cassettes / 'kept.yaml', _entry(body='{"v": 2}'))
        (cassettes / 'removed.yaml').unlink()
        _write(cassettes / 'fresh.yaml', _entry(uri='https://api.test/fresh'))
        (repo / 'notes.yaml').write_text('key: changed\n', encoding='utf-8')

        engine = PreviewEngine(get_default_config())
        diffs, unreadable = engine.diff_against(repo, 'HEAD')

        assert unreadable == []
        by_name = {d.path.name: d for d in diffs}
        assert set(by_name) == {'kept.yaml', 'removed.yaml', 'fresh.yaml'}
        assert by_name['fresh.yaml'].status == 'added'
        assert by_name['removed.yaml'].status == 'deleted'
        (change,) = by_name['kept.yaml'].changed[0].changes
        assert (change.path, change.before, change.after) == ('$.v', '1', '2')

    def test_unparseable_new_version(self, repo: Path):
        (repo / 'tests' / 'cassettes' / 'kept.yaml').write_text('a: [b\n', encoding='utf-8')
        diffs, unreadable = PreviewEngine(get_default_config()).diff_against(repo, 'HEAD')
        assert diffs == []
        assert [p.name for p, _ in unreadable] == ['kept.yaml']

    @pytest.mark.parametrize('ref', ['', '--output=x'])
    def test_rejects_option_like_refs(self, repo: Path, ref: str):
        with pytest.raises(GitError, match='invalid git ref'):
            changed_files(repo, ref)

    def test_unknown_ref(self, repo: Path):
        with pytest.raises(GitError):
            changed_files(repo, 'no-such-branch')

    def test_outside_a_repository(self, tmp_path: Path):
        outside = tmp_path / 'plain'
        outside.mkdir()
        with pytest.raises(GitError):
            changed_files(outside, 'HEAD')


class TestDiffCli:
    @pytest.fixture(autouse=True)
    def no_global_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(loader, 'load_global_config', lambda: None)

    def test_text_report_and_exit_code(self, repo: Path):
        _write(repo / 'tests' / 'cassettes' / 'kept.yaml', _entry(body='{"v": 2}'))
        runner = CliRunner()

        plain = runner.invoke(main, [str(repo), 'diff'])
        strict = runner.invoke(main, [str(repo), 'diff', 'HEAD', '--exit-code'])

        assert plain.exit_code == 0
        assert strict.exit_code == 1
        kept = str(Path('tests') / 'cassettes' / 'kept.yaml')
        assert f'{kept} (modified): 1 changed, 0 added, 0 removed, 0 unchanged' in plain.output
        assert '~ response.body $.v: 1 -> 2' in plain.output

    def test_ignore_field_and_json(self, repo: Path):
        _write(repo / 'tests' / 'cassettes' / 'kept.yaml', _entry(body='{"v": 2}'))
        runner = CliRunner()

        ignored = runner.invoke(
            main,
            [str(repo), 'diff', '--ignore-field', 'v', '--exit-code'],
        )
        as_json = runner.invoke(main, [str(repo), 'diff', '--format', 'json'])

        assert ignored.exit_code == 0
        assert 'No cassette changes.' in ignored.output
        assert json.loads(as_json.output)[0]['changed'][0]['changes'][0]['after'] == '2'

    def test_git_error_is_reported(self, repo: Path):
        result = CliRunner().invoke(main, [str(repo), 'diff', 'no-such-ref'])
        assert result.exit_code != 0
        assert 'Error:' in result.output
