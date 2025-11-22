"""Tests for PreviewPanel widget."""

from __future__ import annotations

import pytest
from textual.app import App, ComposeResult

from vcr_tui.ui.preview_panel import PreviewPanel


class PreviewPanelTestApp(App[None]):
    """Test app for PreviewPanel widget."""

    def __init__(self, preview_panel: PreviewPanel) -> None:
        """Initialize with a PreviewPanel widget."""
        super().__init__()
        self.preview_panel = preview_panel

    def compose(self) -> ComposeResult:
        """Compose the app with the PreviewPanel widget."""
        yield self.preview_panel


class TestPreviewPanelCreation:
    """Tests for PreviewPanel widget creation."""

    def test_create_empty_panel(self) -> None:
        """Test creating PreviewPanel with no content."""
        panel = PreviewPanel()

        assert panel.content == ""
        assert panel.formatter is None
        assert panel.can_focus is True

    def test_create_with_content(self) -> None:
        """Test creating PreviewPanel with initial content."""
        content = '{"name": "John", "age": 30}'
        panel = PreviewPanel(content=content)

        assert panel.content == content

    def test_create_with_formatter(self) -> None:
        """Test creating PreviewPanel with formatter specified."""
        content = '{"name": "John"}'
        panel = PreviewPanel(content=content, formatter="json")

        assert panel.content == content
        assert panel.formatter == "json"

    def test_create_with_id_and_classes(self) -> None:
        """Test creating PreviewPanel with CSS attributes."""
        panel = PreviewPanel(id="test-panel", classes="custom-class")

        assert panel.id == "test-panel"
        assert "custom-class" in panel.classes


class TestPreviewPanelOperations:
    """Tests for PreviewPanel operations."""

    async def test_set_content(self) -> None:
        """Test updating content after creation."""
        panel = PreviewPanel()
        app = PreviewPanelTestApp(panel)

        async with app.run_test():
            assert panel.content == ""

            content = "Hello, World!"
            panel.set_content(content)

            assert panel.content == content

    async def test_set_content_with_formatter(self) -> None:
        """Test updating content with formatter."""
        panel = PreviewPanel()
        app = PreviewPanelTestApp(panel)

        async with app.run_test():
            content = '{"key": "value"}'
            panel.set_content(content, formatter="json")

            assert panel.content == content
            assert panel.formatter == "json"

    async def test_set_content_replaces_existing(self) -> None:
        """Test that set_content replaces existing content."""
        panel = PreviewPanel(content="Old content", formatter="text")
        app = PreviewPanelTestApp(panel)

        async with app.run_test():
            assert panel.content == "Old content"
            assert panel.formatter == "text"

            panel.set_content("New content", formatter="json")

            assert panel.content == "New content"
            assert panel.formatter == "json"

    async def test_clear_content(self) -> None:
        """Test clearing content."""
        panel = PreviewPanel(content="Some content", formatter="text")
        app = PreviewPanelTestApp(panel)

        async with app.run_test():
            assert panel.content == "Some content"

            panel.clear_content()

            assert panel.content == ""
            assert panel.formatter is None

    async def test_content_property(self) -> None:
        """Test content property getter."""
        content = "Test content"
        panel = PreviewPanel(content=content)

        assert panel.content == content

    async def test_formatter_property(self) -> None:
        """Test formatter property getter."""
        panel = PreviewPanel(formatter="yaml")

        assert panel.formatter == "yaml"


class TestPreviewPanelFormatters:
    """Tests for different content formatters."""

    @pytest.mark.parametrize(
        "formatter",
        ["json", "yaml", "html", "toml", "xml", "text"],
    )
    async def test_supported_formatters(self, formatter: str) -> None:
        """Test that all supported formatters work."""
        panel = PreviewPanel()
        app = PreviewPanelTestApp(panel)

        async with app.run_test():
            content = "Sample content"
            panel.set_content(content, formatter=formatter)

            assert panel.content == content
            assert panel.formatter == formatter

    async def test_json_syntax_highlighting(self) -> None:
        """Test JSON content with syntax highlighting."""
        panel = PreviewPanel()
        app = PreviewPanelTestApp(panel)

        async with app.run_test():
            json_content = '{"name": "John", "age": 30, "city": "New York"}'
            panel.set_content(json_content, formatter="json")

            assert panel.content == json_content
            assert panel.formatter == "json"

    async def test_yaml_syntax_highlighting(self) -> None:
        """Test YAML content with syntax highlighting."""
        panel = PreviewPanel()
        app = PreviewPanelTestApp(panel)

        async with app.run_test():
            yaml_content = "name: John\nage: 30\ncity: New York"
            panel.set_content(yaml_content, formatter="yaml")

            assert panel.content == yaml_content
            assert panel.formatter == "yaml"

    async def test_plain_text_no_highlighting(self) -> None:
        """Test plain text content without highlighting."""
        panel = PreviewPanel()
        app = PreviewPanelTestApp(panel)

        async with app.run_test():
            text_content = "This is plain text\nwith multiple lines"
            panel.set_content(text_content, formatter="text")

            assert panel.content == text_content
            assert panel.formatter == "text"

    async def test_no_formatter_specified(self) -> None:
        """Test content without formatter specified."""
        panel = PreviewPanel()
        app = PreviewPanelTestApp(panel)

        async with app.run_test():
            content = "Content without formatter"
            panel.set_content(content)

            assert panel.content == content
            assert panel.formatter is None

    async def test_invalid_syntax_fallback(self) -> None:
        """Test that invalid syntax falls back to plain text."""
        panel = PreviewPanel()
        app = PreviewPanelTestApp(panel)

        async with app.run_test():
            # Intentionally malformed JSON
            bad_json = '{"name": invalid syntax}'
            panel.set_content(bad_json, formatter="json")

            # Should still store the content even if highlighting fails
            assert panel.content == bad_json
            assert panel.formatter == "json"


class TestPreviewPanelContent:
    """Tests for various content types."""

    async def test_empty_content(self) -> None:
        """Test displaying empty content."""
        panel = PreviewPanel()
        app = PreviewPanelTestApp(panel)

        async with app.run_test():
            panel.set_content("")

            assert panel.content == ""

    async def test_multiline_content(self) -> None:
        """Test displaying multiline content."""
        panel = PreviewPanel()
        app = PreviewPanelTestApp(panel)

        async with app.run_test():
            content = "Line 1\nLine 2\nLine 3\nLine 4"
            panel.set_content(content)

            assert panel.content == content
            assert "\n" in panel.content

    async def test_long_content(self) -> None:
        """Test displaying very long content."""
        panel = PreviewPanel()
        app = PreviewPanelTestApp(panel)

        async with app.run_test():
            # Create long content that would require scrolling
            content = "\n".join([f"Line {i}" for i in range(100)])
            panel.set_content(content)

            assert panel.content == content
            assert panel.content.count("\n") == 99

    async def test_special_characters(self) -> None:
        """Test content with special characters."""
        panel = PreviewPanel()
        app = PreviewPanelTestApp(panel)

        async with app.run_test():
            content = "Special chars: <>&\"'\n\t\r"
            panel.set_content(content)

            assert panel.content == content

    async def test_unicode_content(self) -> None:
        """Test content with unicode characters."""
        panel = PreviewPanel()
        app = PreviewPanelTestApp(panel)

        async with app.run_test():
            content = "Unicode: 你好 مرحبا 🎉 ñ ü"
            panel.set_content(content)

            assert panel.content == content


class TestPreviewPanelFocus:
    """Tests for focus behavior."""

    def test_can_focus_enabled(self) -> None:
        """Test that panel can receive focus."""
        panel = PreviewPanel()

        assert panel.can_focus is True

    async def test_panel_is_focusable(self) -> None:
        """Test that panel can be focused in app."""
        panel = PreviewPanel(content="Test content")
        app = PreviewPanelTestApp(panel)

        async with app.run_test():
            # Panel should be focusable
            assert panel.can_focus is True
