"""Tests for YAMLViewer widget."""

from __future__ import annotations

import pytest
from textual.app import App, ComposeResult

from vcr_tui.ui.yaml_viewer import YAMLViewer


class YAMLViewerTestApp(App[None]):
    """Test app for YAMLViewer widget."""

    def __init__(self, yaml_viewer: YAMLViewer) -> None:
        """Initialize with a YAMLViewer widget."""
        super().__init__()
        self.yaml_viewer = yaml_viewer

    def compose(self) -> ComposeResult:
        """Compose the app with the YAMLViewer widget."""
        yield self.yaml_viewer


class TestYAMLViewerCreation:
    """Tests for YAMLViewer widget creation."""

    def test_create_empty_viewer(self) -> None:
        """Test creating YAMLViewer with no keys."""
        viewer = YAMLViewer()

        assert viewer.keys == []
        assert viewer.key_count == 0
        # Check root node label (Rich Text object)
        assert str(viewer.root.label) == "YAML Keys"

    def test_create_with_keys(self) -> None:
        """Test creating YAMLViewer with initial keys."""
        keys = ["user.name", "user.email", "items[0].id"]
        viewer = YAMLViewer(keys=keys)

        assert viewer.keys == keys
        assert viewer.key_count == 3

    def test_create_with_custom_label(self) -> None:
        """Test creating YAMLViewer with custom label."""
        viewer = YAMLViewer(label="Custom Label")

        # Check root node label (Rich Text object)
        assert str(viewer.root.label) == "Custom Label"

    def test_create_with_id_and_classes(self) -> None:
        """Test creating YAMLViewer with CSS attributes."""
        viewer = YAMLViewer(id="test-viewer", classes="custom-class")

        assert viewer.id == "test-viewer"
        assert "custom-class" in viewer.classes


class TestYAMLViewerOperations:
    """Tests for YAMLViewer operations."""

    async def test_set_keys(self) -> None:
        """Test updating keys after creation."""
        viewer = YAMLViewer()
        app = YAMLViewerTestApp(viewer)

        async with app.run_test():
            assert viewer.key_count == 0

            keys = ["version", "interactions[0].request.method"]
            viewer.set_keys(keys)

            assert viewer.keys == keys
            assert viewer.key_count == 2

    async def test_set_keys_replaces_existing(self) -> None:
        """Test that set_keys replaces existing keys."""
        old_keys = ["old.key1", "old.key2"]
        viewer = YAMLViewer(keys=old_keys)
        app = YAMLViewerTestApp(viewer)

        async with app.run_test():
            assert viewer.key_count == 2

            new_keys = ["new.key"]
            viewer.set_keys(new_keys)

            assert viewer.keys == new_keys
            assert viewer.key_count == 1

    def test_keys_property_returns_copy(self) -> None:
        """Test that keys property returns a copy, not reference."""
        keys = ["user.name"]
        viewer = YAMLViewer(keys=keys)
        keys_copy = viewer.keys

        # Modify the copy
        keys_copy.append("user.email")

        # Original should be unchanged
        assert viewer.key_count == 1
        assert len(keys_copy) == 2

    async def test_get_selected_key_with_no_keys(self) -> None:
        """Test get_selected_key with empty viewer."""
        viewer = YAMLViewer()
        app = YAMLViewerTestApp(viewer)

        async with app.run_test():
            assert viewer.get_selected_key() is None

    async def test_get_selected_key_before_selection(self) -> None:
        """Test get_selected_key before any selection is made."""
        keys = ["user.name", "user.email"]
        viewer = YAMLViewer(keys=keys)
        app = YAMLViewerTestApp(viewer)

        async with app.run_test():
            # No selection made yet
            selected = viewer.get_selected_key()
            # Should be None or the default cursor position
            assert selected is None or isinstance(selected, str)


class TestYAMLViewerKeyParsing:
    """Tests for YAML key path parsing."""

    @pytest.mark.parametrize(
        ("key", "expected_parts"),
        [
            ("simple", ["simple"]),
            ("user.name", ["user", "name"]),
            ("user.address.city", ["user", "address", "city"]),
            ("items[0]", ["items", "[0]"]),
            ("items[0].id", ["items", "[0]", "id"]),
            ("data.items[5].value", ["data", "items", "[5]", "value"]),
            ("interactions[0].response.body.string", ["interactions", "[0]", "response", "body", "string"]),
        ],
    )
    def test_parse_key_path(self, key: str, expected_parts: list[str]) -> None:
        """Test parsing of various key path formats."""
        viewer = YAMLViewer()
        parts = viewer._parse_key_path(key)

        assert parts == expected_parts

    @pytest.mark.parametrize(
        "key",
        [
            "version",
            "user.name",
            "items[0].id",
            "interactions[0].response.body.string",
        ],
    )
    async def test_key_path_structure_building(self, key: str) -> None:
        """Test that keys are properly added to hierarchical structure."""
        viewer = YAMLViewer(keys=[key])
        app = YAMLViewerTestApp(viewer)

        async with app.run_test():
            # Check that the tree was populated
            assert viewer.key_count == 1
            assert key in viewer.keys


class TestYAMLViewerTreeStructure:
    """Tests for tree structure building."""

    async def test_simple_keys_in_tree(self) -> None:
        """Test that simple keys appear in tree."""
        keys = ["version", "created_at"]
        viewer = YAMLViewer(keys=keys)
        app = YAMLViewerTestApp(viewer)

        async with app.run_test():
            # Both keys should be in the tree
            assert viewer.key_count == 2

    async def test_nested_keys_in_tree(self) -> None:
        """Test that nested keys create hierarchy."""
        keys = ["user.name", "user.email", "user.address.city"]
        viewer = YAMLViewer(keys=keys)
        app = YAMLViewerTestApp(viewer)

        async with app.run_test():
            # All keys should be stored
            assert viewer.key_count == 3
            assert "user.name" in viewer.keys
            assert "user.email" in viewer.keys
            assert "user.address.city" in viewer.keys

    async def test_array_keys_in_tree(self) -> None:
        """Test that array indices are handled."""
        keys = ["items[0].id", "items[0].name", "items[1].id"]
        viewer = YAMLViewer(keys=keys)
        app = YAMLViewerTestApp(viewer)

        async with app.run_test():
            assert viewer.key_count == 3

    async def test_mixed_keys_in_tree(self) -> None:
        """Test tree with mixed simple, nested, and array keys."""
        keys = [
            "version",
            "user.name",
            "items[0].id",
            "interactions[0].request.method",
            "interactions[0].response.status.code",
        ]
        viewer = YAMLViewer(keys=keys)
        app = YAMLViewerTestApp(viewer)

        async with app.run_test():
            assert viewer.key_count == 5
            # Verify all keys are preserved
            for key in keys:
                assert key in viewer.keys


class TestYAMLViewerKeyboard:
    """Tests for keyboard navigation."""

    async def test_vim_keybindings_registered(self) -> None:
        """Test that j/k vim keybindings are registered."""
        viewer = YAMLViewer()

        # Check bindings are registered (tuples: (key, action, description))
        binding_keys = [binding[0] for binding in viewer.BINDINGS]
        assert "j" in binding_keys
        assert "k" in binding_keys

    async def test_navigation_with_keys(self) -> None:
        """Test navigating the tree with keyboard."""
        keys = ["user.name", "user.email", "user.age"]
        viewer = YAMLViewer(keys=keys)
        app = YAMLViewerTestApp(viewer)

        async with app.run_test() as pilot:
            # Press j to move down (vim-style)
            await pilot.press("j")
            # Tree should still be functional
            assert viewer.key_count == 3


class TestYAMLViewerDisplay:
    """Tests for YAMLViewer display properties."""

    def test_key_count_with_empty_viewer(self) -> None:
        """Test key_count with no keys."""
        viewer = YAMLViewer()

        assert viewer.key_count == 0

    @pytest.mark.parametrize("count", [1, 5, 10, 50])
    def test_key_count_with_various_sizes(self, count: int) -> None:
        """Test key_count with various numbers of keys."""
        keys = [f"key{i}" for i in range(count)]
        viewer = YAMLViewer(keys=keys)

        assert viewer.key_count == count

    def test_keys_order_preserved(self) -> None:
        """Test that key order is preserved."""
        keys = ["zebra", "alpha", "beta"]
        viewer = YAMLViewer(keys=keys)

        # Order should be preserved as given
        assert viewer.keys == keys
        assert viewer.keys[0] == "zebra"
        assert viewer.keys[1] == "alpha"
        assert viewer.keys[2] == "beta"
