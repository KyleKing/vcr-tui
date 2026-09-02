"""Tests for the public API of vcr_tui.preview.yaml_parser."""

import pytest

from vcr_tui.preview.yaml_parser import get_value_at_path, get_yaml_keys


class TestLoadYaml:
    def test_loads_cassette_root_dict(self, cassette_path, cassette_data):
        assert isinstance(cassette_data, dict)
        assert set(cassette_data) == {"interactions", "version"}
        assert cassette_data["version"] == 1

    def test_interactions_structure(self, cassette_data):
        interactions = cassette_data["interactions"]
        assert isinstance(interactions, list)
        assert len(interactions) == 2
        methods = [i["request"]["method"] for i in interactions]
        assert methods == ["GET", "POST"]


class TestGetYamlKeys:
    def test_top_level_keys(self, cassette_path):
        keys = get_yaml_keys(cassette_path)
        top = [k for k in keys if k.depth == 0]
        assert [k.display for k in top] == ["interactions", "version"]
        assert top[0].path == "interactions"
        assert not top[0].is_leaf
        assert top[1].is_leaf

    def test_list_indices_appear_as_keys(self, cassette_path):
        keys = {k.path: k for k in get_yaml_keys(cassette_path)}
        assert "interactions[0]" in keys
        assert "interactions[1]" in keys
        assert keys["interactions[0]"].display == "[0]"
        assert not keys["interactions[0]"].is_leaf

    def test_nested_leaf_paths(self, cassette_path):
        paths = {k.path for k in get_yaml_keys(cassette_path)}
        assert "interactions[0].request.method" in paths
        assert "interactions[0].response.body.string" in paths
        assert "interactions[0].response.status.code" in paths

    def test_depth_increases_with_nesting(self, cassette_path):
        by_path = {k.path: k for k in get_yaml_keys(cassette_path)}
        assert by_path["interactions"].depth == 0
        assert by_path["interactions[0]"].depth == 1
        assert by_path["interactions[0].request"].depth == 2
        assert by_path["interactions[0].request.method"].depth == 3

    def test_leaf_flags(self, cassette_path):
        by_path = {k.path: k for k in get_yaml_keys(cassette_path)}
        assert by_path["interactions[0].request.method"].is_leaf
        assert by_path["interactions[0].request.body"].is_leaf  # null value
        assert not by_path["interactions[0].request.headers"].is_leaf


class TestGetValueAtPath:
    def test_root_path_dot_returns_whole_document(self, cassette_data):
        assert get_value_at_path(cassette_data, ".") is cassette_data

    def test_empty_path_returns_whole_document(self, cassette_data):
        assert get_value_at_path(cassette_data, "") is cassette_data

    def test_dict_access(self, cassette_data):
        assert get_value_at_path(cassette_data, "version") == 1
        value = get_value_at_path(cassette_data, "interactions[0].response.status.code")
        assert value == 200

    def test_list_indexing(self, cassette_data):
        assert get_value_at_path(cassette_data, "interactions[0]")["request"]["method"] == "GET"
        assert get_value_at_path(cassette_data, "interactions[1]")["request"]["method"] == "POST"

    def test_leading_dot_is_tolerated(self, cassette_data):
        assert get_value_at_path(cassette_data, ".version") == 1

    @pytest.mark.parametrize(
        "path",
        [
            "nonexistent",
            "interactions[5]",
            "interactions[-1]",
            "interactions[0].nope",
            "interactions[0].request.method.deeper",
            "version[0]",
        ],
    )
    def test_missing_paths_return_none(self, cassette_data, path):
        assert get_value_at_path(cassette_data, path) is None

    def test_body_string_is_returned_verbatim(self, cassette_data):
        value = get_value_at_path(cassette_data, "interactions[0].response.body.string")
        assert value == (
            '{"id": 1, "name": "John Doe", "email": "john@example.com", "role": "admin"}'
        )
