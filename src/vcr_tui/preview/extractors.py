"""Value extraction from structured data using path expressions."""

from __future__ import annotations

from typing import Any

from vcr_tui.preview.yaml_parser import YAMLParser


class ExtractorRegistry:
    """Registry for extracting values from data using path expressions.

    Supports extraction rules like:
    - Simple paths: ".body.string"
    - Nested paths: ".response.headers.Content-Type"
    - Array iteration: ".interactions[].response.body"
    - Array indices: ".interactions[0].request.method"
    """

    def __init__(self) -> None:
        """Initialize extractor with YAML parser."""
        self.parser = YAMLParser()

    def extract(self, data: Any, path: str) -> list[Any]:
        """Extract value(s) from data using path expression.

        Supports both specific paths and array iteration patterns.
        If path contains `[]` without an index, it will iterate over all
        array elements and return a list of results.

        Args:
            data: Data structure to extract from
            path: Path expression (e.g., ".body", ".items[].id")

        Returns:
            List of extracted values (single item if specific path,
            multiple items if array iteration is used)

        Examples:
            >>> extractor = ExtractorRegistry()
            >>> data = {"body": {"string": "test"}}
            >>> extractor.extract(data, ".body.string")
            ['test']

            >>> data = {"items": [{"id": 1}, {"id": 2}]}
            >>> extractor.extract(data, ".items[].id")
            [1, 2]
        """
        # Remove leading dot if present
        if path.startswith("."):
            path = path[1:]

        # Check if path contains array iteration marker
        if "[]" in path:
            return self._extract_with_iteration(data, path)

        # Simple path extraction
        try:
            value = self.parser.get_value_at_path(data, path)
            return [value]
        except (KeyError, IndexError, ValueError):
            return []

    def _extract_with_iteration(self, data: Any, path: str) -> list[Any]:
        """Extract values using array iteration pattern.

        Supports paths like:
        - "items[].name" - iterate over items array
        - "data.results[].id" - iterate over nested array
        - "items[].tags[]" - nested array iteration

        Args:
            data: Data structure to extract from
            path: Path with array iteration markers ([])

        Returns:
            List of extracted values from all array elements
        """
        results: list[Any] = []

        # Split path into parts (before [], array, after [])
        parts = path.split("[]")

        if len(parts) < 2:
            # No array iteration marker
            return []

        # Get to the array
        array_path = parts[0]
        remaining_path = "[]".join(parts[1:])

        # Navigate to the array
        try:
            if array_path:
                array_data = self.parser.get_value_at_path(data, array_path)
            else:
                # Path starts with [] (root is array)
                array_data = data
        except (KeyError, IndexError, ValueError):
            return []

        # Verify it's actually an array
        if not isinstance(array_data, list):
            return []

        # Iterate over array elements
        for index, item in enumerate(array_data):
            if remaining_path:
                # There's more path to traverse
                # Remove leading dot if present
                next_path = remaining_path.lstrip(".")

                # Check if there are more iterations needed
                if "[]" in next_path:
                    # Recursive iteration
                    sub_results = self._extract_with_iteration(item, next_path)
                    results.extend(sub_results)
                else:
                    # Simple path extraction
                    try:
                        value = self.parser.get_value_at_path(item, next_path)
                        results.append(value)
                    except (KeyError, IndexError, ValueError):
                        # Skip items that don't have this path
                        continue
            else:
                # No remaining path, return the array items themselves
                results.append(item)

        return results

    def matches_path(self, available_path: str, extraction_path: str) -> bool:
        """Check if an available path matches an extraction rule path.

        Handles matching of specific indices against array iteration patterns.

        Args:
            available_path: Actual path in data (e.g., "items[0].id")
            extraction_path: Extraction rule path (e.g., "items[].id", ".items[].id")

        Returns:
            True if paths match, False otherwise

        Examples:
            >>> extractor = ExtractorRegistry()
            >>> extractor.matches_path("items[0].id", "items[].id")
            True
            >>> extractor.matches_path("items[0].id", ".items[].id")
            True
            >>> extractor.matches_path("users[1].name", "items[].name")
            False
        """
        # Normalize paths (remove leading dot)
        available = available_path.lstrip(".")
        extraction = extraction_path.lstrip(".")

        # If exact match, return True
        if available == extraction:
            return True

        # Replace array iteration markers with regex-like pattern for matching
        # Convert "items[].id" to pattern that matches "items[0].id", "items[1].id", etc.
        import re

        pattern = extraction.replace("[]", r"\[\d+\]")
        pattern = f"^{pattern}$"

        return bool(re.match(pattern, available))

    def find_matching_paths(
        self, available_paths: list[str], extraction_path: str
    ) -> list[str]:
        """Find all available paths that match an extraction rule.

        Args:
            available_paths: List of available paths in the data
            extraction_path: Extraction rule path pattern

        Returns:
            List of matching paths

        Examples:
            >>> extractor = ExtractorRegistry()
            >>> paths = ["items[0].id", "items[1].id", "user.name"]
            >>> extractor.find_matching_paths(paths, "items[].id")
            ['items[0].id', 'items[1].id']
        """
        return [path for path in available_paths if self.matches_path(path, extraction_path)]
