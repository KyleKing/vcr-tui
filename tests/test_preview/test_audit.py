# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""Suite-wide summary and findings over parsed cassettes."""

import json
from pathlib import Path

import pytest

from vcr_tui.config.defaults import get_default_config
from vcr_tui.preview.audit import (
    AuditOptions,
    Cassette,
    audit,
    find_test,
    is_redacted,
    render_report,
    report_to_dict,
    template_path,
)
from vcr_tui.preview.cassette import parse_cassette
from vcr_tui.preview.engine import PreviewEngine

ROOT = Path('/suite')


def _interaction(
    uri='https://api.example.com/items/1',
    method='GET',
    status=200,
    request_headers=None,
    response_headers=None,
    request_body=None,
    response_body='',
):
    return {
        'request': {
            'method': method,
            'uri': uri,
            'body': request_body,
            'headers': request_headers or {},
        },
        'response': {
            'status': {'code': status, 'message': ''},
            'headers': response_headers or {},
            'body': {'string': response_body},
        },
    }


def _cassette(*entries, name='cassette.yaml'):
    interactions = tuple(parse_cassette({'interactions': list(entries)}))
    return Cassette(path=ROOT / name, interactions=interactions)


def _codes(report):
    return [(f.severity, f.code) for f in report.findings]


class TestTemplatePath:
    @pytest.mark.parametrize(
        ('path', 'expected'),
        [
            ('/users/1', '/users/{id}'),
            ('/users/42?expand=true', '/users/{id}'),
            ('/orders/3f2b8c1e-5d4a-4b6e-9c7d-1a2b3c4d5e6f/items', '/orders/{id}/items'),
            ('/commits/0123456789abcdef0123', '/commits/{id}'),
            ('/v2/users', '/v2/users'),
            ('/', '/'),
            ('?q=1', '/'),
        ],
    )
    def test_templates_ids(self, path, expected):
        assert template_path(path) == expected


class TestIsRedacted:
    @pytest.mark.parametrize(
        'value',
        ['', 'REDACTED', 'Bearer REDACTED', '***', 'XXXX', '<API_KEY>', '[FILTERED]', 'DUMMY'],
    )
    def test_redacted(self, value):
        assert is_redacted(value)

    @pytest.mark.parametrize('value', ['Bearer abc123def456', 'Basic dXNlcjpwYXNz', 's3cr3t'])
    def test_not_redacted(self, value):
        assert not is_redacted(value)


class TestSummary:
    def test_counts_hosts_and_endpoints(self):
        report = audit(
            [
                _cassette(
                    _interaction(uri='https://a.test/users/1'),
                    _interaction(uri='https://a.test/users/2', status=404),
                    _interaction(uri='https://b.test/health'),
                ),
                _cassette(name='empty.yaml'),
            ],
            AuditOptions(check_tests=False),
        )

        assert report.cassettes == 2
        assert report.interactions == 3
        assert report.hosts == {'a.test': 2, 'b.test': 1}
        top = report.endpoints[0]
        assert (top.method, top.host, top.path) == ('GET', 'a.test', '/users/{id}')
        assert top.statuses == {200: 1, 404: 1}
        assert top.count == 2
        assert _codes(report) == [('warning', 'empty-cassette')]

    def test_clean_suite_has_no_findings(self):
        report = audit([_cassette(_interaction())])
        assert report.findings == []
        assert report.counts() == {'error': 0, 'warning': 0, 'info': 0}
        assert not report.failed('info')


class TestSecrets:
    def test_unredacted_authorization_header(self):
        report = audit([_cassette(_interaction(request_headers={'Authorization': ['Bearer abc']}))])
        assert _codes(report) == [('error', 'secret-header')]
        assert report.findings[0].index == 0
        assert report.failed('error')

    def test_redacted_header_passes(self):
        headers = {'Authorization': ['Bearer REDACTED'], 'X-Auth-Token': ['***']}
        assert audit([_cassette(_interaction(request_headers=headers))]).findings == []

    def test_header_name_words(self):
        headers = {'X-Upstream-Token': ['live-value']}
        assert _codes(audit([_cassette(_interaction(request_headers=headers))])) == [
            ('error', 'secret-header'),
        ]

    def test_query_parameter(self):
        uri = 'https://api.test/search?q=x&api_key=live123'
        report = audit([_cassette(_interaction(uri=uri))])
        assert _codes(report) == [('error', 'secret-query')]
        assert 'api_key' in report.findings[0].message

    def test_body_fields(self):
        body = '{"access_token": "abc.def", "refresh_token": "REDACTED", "user": "me"}'
        report = audit([_cassette(_interaction(response_body=body))])
        assert _codes(report) == [('error', 'secret-field')]
        assert report.findings[0].message == 'response body has unredacted access_token'

    def test_form_fields(self):
        report = audit([
            _cassette(
                _interaction(
                    method='POST',
                    request_headers={'Content-Type': ['application/x-www-form-urlencoded']},
                    request_body='grant_type=password&password=hunter2',
                ),
            ),
        ])
        assert _codes(report) == [('error', 'secret-field')]
        assert report.findings[0].message.startswith('request body')

    @pytest.mark.parametrize(
        ('text', 'label'),
        [
            ('token eyJhbGciOiJIUzI1.eyJzdWIiOiIxMjM0.SflKxwRJSMeKKF2QT4', 'JWT'),
            ('key AKIAABCDEFGHIJKLMNOP here', 'AWS access key'),
            ('ghp_' + 'a' * 36, 'GitHub token'),
            ('-----BEGIN RSA PRIVATE KEY-----', 'private key'),
        ],
    )
    def test_token_patterns(self, text, label):
        report = audit([_cassette(_interaction(response_body=text))])
        assert ('error', 'secret-token') in _codes(report)
        assert any(label in f.message for f in report.findings)

    def test_set_cookie_and_email(self):
        report = audit([
            _cassette(
                _interaction(
                    response_headers={'Set-Cookie': ['session=abc']},
                    response_body='{"email": "a@example.com", "cc": "b@example.org"}',
                ),
            ),
        ])
        assert _codes(report) == [('warning', 'set-cookie'), ('info', 'email')]
        assert '2 email address(es)' in report.findings[1].message
        assert report.failed('warning')
        assert not report.failed('error')


class TestOtherFindings:
    def test_large_body_server_error_and_duplicates(self):
        report = audit(
            [
                _cassette(
                    _interaction(response_body='x' * 2048),
                    _interaction(status=503),
                    _interaction(),
                ),
            ],
            AuditOptions(max_body_bytes=1024, check_tests=False),
        )
        assert _codes(report) == [
            ('warning', 'large-body'),
            ('info', 'duplicate'),
            ('info', 'server-error'),
        ]
        duplicate = report.findings[1]
        assert duplicate.message == (
            'GET https://api.example.com/items/1 recorded 3 times (#0, 1, 2)'
        )

    def test_skip_codes(self):
        cassette = _cassette(_interaction(request_headers={'Cookie': ['a=b']}))
        report = audit([cassette], AuditOptions(skip=frozenset({'secret-header'})))
        assert report.findings == []

    def test_unreadable_files(self):
        report = audit([], unreadable=[(ROOT / 'bad.yaml', 'mapping values are not allowed')])
        assert _codes(report) == [('warning', 'unreadable')]
        assert report.findings[0].location(ROOT) == 'bad.yaml'

    def test_failed_threshold_never(self):
        report = audit([_cassette(_interaction(request_headers={'Cookie': ['a=b']}))])
        assert not report.failed('never')


class TestFindTest:
    def _suite(self, tmp_path: Path) -> Path:
        tests = tmp_path / 'tests'
        (tests / 'cassettes' / 'test_api').mkdir(parents=True)
        (tests / 'test_api.py').write_text(
            'def test_list():\n    pass\n\n\nclass TestUsers:\n    async def test_get(self):\n'
            '        pass\n',
            encoding='utf-8',
        )
        return tests

    @pytest.mark.parametrize(
        ('relative', 'expected'),
        [
            ('cassettes/test_api/test_list.yaml', True),
            ('cassettes/test_api/TestUsers.test_get.yaml', True),
            ('cassettes/test_api/test_list[case-1].yaml', True),
            ('cassettes/test_api/test_removed.yaml', False),
            ('cassettes/test_list.yaml', True),
            ('cassettes/fixture_data.yaml', None),
            ('elsewhere/test_list.yaml', None),
        ],
    )
    def test_matches_pytest_recording_layout(self, tmp_path, relative, expected):
        assert find_test(self._suite(tmp_path) / relative) is expected

    def test_missing_test_is_a_warning(self, tmp_path):
        path = self._suite(tmp_path) / 'cassettes' / 'test_api' / 'test_removed.yaml'
        report = audit([Cassette(path=path, interactions=())])
        assert ('warning', 'no-test') in _codes(report)


class TestRendering:
    def _report(self):
        return audit(
            [
                _cassette(
                    _interaction(request_headers={'Authorization': ['Bearer live']}),
                    _interaction(uri='https://api.example.com/items/2', status=500),
                ),
            ],
            AuditOptions(check_tests=False),
        )

    def test_render_report(self):
        lines = render_report(self._report(), ROOT).splitlines()
        assert lines[0] == '1 cassettes, 2 interactions, 1 hosts'
        assert '  api.example.com  2' in lines
        assert lines[lines.index('Endpoints') + 1].split() == [
            'GET',
            'api.example.com/items/{id}',
            '200x1',
            '500x1',
        ]
        assert 'Findings (1 error, 0 warning, 1 info)' in lines
        assert lines[-2].split()[:3] == ['error', 'secret-header', 'cassette.yaml#0']

    def test_render_without_findings(self):
        text = render_report(audit([]), ROOT)
        assert text.endswith('Findings (0 error, 0 warning, 0 info)\n  none')

    def test_report_to_dict_is_json_ready(self):
        data = report_to_dict(self._report(), ROOT)
        round_trip = json.loads(json.dumps(data))
        assert round_trip['counts'] == {'error': 1, 'warning': 0, 'info': 1}
        assert round_trip['endpoints'][0]['statuses'] == {'200': 1, '500': 1}
        assert round_trip['findings'][0]['location'] == 'cassette.yaml#0'


class TestEngineLoadCassettes:
    def test_loads_cassettes_and_reports_unreadable(self, tmp_path, cassette_path):
        directory = tmp_path / 'cassettes'
        directory.mkdir()
        (directory / 'example_api.yaml').write_text(
            cassette_path.read_text(encoding='utf-8'),
            encoding='utf-8',
        )
        (directory / 'broken.yaml').write_text('key: [unclosed\n', encoding='utf-8')
        (directory / 'plain.yaml').write_text('key: value\n', encoding='utf-8')

        engine = PreviewEngine(get_default_config())
        cassettes, unreadable = engine.load_cassettes(directory)

        assert [c.path.name for c in cassettes] == ['example_api.yaml']
        assert len(cassettes[0].interactions) == 2
        assert [p.name for p, _reason in unreadable] == ['broken.yaml']
