"""Tests for value extractors."""

from __future__ import annotations

import pytest

from vcr_tui.preview.extractors import ExtractorRegistry


class TestExtractorRegistry:
    """Tests for ExtractorRegistry class."""

    @pytest.fixture
    def extractor(self) -> ExtractorRegistry:
        """Return an ExtractorRegistry instance."""
        return ExtractorRegistry()

    def test_extractor_initialization(self, extractor: ExtractorRegistry) -> None:
        """Test that extractor initializes correctly."""
        assert extractor is not None
        assert extractor.parser is not None


class TestSimpleExtraction:
    """Tests for simple path extraction (no iteration)."""

    @pytest.fixture
    def extractor(self) -> ExtractorRegistry:
        """Return an ExtractorRegistry instance."""
        return ExtractorRegistry()

    @pytest.mark.parametrize(
        ("data", "path", "expected"),
        [
            ({"name": "John"}, "name", ["John"]),
            ({"name": "John"}, ".name", ["John"]),
            ({"user": {"name": "John"}}, "user.name", ["John"]),
            ({"user": {"name": "John"}}, ".user.name", ["John"]),
            ({"user": {"contact": {"email": "j@example.com"}}}, "user.contact.email", ["j@example.com"]),
            ({"items": [{"id": 1}]}, "items[0].id", [1]),
            ({"data": {"items": [{"id": 1}]}}, "data.items[0].id", [1]),
        ],
    )
    def test_extract_simple_paths(
        self,
        extractor: ExtractorRegistry,
        data: dict,
        path: str,
        expected: list[object],
    ) -> None:
        """Test extracting values from simple paths."""
        result = extractor.extract(data, path)
        assert result == expected

    def test_extract_nonexistent_path(self, extractor: ExtractorRegistry) -> None:
        """Test extracting from non-existent path returns empty list."""
        data = {"name": "John"}
        result = extractor.extract(data, "nonexistent")
        assert result == []

    def test_extract_invalid_index(self, extractor: ExtractorRegistry) -> None:
        """Test extracting with out-of-range index returns empty list."""
        data = {"items": [{"id": 1}]}
        result = extractor.extract(data, "items[10].id")
        assert result == []

    def test_extract_nested_object(self, extractor: ExtractorRegistry) -> None:
        """Test extracting nested object returns the whole object."""
        data = {"user": {"name": "John", "age": 30}}
        result = extractor.extract(data, "user")
        assert result == [{"name": "John", "age": 30}]


class TestArrayIteration:
    """Tests for array iteration extraction."""

    @pytest.fixture
    def extractor(self) -> ExtractorRegistry:
        """Return an ExtractorRegistry instance."""
        return ExtractorRegistry()

    def test_extract_simple_array_iteration(self, extractor: ExtractorRegistry) -> None:
        """Test iterating over array and extracting values."""
        data = {"items": [{"id": 1}, {"id": 2}, {"id": 3}]}
        result = extractor.extract(data, "items[].id")
        assert result == [1, 2, 3]

    def test_extract_array_iteration_with_leading_dot(
        self, extractor: ExtractorRegistry
    ) -> None:
        """Test array iteration with leading dot in path."""
        data = {"items": [{"id": 1}, {"id": 2}]}
        result = extractor.extract(data, ".items[].id")
        assert result == [1, 2]

    def test_extract_nested_array_iteration(self, extractor: ExtractorRegistry) -> None:
        """Test iterating over nested array."""
        data = {"data": {"items": [{"id": 1}, {"id": 2}]}}
        result = extractor.extract(data, "data.items[].id")
        assert result == [1, 2]

    def test_extract_array_items_without_subpath(
        self, extractor: ExtractorRegistry
    ) -> None:
        """Test iterating array without additional path returns items."""
        data = {"items": [{"id": 1}, {"id": 2}]}
        result = extractor.extract(data, "items[]")
        assert result == [{"id": 1}, {"id": 2}]

    def test_extract_nested_array_iteration_multiple_levels(
        self, extractor: ExtractorRegistry
    ) -> None:
        """Test nested array iteration (arrays within arrays)."""
        data = {"users": [{"tags": ["admin", "user"]}, {"tags": ["guest"]}]}
        result = extractor.extract(data, "users[].tags[]")
        assert result == ["admin", "user", "guest"]

    def test_extract_array_iteration_missing_field(
        self, extractor: ExtractorRegistry
    ) -> None:
        """Test array iteration skips items missing the field."""
        data = {"items": [{"id": 1, "name": "A"}, {"id": 2}, {"id": 3, "name": "C"}]}
        result = extractor.extract(data, "items[].name")
        assert result == ["A", "C"]

    def test_extract_empty_array(self, extractor: ExtractorRegistry) -> None:
        """Test extracting from empty array returns empty list."""
        data = {"items": []}
        result = extractor.extract(data, "items[].id")
        assert result == []

    def test_extract_non_array_with_iteration_marker(
        self, extractor: ExtractorRegistry
    ) -> None:
        """Test array iteration on non-array returns empty list."""
        data = {"item": {"id": 1}}
        result = extractor.extract(data, "item[].id")
        assert result == []

    def test_extract_complex_nested_structure(
        self, extractor: ExtractorRegistry
    ) -> None:
        """Test extraction from complex nested structure."""
        data = {
            "http_interactions": [
                {
                    "request": {"method": "GET", "uri": "https://api.example.com/1"},
                    "response": {"status": {"code": 200}, "body": {"string": "response1"}},
                },
                {
                    "request": {"method": "POST", "uri": "https://api.example.com/2"},
                    "response": {"status": {"code": 201}, "body": {"string": "response2"}},
                },
            ]
        }

        # Extract all response bodies
        result = extractor.extract(data, "http_interactions[].response.body.string")
        assert result == ["response1", "response2"]

        # Extract all request methods
        result = extractor.extract(data, "http_interactions[].request.method")
        assert result == ["GET", "POST"]

        # Extract all status codes
        result = extractor.extract(data, "http_interactions[].response.status.code")
        assert result == [200, 201]


class TestMatchesPath:
    """Tests for matches_path method."""

    @pytest.fixture
    def extractor(self) -> ExtractorRegistry:
        """Return an ExtractorRegistry instance."""
        return ExtractorRegistry()

    @pytest.mark.parametrize(
        ("available_path", "extraction_path", "expected"),
        [
            # Exact matches
            ("name", "name", True),
            ("user.name", "user.name", True),
            # Leading dot shouldn't matter
            ("name", ".name", True),
            (".name", "name", True),
            # Array iteration matching
            ("items[0].id", "items[].id", True),
            ("items[1].id", "items[].id", True),
            ("items[99].id", "items[].id", True),
            ("items[0].id", ".items[].id", True),
            # Nested arrays
            ("data.items[0].tags[0]", "data.items[].tags[]", True),
            ("data.items[1].tags[2]", "data.items[].tags[]", True),
            # Non-matches
            ("name", "email", False),
            ("user.name", "user.email", False),
            ("items[0].id", "items[].name", False),
            ("users[0].id", "items[].id", False),
            # Partial matches shouldn't work
            ("user.name.first", "user.name", False),
            ("items[0]", "items[].id", False),
        ],
    )
    def test_matches_path(
        self,
        extractor: ExtractorRegistry,
        available_path: str,
        extraction_path: str,
        expected: bool,
    ) -> None:
        """Test path matching with various patterns."""
        result = extractor.matches_path(available_path, extraction_path)
        assert result == expected


class TestFindMatchingPaths:
    """Tests for find_matching_paths method."""

    @pytest.fixture
    def extractor(self) -> ExtractorRegistry:
        """Return an ExtractorRegistry instance."""
        return ExtractorRegistry()

    def test_find_matching_simple_paths(self, extractor: ExtractorRegistry) -> None:
        """Test finding exact path matches."""
        available = ["user.name", "user.email", "user.age"]
        result = extractor.find_matching_paths(available, "user.name")
        assert result == ["user.name"]

    def test_find_matching_array_paths(self, extractor: ExtractorRegistry) -> None:
        """Test finding paths matching array iteration pattern."""
        available = [
            "items[0].id",
            "items[0].name",
            "items[1].id",
            "items[1].name",
            "user.name",
        ]
        result = extractor.find_matching_paths(available, "items[].id")
        assert result == ["items[0].id", "items[1].id"]

    def test_find_matching_nested_arrays(self, extractor: ExtractorRegistry) -> None:
        """Test finding paths with nested array patterns."""
        available = [
            "data.items[0].tags[0]",
            "data.items[0].tags[1]",
            "data.items[1].tags[0]",
            "data.other",
        ]
        result = extractor.find_matching_paths(available, "data.items[].tags[]")
        assert result == [
            "data.items[0].tags[0]",
            "data.items[0].tags[1]",
            "data.items[1].tags[0]",
        ]

    def test_find_matching_no_matches(self, extractor: ExtractorRegistry) -> None:
        """Test finding paths when no matches exist."""
        available = ["user.name", "user.email"]
        result = extractor.find_matching_paths(available, "items[].id")
        assert result == []

    def test_find_matching_empty_available(self, extractor: ExtractorRegistry) -> None:
        """Test finding paths with empty available list."""
        result = extractor.find_matching_paths([], "user.name")
        assert result == []


class TestIntegration:
    """Integration tests with real VCR cassette data."""

    @pytest.fixture
    def extractor(self) -> ExtractorRegistry:
        """Return an ExtractorRegistry instance."""
        return ExtractorRegistry()

    @pytest.fixture
    def vcr_data(self) -> dict:
        """Return sample VCR cassette data."""
        return {
            "version": 1,
            "http_interactions": [
                {
                    "request": {
                        "method": "GET",
                        "uri": "https://api.example.com/users/123",
                    },
                    "response": {
                        "status": {"code": 200, "message": "OK"},
                        "body": {
                            "string": '{"id": 123, "name": "John", "email": "john@example.com"}'
                        },
                    },
                },
                {
                    "request": {
                        "method": "POST",
                        "uri": "https://api.example.com/users",
                    },
                    "response": {
                        "status": {"code": 201, "message": "Created"},
                        "body": {"string": '{"id": 124, "name": "Jane"}'},
                    },
                },
            ],
        }

    def test_extract_all_response_bodies(
        self, extractor: ExtractorRegistry, vcr_data: dict
    ) -> None:
        """Test extracting all response bodies from VCR cassette."""
        result = extractor.extract(vcr_data, "http_interactions[].response.body.string")
        assert len(result) == 2
        assert "John" in result[0]
        assert "Jane" in result[1]

    def test_extract_all_request_methods(
        self, extractor: ExtractorRegistry, vcr_data: dict
    ) -> None:
        """Test extracting all request methods."""
        result = extractor.extract(vcr_data, "http_interactions[].request.method")
        assert result == ["GET", "POST"]

    def test_extract_all_status_codes(
        self, extractor: ExtractorRegistry, vcr_data: dict
    ) -> None:
        """Test extracting all response status codes."""
        result = extractor.extract(vcr_data, "http_interactions[].response.status.code")
        assert result == [200, 201]

    def test_extract_specific_interaction(
        self, extractor: ExtractorRegistry, vcr_data: dict
    ) -> None:
        """Test extracting from specific interaction by index."""
        result = extractor.extract(vcr_data, "http_interactions[0].request.method")
        assert result == ["GET"]

        result = extractor.extract(vcr_data, "http_interactions[1].request.method")
        assert result == ["POST"]
