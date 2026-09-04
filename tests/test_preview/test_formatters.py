# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""Tests for the public API of vcr_tui.preview.formatters."""

import json

import pytest

from vcr_tui.preview.formatters import format_content
from vcr_tui.preview.yaml_parser import get_value_at_path

EMBEDDED_JSON = '{"id": 1, "name": "John Doe", "email": "john@example.com", "role": "admin"}'


class TestFormatJson:
    def test_dict_is_pretty_printed(self):
        result = format_content({'id': 1, 'name': 'John'}, 'json')
        assert json.loads(result) == {'id': 1, 'name': 'John'}
        assert '\n  "id": 1,' in result

    def test_string_with_embedded_json_is_parsed_and_pretty_printed(self):
        result = format_content(EMBEDDED_JSON, 'json')
        assert json.loads(result) == json.loads(EMBEDDED_JSON)
        assert '\n  "name": "John Doe",' in result

    def test_malformed_json_string_falls_back_to_verbatim(self):
        assert format_content('not json {', 'json') == 'not json {'

    def test_none(self):
        assert json.loads(format_content(None, 'json')) is None

    def test_list(self):
        assert json.loads(format_content([1, 2], 'json')) == [1, 2]


class TestFormatYaml:
    def test_dict(self):
        result = format_content({'version': 1, 'nested': {'a': True}}, 'yaml')
        assert result == 'version: 1\nnested:\n  a: true'

    def test_string_content_is_dumped_as_scalar(self):
        # No document-end marker for a bare scalar.
        assert format_content('hello', 'yaml') == 'hello'

    def test_embedded_json_string_expands_into_nested_keys(self):
        result = format_content({'body': EMBEDDED_JSON}, 'yaml')
        assert 'name: John Doe' in result
        assert 'email: john@example.com' in result
        assert '\\' not in result

    def test_embedded_json_array_string_expands(self):
        result = format_content({'items': '[1, 2, 3]'}, 'yaml')
        assert result == 'items:\n- 1\n- 2\n- 3'

    def test_nested_embedded_json_string_expands_recursively(self):
        inner = '{"a": 1}'
        outer = json.dumps({'b': inner})
        result = format_content({'payload': outer}, 'yaml')
        assert 'payload:' in result
        assert 'b:' in result
        assert 'a: 1' in result

    def test_plain_string_value_survives_untouched(self):
        result = format_content({'uri': 'https://api.example.com/users/1'}, 'yaml')
        assert 'uri: https://api.example.com/users/1' in result

    def test_invalid_and_scalar_json_strings_stay_strings(self):
        result = format_content(
            {
                'not_json': '{oops',
                'number_string': '42',
                'bool_string': 'true',
                'null_string': 'null',
            },
            'yaml',
        )
        assert "not_json: '{oops'" in result
        assert "number_string: '42'" in result
        assert "bool_string: 'true'" in result
        assert "null_string: 'null'" in result

    def test_input_is_not_mutated(self):
        data = {'body': EMBEDDED_JSON}
        format_content(data, 'yaml')
        assert data['body'] == EMBEDDED_JSON


class TestFormatText:
    def test_plain_string_unchanged(self):
        assert format_content('hello world', 'text') == 'hello world'

    def test_non_string_is_str_coerced(self):
        assert format_content(42, 'text') == '42'
        assert format_content(None, 'text') == 'None'

    def test_literal_backslash_n_is_unescaped(self):
        assert format_content('a\\nb', 'text') == 'a\nb'

    def test_literal_backslash_t_is_unescaped(self):
        assert format_content('a\\tb', 'text') == 'a\tb'

    def test_backslash_r_is_stripped(self):
        # NOTE: current behaviour also strips real carriage returns.
        assert format_content('a\\rb', 'text') == 'ab'


class TestFormatHtml:
    def test_valid_xml_is_pretty_printed(self):
        result = format_content('<html><body><p>hi</p></body></html>', 'html')
        assert '<p>' in result
        assert result.count('\n') > 0

    def test_malformed_markup_falls_back_to_verbatim(self):
        assert format_content('<p>not closed', 'html') == '<p>not closed'

    def test_non_string_is_str_coerced(self):
        assert format_content(5, 'html') == '5'


class TestFormatTomL:
    def test_dict_is_dumped(self):
        # NOTE: tomli_w appends a trailing newline; _format_toml does not strip it.
        assert format_content({'version': 1, 'name': 'cassette'}, 'toml') == (
            'version = 1\nname = "cassette"\n'
        )

    def test_non_table_content_falls_back_to_verbatim_instead_of_raising(self):
        assert format_content(1, 'toml') == '1'
        assert format_content([1, 2], 'toml') == '[1, 2]'

    def test_string_is_returned_verbatim(self):
        assert format_content(EMBEDDED_JSON, 'toml') == EMBEDDED_JSON


class TestFormatContentWithCassetteData:
    @pytest.mark.parametrize(
        ('path', 'formatter', 'expected'),
        [
            ('version', 'json', '1'),
            ('version', 'text', '1'),
            ('interactions[0].request.method', 'json', 'GET'),
            ('interactions[0].response.status.message', 'text', 'OK'),
        ],
    )
    def test_scalar_paths(self, cassette_data, path, formatter, expected):
        assert format_content(get_value_at_path(cassette_data, path), formatter) == expected

    def test_yaml_scalar_path_has_no_document_end_marker(self, cassette_data):
        version = get_value_at_path(cassette_data, 'version')
        assert format_content(version, 'yaml') == '1'

    def test_toml_scalar_path_falls_back_to_verbatim(self, cassette_data):
        version = get_value_at_path(cassette_data, 'version')
        assert format_content(version, 'toml') == '1'

    def test_response_body_key_renders_json(self, cassette_data):
        body = get_value_at_path(cassette_data, 'interactions[0].response.body.string')
        parsed = json.loads(format_content(body, 'json'))
        assert parsed['id'] == 1
        assert parsed['name'] == 'John Doe'

    def test_yaml_key_path_expands_embedded_json(self, cassette_data):
        # Regression: with a yaml-formatted rule (e.g. the 'yaml' channel's '.'
        # rule), the body string used to stay an escaped one-line string.
        body = get_value_at_path(cassette_data, 'interactions[0].response.body.string')
        result = format_content(body, 'yaml')
        assert 'name: John Doe' in result
        assert 'email: john@example.com' in result
