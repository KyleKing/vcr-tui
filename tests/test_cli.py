"""Tests for CLI interface."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from vcr_tui.cli import discover, keys, main, preview, previewable


class TestCLIMain:
    """Tests for main CLI group."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Return a Click test runner."""
        return CliRunner()

    def test_main_help(self, runner: CliRunner) -> None:
        """Test main command shows help."""
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "VCR-TUI" in result.output
        assert "discover" in result.output
        assert "keys" in result.output
        assert "preview" in result.output

    def test_main_version(self, runner: CliRunner) -> None:
        """Test version flag works."""
        result = runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert "version" in result.output.lower()


class TestDiscoverCommand:
    """Tests for discover command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Return a Click test runner."""
        return CliRunner()

    def test_discover_finds_files(
        self, runner: CliRunner, cassettes_dir: Path
    ) -> None:
        """Test discover command finds files."""
        result = runner.invoke(discover, [str(cassettes_dir)])

        assert result.exit_code == 0
        assert "Found" in result.output
        assert "file" in result.output
        assert "example_api.yaml" in result.output or "html_response.yaml" in result.output

    def test_discover_with_channel(
        self, runner: CliRunner, cassettes_dir: Path
    ) -> None:
        """Test discover with channel option."""
        result = runner.invoke(discover, [str(cassettes_dir), "-c", "vcr"])

        assert result.exit_code == 0
        assert "Found" in result.output

    def test_discover_empty_directory(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test discover in empty directory."""
        result = runner.invoke(discover, [str(tmp_path)])

        assert result.exit_code == 1
        assert "No files found" in result.output

    def test_discover_default_directory(self, runner: CliRunner) -> None:
        """Test discover uses current directory by default."""
        result = runner.invoke(discover)

        # Should work (may or may not find files)
        assert result.exit_code in [0, 1]


class TestKeysCommand:
    """Tests for keys command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Return a Click test runner."""
        return CliRunner()

    def test_keys_lists_all_keys(
        self, runner: CliRunner, cassettes_dir: Path
    ) -> None:
        """Test keys command lists all keys in file."""
        cassette = cassettes_dir / "example_api.yaml"
        result = runner.invoke(keys, [str(cassette)])

        assert result.exit_code == 0
        assert "Keys in" in result.output
        assert "version" in result.output
        assert "interactions" in result.output

    def test_keys_with_channel(
        self, runner: CliRunner, cassettes_dir: Path
    ) -> None:
        """Test keys command with channel option."""
        cassette = cassettes_dir / "example_api.yaml"
        result = runner.invoke(keys, [str(cassette), "-c", "vcr"])

        assert result.exit_code == 0
        assert "Keys in" in result.output

    def test_keys_nonexistent_file(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test keys command with non-existent file."""
        nonexistent = tmp_path / "nonexistent.yaml"
        result = runner.invoke(keys, [str(nonexistent)])

        # Click validates path and exits with code 2 for usage errors
        assert result.exit_code == 2
        assert "Error" in result.output or "does not exist" in result.output

    def test_keys_shows_nested_paths(
        self, runner: CliRunner, cassettes_dir: Path
    ) -> None:
        """Test that keys shows nested paths."""
        cassette = cassettes_dir / "example_api.yaml"
        result = runner.invoke(keys, [str(cassette)])

        assert result.exit_code == 0
        # Should show nested paths with dot notation
        assert "interactions[0]" in result.output
        assert "response" in result.output or "request" in result.output


class TestPreviewableCommand:
    """Tests for previewable command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Return a Click test runner."""
        return CliRunner()

    def test_previewable_lists_matching_keys(
        self, runner: CliRunner, cassettes_dir: Path
    ) -> None:
        """Test previewable command lists keys with extraction rules."""
        cassette = cassettes_dir / "example_api.yaml"
        result = runner.invoke(previewable, [str(cassette)])

        assert result.exit_code == 0
        assert "Previewable keys" in result.output
        # VCR channel should match response body keys
        assert "response.body" in result.output or "request.body" in result.output

    def test_previewable_with_channel(
        self, runner: CliRunner, cassettes_dir: Path
    ) -> None:
        """Test previewable with specific channel."""
        cassette = cassettes_dir / "example_api.yaml"
        result = runner.invoke(previewable, [str(cassette), "-c", "vcr"])

        assert result.exit_code == 0
        assert "Previewable keys" in result.output

    def test_previewable_no_matches(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test previewable when no keys match."""
        # Create a simple YAML file with no matching keys
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("simple: value\n")

        result = runner.invoke(previewable, [str(yaml_file)])

        assert result.exit_code == 1
        assert "No previewable keys" in result.output


class TestPreviewCommand:
    """Tests for preview command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Return a Click test runner."""
        return CliRunner()

    def test_preview_shows_content(
        self, runner: CliRunner, cassettes_dir: Path
    ) -> None:
        """Test preview command shows formatted content."""
        cassette = cassettes_dir / "example_api.yaml"
        key = "interactions[0].response.body.string"

        result = runner.invoke(preview, [str(cassette), key])

        assert result.exit_code == 0
        # Should show JSON content
        assert "John" in result.output or "Jane" in result.output or "{" in result.output

    def test_preview_with_channel(
        self, runner: CliRunner, cassettes_dir: Path
    ) -> None:
        """Test preview with channel option."""
        cassette = cassettes_dir / "example_api.yaml"
        key = "interactions[0].response.body.string"

        result = runner.invoke(preview, [str(cassette), key, "-c", "vcr"])

        assert result.exit_code == 0

    @pytest.mark.parametrize(
        "output_format",
        ["content", "metadata", "all"],
    )
    def test_preview_output_formats(
        self, runner: CliRunner, cassettes_dir: Path, output_format: str
    ) -> None:
        """Test preview with different output formats."""
        cassette = cassettes_dir / "example_api.yaml"
        key = "interactions[0].response.body.string"

        result = runner.invoke(preview, [str(cassette), key, "-f", output_format])

        assert result.exit_code == 0
        if output_format == "metadata":
            # Metadata format doesn't show content
            pass  # Depends on extraction rule metadata
        elif output_format == "all":
            assert "Formatter:" in result.output
            assert "Content:" in result.output
        else:  # content
            # Should show the actual content
            assert len(result.output) > 0

    def test_preview_nonexistent_key(
        self, runner: CliRunner, cassettes_dir: Path
    ) -> None:
        """Test preview with key that has no matching rule."""
        cassette = cassettes_dir / "example_api.yaml"
        key = "nonexistent.key"

        result = runner.invoke(preview, [str(cassette), key])

        assert result.exit_code == 1
        assert "No preview available" in result.output

    def test_preview_nonexistent_file(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test preview with non-existent file."""
        nonexistent = tmp_path / "nonexistent.yaml"
        key = "some.key"

        result = runner.invoke(preview, [str(nonexistent), key])

        # Click validates path and exits with code 2 for usage errors
        assert result.exit_code == 2
        assert "Error" in result.output or "does not exist" in result.output


class TestIntegration:
    """Integration tests with real workflow."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Return a Click test runner."""
        return CliRunner()

    def test_complete_workflow(
        self, runner: CliRunner, cassettes_dir: Path
    ) -> None:
        """Test complete CLI workflow: discover → keys → previewable → preview."""
        # 1. Discover files
        result = runner.invoke(discover, [str(cassettes_dir)])
        assert result.exit_code == 0

        # 2. List keys from first file
        cassette = cassettes_dir / "example_api.yaml"
        result = runner.invoke(keys, [str(cassette)])
        assert result.exit_code == 0

        # 3. List previewable keys
        result = runner.invoke(previewable, [str(cassette)])
        assert result.exit_code == 0

        # 4. Preview a specific key
        key = "interactions[0].response.body.string"
        result = runner.invoke(preview, [str(cassette), key])
        assert result.exit_code == 0

    def test_json_response_preview(
        self, runner: CliRunner, cassettes_dir: Path
    ) -> None:
        """Test previewing JSON response from VCR cassette."""
        cassette = cassettes_dir / "example_api.yaml"
        key = "interactions[0].response.body.string"

        result = runner.invoke(preview, [str(cassette), key, "-c", "vcr"])

        assert result.exit_code == 0
        # Should be formatted JSON
        assert "{" in result.output
        assert "John" in result.output or "name" in result.output

    def test_html_response_preview(
        self, runner: CliRunner, cassettes_dir: Path
    ) -> None:
        """Test previewing HTML response."""
        cassette = cassettes_dir / "html_response.yaml"
        key = "interactions[0].response.body.string"

        result = runner.invoke(preview, [str(cassette), key, "-c", "vcr"])

        assert result.exit_code == 0
        # Should show HTML content
        assert result.output  # Non-empty

    def test_empty_response_preview(
        self, runner: CliRunner, cassettes_dir: Path
    ) -> None:
        """Test previewing cassette with empty response."""
        cassette = cassettes_dir / "empty_response.yaml"
        key = "interactions[0].response.body.string"

        result = runner.invoke(preview, [str(cassette), key, "-c", "vcr"])

        # Should handle empty responses gracefully
        assert result.exit_code == 0


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Return a Click test runner."""
        return CliRunner()

    def test_invalid_directory(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test discover with invalid directory path."""
        nonexistent = tmp_path / "nonexistent"
        result = runner.invoke(discover, [str(nonexistent)])

        assert result.exit_code != 0

    def test_file_as_directory(
        self, runner: CliRunner, cassettes_dir: Path
    ) -> None:
        """Test discover when given a file instead of directory."""
        cassette = cassettes_dir / "example_api.yaml"
        result = runner.invoke(discover, [str(cassette)])

        # Click should validate this
        assert result.exit_code != 0

    def test_invalid_key_syntax(
        self, runner: CliRunner, cassettes_dir: Path
    ) -> None:
        """Test preview with malformed key path."""
        cassette = cassettes_dir / "example_api.yaml"
        # Key with unclosed bracket
        key = "interactions[0"

        result = runner.invoke(preview, [str(cassette), key])

        # Should handle gracefully (either error or no match)
        assert result.exit_code in [0, 1]
