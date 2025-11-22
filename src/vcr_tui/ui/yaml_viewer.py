"""YAML viewer widget for displaying YAML structure as a tree."""

from __future__ import annotations

from typing import Any

from textual.widgets import Tree
from textual.widgets.tree import TreeNode


class YAMLViewer(Tree[str]):
    """Widget for displaying YAML keys in a hierarchical tree structure.

    Displays keys from a YAML file in a collapsible tree view. Keys are shown
    in their hierarchical structure (e.g., "user.name" becomes User > name).
    Emits Tree.NodeSelected messages when a key is chosen.
    """

    BINDINGS = [
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
    ]

    def __init__(
        self,
        label: str = "YAML Keys",
        keys: list[str] | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the YAML viewer widget.

        Args:
            label: Root label for the tree
            keys: Initial list of YAML keys to display
            name: Widget name
            id: Widget ID for CSS
            classes: CSS classes
        """
        super().__init__(
            label,
            data=None,
            name=name,
            id=id,
            classes=classes,
        )
        self._keys: list[str] = keys or []
        self._key_nodes: dict[str, TreeNode[str]] = {}

    def on_mount(self) -> None:
        """Called when widget is mounted to the app."""
        if self._keys:
            self._populate_tree()

    def set_keys(self, keys: list[str]) -> None:
        """Update the displayed YAML keys.

        Args:
            keys: New list of YAML keys to display
        """
        self._keys = keys
        self._key_nodes.clear()
        self._populate_tree()

    def _populate_tree(self) -> None:
        """Populate the tree with YAML keys."""
        # Clear existing nodes
        self.clear()

        # Build hierarchical structure from flat keys
        tree_structure: dict[str, Any] = {}
        for key in self._keys:
            self._add_key_to_structure(key, tree_structure)

        # Build the tree nodes
        self._build_tree_nodes(tree_structure, self.root)

        # Expand root by default
        self.root.expand()

    def _add_key_to_structure(self, key: str, structure: dict[str, Any]) -> None:
        """Add a flat key to the hierarchical structure.

        Args:
            key: Flat key path (e.g., "user.name" or "items[0].id")
            structure: Dictionary representing the tree structure
        """
        parts = self._parse_key_path(key)
        current = structure

        for i, part in enumerate(parts):
            if part not in current:
                # Check if this is the last part
                is_leaf = i == len(parts) - 1
                if is_leaf:
                    # Store the full path for leaf nodes
                    current[part] = {"__full_path__": key}
                else:
                    # Create intermediate node
                    current[part] = {}

            current = current[part]

    def _parse_key_path(self, key: str) -> list[str]:
        """Parse a key path into its component parts.

        Args:
            key: Key path (e.g., "user.name" or "items[0].id")

        Returns:
            List of path components (e.g., ["user", "name"] or ["items", "[0]", "id"])
        """
        # Simple parsing - split by dots, keep brackets as separate parts
        parts: list[str] = []
        current_part = ""

        for char in key:
            if char == ".":
                if current_part:
                    parts.append(current_part)
                    current_part = ""
            elif char == "[":
                if current_part:
                    parts.append(current_part)
                    current_part = ""
                current_part = "["
            elif char == "]":
                current_part += "]"
                parts.append(current_part)
                current_part = ""
            else:
                current_part += char

        if current_part:
            parts.append(current_part)

        return parts

    def _build_tree_nodes(
        self, structure: dict[str, Any], parent_node: TreeNode[str]
    ) -> None:
        """Recursively build tree nodes from structure.

        Args:
            structure: Hierarchical dictionary structure
            parent_node: Parent tree node to add children to
        """
        for key, value in sorted(structure.items()):
            if isinstance(value, dict) and "__full_path__" in value:
                # This is a leaf node - add as non-expandable
                full_path = value["__full_path__"]
                node = parent_node.add_leaf(key, data=full_path)
                self._key_nodes[full_path] = node
            elif isinstance(value, dict):
                # This is an intermediate node - add as expandable
                node = parent_node.add(key, data=None)
                self._build_tree_nodes(value, node)
            else:
                # Shouldn't happen, but handle it
                parent_node.add_leaf(str(key), data=str(value))

    def get_selected_key(self) -> str | None:
        """Get the currently selected YAML key path.

        Returns:
            Full key path or None if no selection or non-leaf node selected
        """
        if self.cursor_node is None:
            return None

        # Return the data (full path) if it's a leaf node
        return self.cursor_node.data

    @property
    def keys(self) -> list[str]:
        """Get the current list of keys.

        Returns:
            List of YAML key paths
        """
        return self._keys.copy()

    @property
    def key_count(self) -> int:
        """Get the number of keys in the viewer.

        Returns:
            Count of keys
        """
        return len(self._keys)
