# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""Interaction parsing and body decoding for VCR cassettes."""

import base64
import gzip
import zlib
from pathlib import Path

import pytest

from vcr_tui.preview.cassette import (
    body_summary,
    decode_body,
    format_row,
    human_size,
    is_cassette,
    parse_cassette,
    render_text,
)
from vcr_tui.preview.engine import PreviewEngine


def _vcrpy(request_body=None, response_body='', headers=None, status=200):
    return {
        'version': 1,
        'interactions': [
            {
                'request': {
                    'method': 'post',
                    'uri': 'https://api.example.com/v1/items?page=2&q=a%20b',
                    'body': request_body,
                    'headers': {'Accept': ['application/json']},
                },
                'response': {
                    'status': {'code': status, 'message': 'OK'},
                    'headers': headers or {},
                    'body': {'string': response_body},
                },
            },
        ],
    }


class TestIsCassette:
    @pytest.mark.parametrize(
        ('data', 'expected'),
        [
            ({'interactions': []}, True),
            ({'http_interactions': []}, True),
            ({'interactions': 'nope'}, False),
            ({'key': 'value'}, False),
            (['interactions'], False),
            (None, False),
        ],
    )
    def test_detects_layouts(self, data, expected):
        assert is_cassette(data) is expected


class TestParseCassette:
    def test_fixture_cassette(self, cassette_data):
        interactions = parse_cassette(cassette_data)

        assert [i.method for i in interactions] == ['GET', 'POST']
        assert [i.status_code for i in interactions] == [200, 201]
        first, second = interactions
        assert first.host == 'api.example.com'
        assert first.path == '/users/1'
        assert first.status == '200 OK'
        assert first.request.body.kind == 'empty'
        assert first.response.body.kind == 'json'
        assert '"name": "John Doe"' in first.response.body.text
        assert first.response.header('content-type') == 'application/json'
        assert second.request.body.kind == 'json'
        assert '"email": "jane@example.com"' in second.request.body.text
        assert second.status == '201 Created'

    def test_query_and_method_normalized(self):
        (interaction,) = parse_cassette(_vcrpy())

        assert interaction.method == 'POST'
        assert interaction.path == '/v1/items?page=2&q=a%20b'
        assert interaction.query == (('page', '2'), ('q', 'a b'))

    def test_ruby_vcr_layout(self):
        payload = base64.b64encode(b'{"ok": true}').decode()
        data = {
            'http_interactions': [
                {
                    'request': {
                        'method': 'get',
                        'uri': 'http://localhost/health',
                        'body': {'encoding': 'UTF-8', 'string': ''},
                        'headers': {},
                    },
                    'response': {
                        'status': {'code': 503, 'message': 'Service Unavailable'},
                        'headers': {'Content-Type': 'application/json'},
                        'body': {'encoding': 'ASCII-8BIT', 'base64_string': payload},
                    },
                    'recorded_at': 'Tue, 01 Nov 2026 00:00:00 GMT',
                },
            ],
            'recorded_with': 'VCR 6.2.0',
        }

        (interaction,) = parse_cassette(data)

        assert interaction.method == 'GET'
        assert interaction.status == '503 Service Unavailable'
        assert interaction.request.body.kind == 'empty'
        assert interaction.response.body.kind == 'json'
        assert interaction.response.body.text == '{\n  "ok": true\n}'
        assert interaction.recorded_at == 'Tue, 01 Nov 2026 00:00:00 GMT'

    def test_malformed_entries_are_tolerated(self):
        data = {'interactions': ['junk', {'request': None, 'response': {'status': 'x'}}]}

        (interaction,) = parse_cassette(data)

        assert interaction.index == 1
        assert interaction.method == '?'
        assert interaction.status_code is None
        assert interaction.status == '-'
        assert interaction.path == '/'

    def test_non_cassette_is_empty(self):
        assert parse_cassette({'key': 'value'}) == []
        assert parse_cassette('text') == []


class TestDecodeBody:
    @pytest.mark.parametrize('raw', [None, '', b''])
    def test_empty(self, raw):
        body = decode_body(raw)
        assert body.kind == 'empty'
        assert body.size == 0

    def test_json_detected_without_content_type(self):
        body = decode_body('[1, 2]')
        assert body.kind == 'json'
        assert body.text == '[\n  1,\n  2\n]'
        assert body.size == len('[1, 2]')

    def test_invalid_json_falls_back_to_text(self):
        body = decode_body('{not json', {'Content-Type': ['application/json']})
        assert body.kind == 'text'
        assert body.text == '{not json'

    def test_unicode_kept_and_sized_in_bytes(self):
        body = decode_body('{"name": "Zoë"}')
        assert '"Zoë"' in body.text
        assert body.size == len('{"name": "Zoë"}'.encode())

    def test_gzip_bytes(self):
        raw = gzip.compress(b'{"compressed": 1}')
        body = decode_body(raw, {'Content-Encoding': ['gzip']})
        assert body.kind == 'json'
        assert body.notes == ('gzip-decoded',)
        assert '"compressed": 1' in body.text

    @pytest.mark.parametrize('wbits', [zlib.MAX_WBITS, -zlib.MAX_WBITS])
    def test_deflate_bytes(self, wbits):
        compressor = zlib.compressobj(wbits=wbits)
        raw = compressor.compress(b'plain text') + compressor.flush()
        body = decode_body(raw, {'content-encoding': 'deflate'})
        assert body.kind == 'text'
        assert body.text == 'plain text'
        assert body.notes == ('deflate-decoded',)

    def test_binary_placeholder(self):
        body = decode_body(b'\x89PNG\r\n\x1a\n\xff\xfe')
        assert body.kind == 'binary'
        assert body.text == '<10 bytes of binary data>'
        assert body.size == 10

    def test_form_encoded(self):
        body = decode_body(
            'grant_type=client_credentials&scope=read+write',
            {'Content-Type': ['application/x-www-form-urlencoded']},
        )
        assert body.kind == 'form'
        assert body.text == 'grant_type = client_credentials\nscope = read write'

    @pytest.mark.parametrize(
        ('raw', 'content_type', 'kind'),
        [
            ('<!DOCTYPE html><p>hi</p>', '', 'html'),
            ('<p>hi</p>', 'text/html; charset=utf-8', 'html'),
            ('<?xml version="1.0"?><a/>', '', 'xml'),
            ('<a/>', 'application/xml', 'xml'),
            ('hello', 'text/plain', 'text'),
        ],
    )
    def test_markup_and_text(self, raw, content_type, kind):
        assert decode_body(raw, {'Content-Type': [content_type]}).kind == kind


class TestFormatting:
    @pytest.mark.parametrize(
        ('size', 'expected'),
        [(0, '0 B'), (1023, '1023 B'), (1536, '1.5 KB'), (3 * 1024 * 1024, '3.0 MB')],
    )
    def test_human_size(self, size, expected):
        assert human_size(size) == expected

    def test_format_row(self, cassette_data):
        row = format_row(parse_cassette(cassette_data)[1])
        assert row.split() == ['1', 'POST', '201', '112', 'B', 'api.example.com/users']

    def test_body_summary(self):
        assert body_summary(decode_body(None)) == 'no body'
        gz = decode_body(gzip.compress(b'{}'))
        assert body_summary(gz) == 'json, 2 B, gzip-decoded'

    def test_render_text(self, cassette_data):
        text = render_text(parse_cassette(cassette_data)[1])
        lines = text.splitlines()

        assert lines[:2] == ['POST https://api.example.com/users', '-> 201 Created']
        assert '== Request (json, 49 B) ==' in lines
        assert '== Response (json, 112 B) ==' in lines
        assert 'Content-Type: application/json' in lines
        assert '  "role": "user",' in lines

    def test_render_text_skips_empty_body(self, cassette_data):
        text = render_text(parse_cassette(cassette_data)[0])
        request_section = text.split('== Response')[0]
        assert '== Request (no body) ==' in request_section
        assert request_section.rstrip().endswith('User-Agent: python-requests/2.28.0')


class TestEngineInteractions:
    def test_cassette(self, cassette_path):
        interactions = PreviewEngine.get_interactions(cassette_path)
        assert interactions is not None
        assert len(interactions) == 2

    def test_non_cassette_is_none(self, tmp_path: Path):
        path = tmp_path / 'doc.yaml'
        path.write_text('key: value\n', encoding='utf-8')
        assert PreviewEngine.get_interactions(path) is None
