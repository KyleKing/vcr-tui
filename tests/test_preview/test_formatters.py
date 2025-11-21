"""Tests for content formatters."""

from __future__ import annotations

import json

import pytest

from vcr_tui.preview.formatters import FormatterRegistry


class TestFormatterRegistry:
    """Tests for FormatterRegistry class."""

    @pytest.fixture
    def formatter(self) -> FormatterRegistry:
        """Return a FormatterRegistry instance."""
        return FormatterRegistry()

    def test_formatter_initialization(self, formatter: FormatterRegistry) -> None:
        """Test that formatter initializes correctly."""
        assert formatter is not None
        assert formatter.yaml is not None

    def test_format_with_unknown_formatter(self, formatter: FormatterRegistry) -> None:
        """Test that unknown formatter raises ValueError."""
        with pytest.raises(ValueError, match="Unknown formatter"):
            formatter.format("test", "unknown")


class TestJSONFormatter:
    """Tests for JSON formatting."""

    @pytest.fixture
    def formatter(self) -> FormatterRegistry:
        """Return a FormatterRegistry instance."""
        return FormatterRegistry()

    def test_format_json_from_string(self, formatter: FormatterRegistry) -> None:
        """Test formatting JSON from string."""
        json_string = '{"name":"John","age":30}'
        result = formatter.format_json(json_string)

        # Should be pretty-printed
        assert '"name"' in result
        assert '"John"' in result
        # Should have indentation
        assert "  " in result or "\n" in result

    def test_format_json_from_object(self, formatter: FormatterRegistry) -> None:
        """Test formatting JSON from Python object."""
        data = {"name": "John", "age": 30, "items": [1, 2, 3]}
        result = formatter.format_json(data)

        # Should be pretty-printed
        assert '"name"' in result
        assert '"John"' in result
        # Should be parseable
        reparsed = json.loads(result)
        assert reparsed == data

    def test_format_json_invalid_string(self, formatter: FormatterRegistry) -> None:
        """Test formatting invalid JSON string returns as-is."""
        invalid = "not valid json"
        result = formatter.format_json(invalid)

        assert result == invalid

    @pytest.mark.parametrize(
        ("data", "expected_keys"),
        [
            ({"key": "value"}, ["key", "value"]),
            ({"user": {"name": "John"}}, ["user", "name", "John"]),
            ([1, 2, 3], ["1", "2", "3"]),
            ({"unicode": "café ☕"}, ["café", "☕"]),
        ],
    )
    def test_format_json_various_types(
        self,
        formatter: FormatterRegistry,
        data: object,
        expected_keys: list[str],
    ) -> None:
        """Test formatting various JSON data types."""
        result = formatter.format_json(data)

        for key in expected_keys:
            assert key in result

    def test_format_json_preserves_unicode(self, formatter: FormatterRegistry) -> None:
        """Test that JSON formatting preserves Unicode characters."""
        data = {"text": "Hello 世界 🌍"}
        result = formatter.format_json(data)

        assert "世界" in result
        assert "🌍" in result

    def test_format_json_with_format_method(self, formatter: FormatterRegistry) -> None:
        """Test JSON formatting through main format() method."""
        data = {"name": "Test"}
        result = formatter.format(data, "json")

        assert '"name"' in result
        assert '"Test"' in result


class TestYAMLFormatter:
    """Tests for YAML formatting."""

    @pytest.fixture
    def formatter(self) -> FormatterRegistry:
        """Return a FormatterRegistry instance."""
        return FormatterRegistry()

    def test_format_yaml_from_dict(self, formatter: FormatterRegistry) -> None:
        """Test formatting YAML from dictionary."""
        data = {"name": "John", "age": 30}
        result = formatter.format_yaml(data)

        assert "name:" in result
        assert "John" in result
        assert "age:" in result
        assert "30" in result

    def test_format_yaml_from_list(self, formatter: FormatterRegistry) -> None:
        """Test formatting YAML from list."""
        data = [{"id": 1}, {"id": 2}]
        result = formatter.format_yaml(data)

        assert "- id: 1" in result or "id: 1" in result

    def test_format_yaml_nested_structure(self, formatter: FormatterRegistry) -> None:
        """Test formatting nested YAML structure."""
        data = {"user": {"name": "John", "contact": {"email": "john@example.com"}}}
        result = formatter.format_yaml(data)

        assert "user:" in result
        assert "name:" in result
        assert "contact:" in result
        assert "email:" in result

    def test_format_yaml_from_string(self, formatter: FormatterRegistry) -> None:
        """Test formatting YAML from string."""
        yaml_string = "name: John\nage: 30"
        result = formatter.format_yaml(yaml_string)

        # Should parse and reformat
        assert "name:" in result
        assert "John" in result

    def test_format_yaml_invalid_string(self, formatter: FormatterRegistry) -> None:
        """Test formatting invalid YAML string returns as-is."""
        invalid = "not: valid: yaml: content:"
        result = formatter.format_yaml(invalid)

        # Should return as-is when can't parse
        assert invalid in result

    def test_format_yaml_with_format_method(self, formatter: FormatterRegistry) -> None:
        """Test YAML formatting through main format() method."""
        data = {"name": "Test"}
        result = formatter.format(data, "yaml")

        assert "name:" in result
        assert "Test" in result


class TestTextFormatter:
    """Tests for text formatting."""

    @pytest.fixture
    def formatter(self) -> FormatterRegistry:
        """Return a FormatterRegistry instance."""
        return FormatterRegistry()

    @pytest.mark.parametrize(
        ("input_text", "expected_output"),
        [
            ("hello\\nworld", "hello\nworld"),
            ("tab\\there", "tab\there"),
            ("quote\\'test", "quote'test"),
            ('double\\"quote', 'double"quote'),
            ("backslash\\\\test", "backslash\\test"),
        ],
    )
    def test_format_text_escape_sequences(
        self,
        formatter: FormatterRegistry,
        input_text: str,
        expected_output: str,
    ) -> None:
        """Test formatting text with various escape sequences."""
        result = formatter.format_text(input_text)
        assert result == expected_output

    def test_format_text_no_escapes(self, formatter: FormatterRegistry) -> None:
        """Test formatting plain text without escapes."""
        text = "Hello, World!"
        result = formatter.format_text(text)

        assert result == text

    def test_format_text_non_string(self, formatter: FormatterRegistry) -> None:
        """Test formatting non-string converts to string."""
        result = formatter.format_text(123)
        assert result == "123"

    def test_format_text_with_format_method(self, formatter: FormatterRegistry) -> None:
        """Test text formatting through main format() method."""
        text = "hello\\nworld"
        result = formatter.format(text, "text")

        assert "\n" in result


class TestHTMLFormatter:
    """Tests for HTML formatting."""

    @pytest.fixture
    def formatter(self) -> FormatterRegistry:
        """Return a FormatterRegistry instance."""
        return FormatterRegistry()

    @pytest.mark.parametrize(
        ("input_html", "expected_char"),
        [
            ("&lt;div&gt;", "<div>"),
            ("&amp;", "&"),
            ("&quot;test&quot;", '"test"'),
            ("&#39;", "'"),
            ("&nbsp;", "\xa0"),  # Non-breaking space
        ],
    )
    def test_format_html_entities(
        self,
        formatter: FormatterRegistry,
        input_html: str,
        expected_char: str,
    ) -> None:
        """Test formatting HTML with various entities."""
        result = formatter.format_html(input_html)
        assert expected_char in result

    def test_format_html_complex_document(self, formatter: FormatterRegistry) -> None:
        """Test formatting complex HTML document."""
        html_content = "&lt;html&gt;&lt;body&gt;&lt;h1&gt;Title&lt;/h1&gt;&lt;/body&gt;&lt;/html&gt;"
        result = formatter.format_html(html_content)

        assert "<html>" in result
        assert "<body>" in result
        assert "<h1>" in result

    def test_format_html_non_string(self, formatter: FormatterRegistry) -> None:
        """Test formatting non-string HTML."""
        result = formatter.format_html(123)
        assert result == "123"

    def test_format_html_with_format_method(self, formatter: FormatterRegistry) -> None:
        """Test HTML formatting through main format() method."""
        html_content = "&lt;div&gt;test&lt;/div&gt;"
        result = formatter.format(html_content, "html")

        assert "<div>" in result


class TestTOMLFormatter:
    """Tests for TOML formatting."""

    @pytest.fixture
    def formatter(self) -> FormatterRegistry:
        """Return a FormatterRegistry instance."""
        return FormatterRegistry()

    def test_format_toml_from_string(self, formatter: FormatterRegistry) -> None:
        """Test formatting TOML from string."""
        toml_string = "[section]\nkey = 'value'"
        result = formatter.format_toml(toml_string)

        assert toml_string in result

    def test_format_toml_from_dict(self, formatter: FormatterRegistry) -> None:
        """Test formatting TOML from dictionary."""
        data = {"name": "test", "value": 123}
        result = formatter.format_toml(data)

        # Currently uses JSON formatting as fallback
        assert "name" in result
        assert "test" in result

    def test_format_toml_with_format_method(self, formatter: FormatterRegistry) -> None:
        """Test TOML formatting through main format() method."""
        data = {"key": "value"}
        result = formatter.format(data, "toml")

        assert "key" in result


class TestAutoDetectFormat:
    """Tests for auto-detect formatting."""

    @pytest.fixture
    def formatter(self) -> FormatterRegistry:
        """Return a FormatterRegistry instance."""
        return FormatterRegistry()

    def test_auto_detect_json(self, formatter: FormatterRegistry) -> None:
        """Test auto-detecting JSON content."""
        json_content = '{"name": "John", "age": 30}'
        result = formatter.auto_detect_format(json_content)

        # Should be formatted as JSON with indentation
        assert '"name"' in result
        assert "\n" in result or "  " in result

    @pytest.mark.parametrize(
        "html_start",
        [
            "<!DOCTYPE html>",
            "<html>",
            "<HTML>",
            "<!doctype HTML>",
        ],
    )
    def test_auto_detect_html(
        self, formatter: FormatterRegistry, html_start: str
    ) -> None:
        """Test auto-detecting HTML content."""
        html_content = f"{html_start}<body>test</body>"
        result = formatter.auto_detect_format(html_content)

        # Should recognize as HTML
        assert "body" in result

    def test_auto_detect_yaml(self, formatter: FormatterRegistry) -> None:
        """Test auto-detecting YAML content."""
        yaml_content = "name: John\nage: 30\nactive: true"
        result = formatter.auto_detect_format(yaml_content)

        # Should format as YAML
        assert "name:" in result or "John" in result

    def test_auto_detect_plain_text(self, formatter: FormatterRegistry) -> None:
        """Test auto-detecting plain text."""
        text_content = "Just some plain text\\nwith newlines"
        result = formatter.auto_detect_format(text_content)

        # Should fall back to text formatting
        assert "\n" in result  # Escape sequence should be converted

    def test_auto_detect_non_string(self, formatter: FormatterRegistry) -> None:
        """Test auto-detect with non-string input."""
        result = formatter.auto_detect_format(123)  # type: ignore[arg-type]
        assert result == "123"


class TestIntegration:
    """Integration tests with real VCR data."""

    @pytest.fixture
    def formatter(self) -> FormatterRegistry:
        """Return a FormatterRegistry instance."""
        return FormatterRegistry()

    def test_format_vcr_response_body_json(self, formatter: FormatterRegistry) -> None:
        """Test formatting VCR response body as JSON."""
        # Typical VCR response body (JSON as escaped string)
        body = '{"id": 123, "name": "John Doe", "email": "john@example.com"}'

        result = formatter.format_json(body)

        # Should be pretty-printed
        assert '"id"' in result
        assert '"name"' in result
        assert "John Doe" in result
        # Should have indentation
        assert "\n" in result

    def test_format_vcr_response_body_html(self, formatter: FormatterRegistry) -> None:
        """Test formatting VCR response body as HTML."""
        body = "&lt;!DOCTYPE html&gt;\\n&lt;html&gt;\\n&lt;head&gt;\\n    &lt;title&gt;Example&lt;/title&gt;\\n&lt;/head&gt;"

        # First apply text formatting to handle \\n
        text_formatted = formatter.format_text(body)
        # Then apply HTML formatting
        result = formatter.format_html(text_formatted)

        assert "<!DOCTYPE html>" in result
        assert "<title>" in result

    def test_auto_format_vcr_json_response(self, formatter: FormatterRegistry) -> None:
        """Test auto-formatting typical VCR JSON response."""
        body = '{"id": 124, "name": "Jane Smith"}'

        result = formatter.auto_detect_format(body)

        # Should auto-detect as JSON and format
        parsed = json.loads(result)
        assert parsed["name"] == "Jane Smith"

    def test_format_empty_response(self, formatter: FormatterRegistry) -> None:
        """Test formatting empty response body."""
        body = ""

        result = formatter.format_text(body)
        assert result == ""

        result = formatter.auto_detect_format(body)
        assert result == ""
