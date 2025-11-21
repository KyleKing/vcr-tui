"""Tests for YAML parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from vcr_tui.preview.yaml_parser import YAMLParser


class TestYAMLParser:
    """Tests for YAMLParser class."""

    @pytest.fixture
    def parser(self) -> YAMLParser:
        """Return a YAMLParser instance."""
        return YAMLParser()

    def test_parser_initialization(self, parser: YAMLParser) -> None:
        """Test that parser initializes correctly."""
        assert parser is not None
        assert parser.yaml is not None

    def test_load_existing_file(self, parser: YAMLParser, cassettes_dir: Path) -> None:
        """Test loading an existing YAML file."""
        cassette = cassettes_dir / "example_api.yaml"
        data = parser.load(cassette)

        assert data is not None
        assert isinstance(data, dict)
        assert "version" in data
        assert "interactions" in data

    def test_load_nonexistent_file(self, parser: YAMLParser, tmp_path: Path) -> None:
        """Test loading non-existent file raises FileNotFoundError."""
        nonexistent = tmp_path / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError, match="not found"):
            parser.load(nonexistent)

    def test_load_invalid_yaml(self, parser: YAMLParser, tmp_path: Path) -> None:
        """Test loading invalid YAML raises ValueError."""
        invalid_yaml = tmp_path / "invalid.yaml"
        invalid_yaml.write_text("[invalid yaml content")

        with pytest.raises(ValueError, match="Invalid YAML"):
            parser.load(invalid_yaml)


class TestGetAllKeys:
    """Tests for get_all_keys method."""

    @pytest.fixture
    def parser(self) -> YAMLParser:
        """Return a YAMLParser instance."""
        return YAMLParser()

    def test_empty_dict(self, parser: YAMLParser) -> None:
        """Test extracting keys from empty dict."""
        keys = parser.get_all_keys({})

        assert keys == []

    def test_flat_dict(self, parser: YAMLParser) -> None:
        """Test extracting keys from flat dict."""
        data = {"name": "John", "age": 30, "email": "john@example.com"}
        keys = parser.get_all_keys(data)

        assert set(keys) == {"name", "age", "email"}

    def test_nested_dict(self, parser: YAMLParser) -> None:
        """Test extracting keys from nested dict."""
        data = {"user": {"name": "John", "contact": {"email": "john@example.com"}}}
        keys = parser.get_all_keys(data)

        expected = {"user", "user.name", "user.contact", "user.contact.email"}
        assert set(keys) == expected

    def test_list_items(self, parser: YAMLParser) -> None:
        """Test extracting keys from list."""
        data = {"items": [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]}
        keys = parser.get_all_keys(data)

        expected = {
            "items",
            "items[0]",
            "items[0].id",
            "items[0].name",
            "items[1]",
            "items[1].id",
            "items[1].name",
        }
        assert set(keys) == expected

    def test_nested_lists(self, parser: YAMLParser) -> None:
        """Test extracting keys from nested lists."""
        data = {"matrix": [[1, 2], [3, 4]]}
        keys = parser.get_all_keys(data)

        expected = {
            "matrix",
            "matrix[0]",
            "matrix[0][0]",
            "matrix[0][1]",
            "matrix[1]",
            "matrix[1][0]",
            "matrix[1][1]",
        }
        assert set(keys) == expected

    def test_mixed_structure(self, parser: YAMLParser) -> None:
        """Test extracting keys from complex mixed structure."""
        data = {
            "version": 1,
            "config": {"debug": True, "servers": ["localhost", "remote"]},
            "users": [{"id": 1, "roles": ["admin"]}, {"id": 2, "roles": ["user"]}],
        }
        keys = parser.get_all_keys(data)

        expected = {
            "version",
            "config",
            "config.debug",
            "config.servers",
            "config.servers[0]",
            "config.servers[1]",
            "users",
            "users[0]",
            "users[0].id",
            "users[0].roles",
            "users[0].roles[0]",
            "users[1]",
            "users[1].id",
            "users[1].roles",
            "users[1].roles[0]",
        }
        assert set(keys) == expected

    def test_get_all_keys_with_prefix(self, parser: YAMLParser) -> None:
        """Test get_all_keys with existing prefix."""
        data = {"name": "John", "age": 30}
        keys = parser.get_all_keys(data, prefix="user")

        expected = {"user.name", "user.age"}
        assert set(keys) == expected

    def test_empty_list(self, parser: YAMLParser) -> None:
        """Test extracting keys from empty list."""
        data = {"items": []}
        keys = parser.get_all_keys(data)

        assert keys == ["items"]

    def test_scalar_values_not_expanded(self, parser: YAMLParser) -> None:
        """Test that scalar values don't generate extra keys."""
        data = {"text": "hello", "number": 42, "flag": True}
        keys = parser.get_all_keys(data)

        # Should only have the top-level keys, not the values
        assert set(keys) == {"text", "number", "flag"}

    def test_real_vcr_cassette_structure(
        self, parser: YAMLParser, cassettes_dir: Path
    ) -> None:
        """Test extracting keys from real VCR cassette."""
        cassette = cassettes_dir / "example_api.yaml"
        data = parser.load(cassette)
        keys = parser.get_all_keys(data)

        # Should include top-level keys
        assert "version" in keys
        assert "interactions" in keys

        # Should include array access
        assert "interactions[0]" in keys
        assert "interactions[1]" in keys

        # Should include nested request/response keys
        assert "interactions[0].request" in keys
        assert "interactions[0].response" in keys
        assert "interactions[0].response.body" in keys
        assert "interactions[0].response.body.string" in keys


class TestGetValueAtPath:
    """Tests for get_value_at_path method."""

    @pytest.fixture
    def parser(self) -> YAMLParser:
        """Return a YAMLParser instance."""
        return YAMLParser()

    @pytest.fixture
    def sample_data(self) -> dict:
        """Return sample data for testing."""
        return {
            "user": {"name": "John", "age": 30, "contact": {"email": "john@example.com"}},
            "items": [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}],
            "matrix": [[1, 2], [3, 4]],
        }

    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            ("user.name", "John"),
            ("user.age", 30),
            ("user.contact.email", "john@example.com"),
            ("items[0].id", 1),
            ("items[0].name", "Item 1"),
            ("items[1].id", 2),
            ("matrix[0][0]", 1),
            ("matrix[0][1]", 2),
            ("matrix[1][0]", 3),
            ("matrix[1][1]", 4),
        ],
    )
    def test_get_value_at_valid_paths(
        self,
        parser: YAMLParser,
        sample_data: dict,
        path: str,
        expected: object,
    ) -> None:
        """Test getting values at various valid paths."""
        result = parser.get_value_at_path(sample_data, path)
        assert result == expected

    def test_get_value_empty_path_returns_root(
        self, parser: YAMLParser, sample_data: dict
    ) -> None:
        """Test that empty path returns root data."""
        result = parser.get_value_at_path(sample_data, "")
        assert result == sample_data

    def test_get_value_at_missing_key(self, parser: YAMLParser, sample_data: dict) -> None:
        """Test getting value at non-existent key raises KeyError."""
        with pytest.raises(KeyError, match="not found"):
            parser.get_value_at_path(sample_data, "user.nonexistent")

    def test_get_value_at_invalid_index(
        self, parser: YAMLParser, sample_data: dict
    ) -> None:
        """Test getting value at out-of-range index raises IndexError."""
        with pytest.raises(IndexError, match="out of range"):
            parser.get_value_at_path(sample_data, "items[10]")

    def test_get_value_wrong_type_for_key(
        self, parser: YAMLParser, sample_data: dict
    ) -> None:
        """Test accessing key on non-dict raises KeyError."""
        with pytest.raises(KeyError, match="Expected dict"):
            parser.get_value_at_path(sample_data, "user.name.invalid")

    def test_get_value_wrong_type_for_index(
        self, parser: YAMLParser, sample_data: dict
    ) -> None:
        """Test accessing index on non-list raises KeyError."""
        with pytest.raises(KeyError, match="Expected list"):
            parser.get_value_at_path(sample_data, "user[0]")

    def test_get_nested_object(self, parser: YAMLParser, sample_data: dict) -> None:
        """Test getting nested object returns the whole object."""
        result = parser.get_value_at_path(sample_data, "user.contact")
        assert result == {"email": "john@example.com"}

    def test_get_array_item(self, parser: YAMLParser, sample_data: dict) -> None:
        """Test getting array item returns the whole item."""
        result = parser.get_value_at_path(sample_data, "items[0]")
        assert result == {"id": 1, "name": "Item 1"}


class TestParsePath:
    """Tests for _parse_path method."""

    @pytest.fixture
    def parser(self) -> YAMLParser:
        """Return a YAMLParser instance."""
        return YAMLParser()

    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            ("name", ["name"]),
            ("user.name", ["user", "name"]),
            ("user.contact.email", ["user", "contact", "email"]),
            ("items[0]", ["items", 0]),
            ("items[0].id", ["items", 0, "id"]),
            ("items[10].name", ["items", 10, "name"]),
            ("matrix[0][1]", ["matrix", 0, 1]),
            ("data.items[0].tags[2]", ["data", "items", 0, "tags", 2]),
        ],
    )
    def test_parse_valid_paths(
        self,
        parser: YAMLParser,
        path: str,
        expected: list[str | int],
    ) -> None:
        """Test parsing various valid path formats."""
        result = parser._parse_path(path)
        assert result == expected

    def test_parse_empty_path(self, parser: YAMLParser) -> None:
        """Test parsing empty path returns empty list."""
        result = parser._parse_path("")
        assert result == []

    def test_parse_unclosed_bracket(self, parser: YAMLParser) -> None:
        """Test parsing path with unclosed bracket raises ValueError."""
        with pytest.raises(ValueError, match="Unclosed bracket"):
            parser._parse_path("items[0")

    def test_parse_invalid_index(self, parser: YAMLParser) -> None:
        """Test parsing path with non-numeric index raises ValueError."""
        with pytest.raises(ValueError, match="Invalid array index"):
            parser._parse_path("items[abc]")


class TestIntegration:
    """Integration tests using real fixtures."""

    @pytest.fixture
    def parser(self) -> YAMLParser:
        """Return a YAMLParser instance."""
        return YAMLParser()

    def test_load_and_extract_vcr_cassette(
        self, parser: YAMLParser, cassettes_dir: Path
    ) -> None:
        """Test complete workflow: load cassette and extract values."""
        cassette = cassettes_dir / "example_api.yaml"

        # Load the cassette
        data = parser.load(cassette)

        # Extract all keys
        keys = parser.get_all_keys(data)

        # Verify we can access important paths
        assert "interactions[0].response.body.string" in keys

        # Get the response body
        body = parser.get_value_at_path(data, "interactions[0].response.body.string")
        assert isinstance(body, str)
        assert "John Doe" in body

    def test_empty_response_cassette(
        self, parser: YAMLParser, cassettes_dir: Path
    ) -> None:
        """Test handling cassette with empty response body."""
        cassette = cassettes_dir / "empty_response.yaml"

        data = parser.load(cassette)
        keys = parser.get_all_keys(data)

        # Should still extract the structure
        assert "interactions[0].response.body.string" in keys

        # Body should be empty string
        body = parser.get_value_at_path(data, "interactions[0].response.body.string")
        assert body == ""

    def test_html_response_cassette(
        self, parser: YAMLParser, cassettes_dir: Path
    ) -> None:
        """Test handling cassette with HTML response."""
        cassette = cassettes_dir / "html_response.yaml"

        data = parser.load(cassette)

        # Get HTML body
        body = parser.get_value_at_path(data, "interactions[0].response.body.string")
        assert "<!DOCTYPE html>" in body
        assert "Hello, World!" in body
