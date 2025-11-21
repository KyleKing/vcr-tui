"""Content formatters for displaying extracted data."""

from __future__ import annotations

import html
import json
from io import StringIO
from typing import Any

from ruamel.yaml import YAML


class FormatterRegistry:
    """Registry of content formatters for different output types.

    Supports formatting extracted content for display:
    - json: Pretty-print JSON with indentation
    - yaml: Format YAML with proper indentation
    - text: Convert escape sequences to actual characters
    - html: Basic HTML formatting
    - toml: Format TOML structures
    """

    def __init__(self) -> None:
        """Initialize formatter registry."""
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.default_flow_style = False

    def format(self, content: Any, formatter_name: str) -> str:
        """Format content using specified formatter.

        Args:
            content: Content to format (can be string, dict, list, etc.)
            formatter_name: Name of formatter to use

        Returns:
            Formatted string ready for display

        Raises:
            ValueError: If formatter_name is not recognized
        """
        if formatter_name == "json":
            return self.format_json(content)
        elif formatter_name == "yaml":
            return self.format_yaml(content)
        elif formatter_name == "text":
            return self.format_text(content)
        elif formatter_name == "html":
            return self.format_html(content)
        elif formatter_name == "toml":
            return self.format_toml(content)
        else:
            raise ValueError(f"Unknown formatter: {formatter_name}")

    def format_json(self, content: Any) -> str:
        """Format content as pretty-printed JSON.

        Handles both JSON strings that need parsing and already-parsed objects.

        Args:
            content: Content to format (string or object)

        Returns:
            Pretty-printed JSON string
        """
        # If content is a string, try to parse it as JSON first
        if isinstance(content, str):
            try:
                parsed = json.loads(content)
                return json.dumps(parsed, indent=2, ensure_ascii=False)
            except json.JSONDecodeError:
                # Not valid JSON, format as-is
                return content

        # Content is already a Python object
        return json.dumps(content, indent=2, ensure_ascii=False)

    def format_yaml(self, content: Any) -> str:
        """Format content as YAML.

        Args:
            content: Content to format (string or object)

        Returns:
            Formatted YAML string
        """
        # If content is a string, try to load it first
        if isinstance(content, str):
            try:
                from ruamel.yaml import YAML

                yaml_parser = YAML()
                parsed = yaml_parser.load(content)
                content = parsed
            except Exception:
                # Not valid YAML, format as-is
                return content

        # Format as YAML
        stream = StringIO()
        self.yaml.dump(content, stream)
        return stream.getvalue()

    def format_text(self, content: Any) -> str:
        """Format text content, converting escape sequences.

        Converts common escape sequences like \\n, \\t, \\r to actual characters.

        Args:
            content: Text content to format

        Returns:
            Text with escape sequences converted
        """
        if not isinstance(content, str):
            content = str(content)

        # Convert escape sequences
        # Use 'unicode_escape' codec to handle escaped characters
        result = content.encode().decode("unicode_escape")

        return result

    def format_html(self, content: Any) -> str:
        """Format HTML content.

        Currently performs basic HTML unescaping. Could be extended
        with pretty-printing in the future.

        Args:
            content: HTML content to format

        Returns:
            Formatted HTML string
        """
        if not isinstance(content, str):
            content = str(content)

        # Unescape HTML entities
        return html.unescape(content)

    def format_toml(self, content: Any) -> str:
        """Format TOML content.

        Args:
            content: TOML content to format

        Returns:
            Formatted TOML string
        """
        if isinstance(content, str):
            # Already a string, return as-is
            return content

        # For dict/object, would need toml library to serialize
        # For now, use JSON-like formatting
        return json.dumps(content, indent=2, ensure_ascii=False)

    def auto_detect_format(self, content: str) -> str:
        """Auto-detect content format and apply appropriate formatter.

        Tries to detect if content is JSON, YAML, HTML, etc. and formats accordingly.

        Args:
            content: Content string to analyze and format

        Returns:
            Formatted content string
        """
        if not isinstance(content, str):
            return str(content)

        # Try JSON first (most common for APIs)
        try:
            parsed = json.loads(content)
            return self.format_json(parsed)
        except (json.JSONDecodeError, ValueError):
            pass

        # Check for HTML
        if content.strip().startswith(("<html", "<!DOCTYPE", "<HTML")):
            return self.format_html(content)

        # Try YAML
        try:
            from ruamel.yaml import YAML

            yaml_parser = YAML()
            parsed = yaml_parser.load(content)
            if parsed is not None:
                return self.format_yaml(parsed)
        except Exception:
            pass

        # Default to text formatting
        return self.format_text(content)
