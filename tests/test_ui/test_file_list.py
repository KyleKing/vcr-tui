"""Tests for FileList widget."""

from __future__ import annotations

from pathlib import Path

import pytest
from textual.app import App, ComposeResult
from textual.widgets import ListItem

from vcr_tui.ui.file_list import FileList


class FileListTestApp(App[None]):
    """Test app for FileList widget."""

    def __init__(self, file_list: FileList) -> None:
        """Initialize with a FileList widget."""
        super().__init__()
        self.file_list = file_list

    def compose(self) -> ComposeResult:
        """Compose the app with the FileList widget."""
        yield self.file_list


class TestFileListCreation:
    """Tests for FileList widget creation."""

    def test_create_empty_list(self) -> None:
        """Test creating FileList with no files."""
        file_list = FileList()

        assert file_list.files == []
        assert file_list.file_count == 0

    def test_create_with_files(self, tmp_path: Path) -> None:
        """Test creating FileList with initial files."""
        files = [
            tmp_path / "file1.yaml",
            tmp_path / "file2.yaml",
            tmp_path / "file3.yaml",
        ]
        for f in files:
            f.touch()

        file_list = FileList(files=files)

        assert file_list.files == files
        assert file_list.file_count == 3

    async def test_create_with_initial_index(self, tmp_path: Path) -> None:
        """Test creating FileList with initial index."""
        files = [tmp_path / f"file{i}.yaml" for i in range(3)]
        for f in files:
            f.touch()

        file_list = FileList(files=files, initial_index=1)
        app = FileListTestApp(file_list)

        async with app.run_test():
            assert file_list.index == 1

    def test_create_with_id_and_classes(self) -> None:
        """Test creating FileList with CSS attributes."""
        file_list = FileList(id="test-list", classes="custom-class")

        assert file_list.id == "test-list"
        assert "custom-class" in file_list.classes


class TestFileListOperations:
    """Tests for FileList operations."""

    async def test_set_files(self, tmp_path: Path) -> None:
        """Test updating files after creation."""
        file_list = FileList()
        app = FileListTestApp(file_list)

        async with app.run_test():
            assert file_list.file_count == 0

            files = [tmp_path / "file1.yaml", tmp_path / "file2.yaml"]
            for f in files:
                f.touch()

            file_list.set_files(files)

            assert file_list.files == files
            assert file_list.file_count == 2

    async def test_set_files_replaces_existing(self, tmp_path: Path) -> None:
        """Test that set_files replaces existing files."""
        old_files = [tmp_path / "old1.yaml", tmp_path / "old2.yaml"]
        for f in old_files:
            f.touch()

        file_list = FileList(files=old_files)
        app = FileListTestApp(file_list)

        async with app.run_test():
            assert file_list.file_count == 2

            new_files = [tmp_path / "new1.yaml"]
            new_files[0].touch()

            file_list.set_files(new_files)

            assert file_list.files == new_files
            assert file_list.file_count == 1

    def test_files_property_returns_copy(self, tmp_path: Path) -> None:
        """Test that files property returns a copy, not reference."""
        files = [tmp_path / "file1.yaml"]
        files[0].touch()

        file_list = FileList(files=files)
        files_copy = file_list.files

        # Modify the copy
        files_copy.append(tmp_path / "file2.yaml")

        # Original should be unchanged
        assert file_list.file_count == 1
        assert len(files_copy) == 2

    def test_get_selected_file_with_no_files(self) -> None:
        """Test get_selected_file with empty list."""
        file_list = FileList()

        assert file_list.get_selected_file() is None

    async def test_get_selected_file_with_files(self, tmp_path: Path) -> None:
        """Test get_selected_file returns highlighted file."""
        files = [
            tmp_path / "file1.yaml",
            tmp_path / "file2.yaml",
            tmp_path / "file3.yaml",
        ]
        for f in files:
            f.touch()

        file_list = FileList(files=files, initial_index=1)
        app = FileListTestApp(file_list)

        async with app.run_test():
            # Should return file at index 1
            assert file_list.get_selected_file() == files[1]

    def test_get_selected_file_with_none_index(self, tmp_path: Path) -> None:
        """Test get_selected_file when index is None."""
        files = [tmp_path / "file1.yaml"]
        files[0].touch()

        file_list = FileList(files=files)
        file_list.index = None

        assert file_list.get_selected_file() is None

    @pytest.mark.parametrize(
        ("index", "expected_file_index"),
        [
            (0, 0),  # First file
            (1, 1),  # Middle file
            (2, 2),  # Last file
            (-1, 0),  # Negative clamped to 0
            (999, 2),  # Out of bounds clamped to last
        ],
    )
    async def test_get_selected_file_bounds_checking(
        self, tmp_path: Path, index: int, expected_file_index: int
    ) -> None:
        """Test that get_selected_file handles out-of-bounds indices."""
        files = [tmp_path / f"file{i}.yaml" for i in range(3)]
        for f in files:
            f.touch()

        file_list = FileList(files=files)
        app = FileListTestApp(file_list)

        async with app.run_test():
            file_list.index = index
            assert file_list.get_selected_file() == files[expected_file_index]


class TestFileListDisplay:
    """Tests for FileList display formatting."""

    def test_file_count_with_empty_list(self) -> None:
        """Test file_count with no files."""
        file_list = FileList()

        assert file_list.file_count == 0

    @pytest.mark.parametrize("count", [1, 5, 10, 100])
    def test_file_count_with_various_sizes(self, tmp_path: Path, count: int) -> None:
        """Test file_count with various list sizes."""
        files = [tmp_path / f"file{i}.yaml" for i in range(count)]
        for f in files:
            f.touch()

        file_list = FileList(files=files)

        assert file_list.file_count == count

    def test_files_display_order_preserved(self, tmp_path: Path) -> None:
        """Test that file order is preserved."""
        files = [
            tmp_path / "zebra.yaml",
            tmp_path / "alpha.yaml",
            tmp_path / "beta.yaml",
        ]
        for f in files:
            f.touch()

        file_list = FileList(files=files)

        # Order should be preserved as given, not sorted
        assert file_list.files == files
        assert file_list.files[0].name == "zebra.yaml"
        assert file_list.files[1].name == "alpha.yaml"
        assert file_list.files[2].name == "beta.yaml"
