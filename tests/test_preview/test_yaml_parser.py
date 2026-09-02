"""Tests for the public API of vcr_tui.preview.yaml_parser."""

import pytest

from vcr_tui.preview.yaml_parser import get_value_at_path, get_yaml_keys


@pytest.fixture(scope="module")
def keys(cassette_path):
    return {k.path: k for k in get_yaml_keys(cassette_path)}


class TestLoadYaml:
    def test_top_level_document(self, cassette_data):
        assert isinstance(cassette_data, dict)
        assert set(cassette_data) == {"interactions", "version"}
        assert cassette_data["version"] == 1
        assert len(cassette_data["interactions"]) == 2

    def test_interaction_methods(self, cassette_data):
        methods = [i["request"]["method"] for i in cassette_data["interactions"]]
        assert methods == ["GET", "POST"]


class TestGetYamlKeys:
    @pytest.mark.parametrize(
        ("path", "display", "depth", "is_leaf"),
        [
            ("interactions", "interactions", 0, False),
            ("version", "version", 0, True),
            ("interactions[0]", "[0]", 1, False),
            ("interactions[1]", "[1]", 1, False),
            ("interactions[0].request", "request", 2, False),
            ("interactions[0].request.method", "method", 3, True),
            ("interactions[0].request.body", "body", 3, True),  # null value is a leaf
            ("interactions[0].request.headers", "headers", 3, False),
            ("interactions[0].response.body.string", "string", 4, True),
            ("interactions[0].response.status.code", "code", 4, True),
            ("interactions[1].response.status.message", "message", 4, True),
        ],
    )
    def test_extracted_keys(self, keys, path, display, depth, is_leaf):
        key = keys[path]
        assert key.display == display
        assert key.depth == depth
        assert key.is_leaf is is_leaf

    def test_only_top_level_keys_have_depth_zero(self, keys):
        assert [p for p, k in keys.items() if k.depth == 0] == ["interactions", "version"]


class TestGetValueAtPath:
    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            # Whole-document access
            ("", "root"),
            (".", "root"),
            # Dict access
            ("version", 1),
            (".version", 1),  # leading dot tolerated
            ("interactions[0].response.status.code", 200),
            ("interactions[1].response.status.message", "Created"),
            # List indexing
            ("interactions[0].request.method", "GET"),
            ("interactions[1].request.method", "POST"),
            # Body string returned verbatim, not parsed
            (
                "interactions[0].response.body.string",
                '{"id": 1, "name": "John Doe", "email": "john@example.com", "role": "admin"}',
            ),
            # Missing keys / bad indices -> None
            ("nonexistent", None),
            ("interactions[5]", None),
            ("interactions[-1]", None),
            ("interactions[0].nope", None),
            ("interactions[0].request.method.deeper", None),
            ("version[0]", None),  # indexing into a scalar
            ("interactions.version", None),  # keying into a list
        ],
    )
    def test_paths(self, cassette_data, path, expected):
        result = get_value_at_path(cassette_data, path)
        if expected == "root":
            assert result is cassette_data
        else:
            assert result == expected
