"""YAML parsing and key extraction for preview engine."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ruamel.yaml import YAML


class YAMLParser:
    """Parse YAML files and extract key paths.

    This parser extracts all keys from a YAML file in a flat, unwrapped format
    suitable for navigation in a TUI. For example:
    - Simple keys: "name", "email"
    - Nested keys: "user.name", "config.database.host"
    - Array indices: "items[0].id", "users[1].email"
    """

    def __init__(self) -> None:
        """Initialize YAML parser with ruamel.yaml."""
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.default_flow_style = False

    def load(self, file_path: Path) -> Any:
        """Load YAML file and return parsed data.

        Args:
            file_path: Path to YAML file

        Returns:
            Parsed YAML data structure

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If YAML is invalid
        """
        if not file_path.exists():
            raise FileNotFoundError(f"YAML file not found: {file_path}")

        try:
            with open(file_path, encoding="utf-8") as f:
                return self.yaml.load(f)
        except Exception as e:
            raise ValueError(f"Invalid YAML in {file_path}: {e}") from e

    def get_all_keys(self, data: Any, prefix: str = "") -> list[str]:
        """Recursively extract all key paths from data.

        Converts nested YAML structures into flat key paths suitable for
        navigation. Arrays are represented with bracket notation.

        Args:
            data: YAML data structure to extract keys from
            prefix: Current key path prefix (used in recursion)

        Returns:
            List of key paths in unwrapped format

        Examples:
            >>> parser = YAMLParser()
            >>> data = {"user": {"name": "John", "age": 30}}
            >>> parser.get_all_keys(data)
            ['user', 'user.name', 'user.age']

            >>> data = {"items": [{"id": 1}, {"id": 2}]}
            >>> parser.get_all_keys(data)
            ['items', 'items[0]', 'items[0].id', 'items[1]', 'items[1].id']
        """
        keys: list[str] = []

        if isinstance(data, dict):
            for key, value in data.items():
                # Create the full path for this key
                if prefix:
                    full_key = f"{prefix}.{key}"
                else:
                    full_key = str(key)

                keys.append(full_key)

                # Recursively process nested structures
                if isinstance(value, (dict, list)):
                    keys.extend(self.get_all_keys(value, full_key))

        elif isinstance(data, list):
            for index, item in enumerate(data):
                # Create array index notation
                full_key = f"{prefix}[{index}]"
                keys.append(full_key)

                # Recursively process array items
                if isinstance(item, (dict, list)):
                    keys.extend(self.get_all_keys(item, full_key))

        return keys

    def get_value_at_path(self, data: Any, path: str) -> Any:
        """Get value at a specific key path.

        Navigates through nested structures using dot notation and array indices.

        Args:
            data: YAML data structure
            path: Key path (e.g., "user.name", "items[0].id")

        Returns:
            Value at the specified path

        Raises:
            KeyError: If path doesn't exist in data
            IndexError: If array index is out of range
            ValueError: If path syntax is invalid

        Examples:
            >>> parser = YAMLParser()
            >>> data = {"user": {"name": "John"}}
            >>> parser.get_value_at_path(data, "user.name")
            'John'

            >>> data = {"items": [{"id": 1}, {"id": 2}]}
            >>> parser.get_value_at_path(data, "items[1].id")
            2
        """
        if not path:
            return data

        current = data
        parts = self._parse_path(path)

        for part in parts:
            if isinstance(part, int):
                # Array index
                if not isinstance(current, list):
                    raise KeyError(f"Expected list at path, got {type(current).__name__}")
                if part >= len(current) or part < 0:
                    raise IndexError(f"Index {part} out of range")
                current = current[part]
            else:
                # Dictionary key
                if not isinstance(current, dict):
                    raise KeyError(f"Expected dict at path, got {type(current).__name__}")
                if part not in current:
                    raise KeyError(f"Key '{part}' not found")
                current = current[part]

        return current

    def _parse_path(self, path: str) -> list[str | int]:
        """Parse a key path into components.

        Args:
            path: Key path string (e.g., "user.name", "items[0].id")

        Returns:
            List of path components (strings for keys, ints for indices)

        Examples:
            >>> parser = YAMLParser()
            >>> parser._parse_path("user.name")
            ['user', 'name']

            >>> parser._parse_path("items[0].id")
            ['items', 0, 'id']
        """
        parts: list[str | int] = []
        current = ""

        i = 0
        while i < len(path):
            char = path[i]

            if char == ".":
                # End of a key component
                if current:
                    parts.append(current)
                    current = ""
                i += 1
            elif char == "[":
                # Start of array index
                if current:
                    parts.append(current)
                    current = ""

                # Find closing bracket
                end = path.find("]", i)
                if end == -1:
                    raise ValueError(f"Unclosed bracket in path: {path}")

                # Extract index
                index_str = path[i + 1 : end]
                try:
                    parts.append(int(index_str))
                except ValueError as e:
                    raise ValueError(f"Invalid array index '{index_str}' in path: {path}") from e

                i = end + 1
            else:
                current += char
                i += 1

        # Add final component
        if current:
            parts.append(current)

        return parts
