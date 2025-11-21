"""Tests for preview engine."""

from __future__ import annotations

from pathlib import Path

import pytest

from vcr_tui.config.defaults import get_default_config
from vcr_tui.config.models import Channel, Config, ExtractionRule
from vcr_tui.preview.engine import PreviewEngine, PreviewResult


class TestPreviewEngine:
    """Tests for PreviewEngine class."""

    @pytest.fixture
    def config(self) -> Config:
        """Return a test configuration."""
        return get_default_config()

    @pytest.fixture
    def engine(self, config: Config) -> PreviewEngine:
        """Return a PreviewEngine instance."""
        return PreviewEngine(config)

    def test_engine_initialization(self, engine: PreviewEngine) -> None:
        """Test that engine initializes correctly."""
        assert engine is not None
        assert engine.config is not None
        assert engine.parser is not None
        assert engine.extractor is not None
        assert engine.formatter is not None


class TestDiscoverFiles:
    """Tests for file discovery."""

    @pytest.fixture
    def config(self) -> Config:
        """Return a config with YAML glob patterns."""
        channel = Channel(
            name="test",
            glob_patterns=["*.yaml", "*.yml"],
            extraction_rules=[],
        )
        return Config(channels={"test": channel}, default_channel="test")

    @pytest.fixture
    def engine(self, config: Config) -> PreviewEngine:
        """Return a PreviewEngine instance."""
        return PreviewEngine(config)

    def test_discover_files_in_directory(
        self, engine: PreviewEngine, cassettes_dir: Path
    ) -> None:
        """Test discovering files in a directory."""
        files = engine.discover_files(cassettes_dir)

        assert len(files) > 0
        assert all(f.suffix in [".yaml", ".yml"] for f in files)

    def test_discover_files_with_channel(
        self, engine: PreviewEngine, cassettes_dir: Path
    ) -> None:
        """Test discovering files with specific channel."""
        files = engine.discover_files(cassettes_dir, "test")

        assert len(files) > 0

    def test_discover_files_disabled_channel(self, cassettes_dir: Path) -> None:
        """Test that disabled channel returns no files."""
        channel = Channel(
            name="disabled",
            glob_patterns=["*.yaml"],
            extraction_rules=[],
            enabled=False,
        )
        config = Config(channels={"disabled": channel}, default_channel="disabled")
        engine = PreviewEngine(config)

        files = engine.discover_files(cassettes_dir)

        assert files == []

    def test_discover_files_nonexistent_channel(
        self, engine: PreviewEngine, cassettes_dir: Path
    ) -> None:
        """Test discovering files with non-existent channel."""
        files = engine.discover_files(cassettes_dir, "nonexistent")

        assert files == []

    def test_discover_files_empty_directory(
        self, engine: PreviewEngine, tmp_path: Path
    ) -> None:
        """Test discovering files in empty directory."""
        files = engine.discover_files(tmp_path)

        assert files == []


class TestGetYAMLKeys:
    """Tests for YAML key extraction."""

    @pytest.fixture
    def engine(self) -> PreviewEngine:
        """Return a PreviewEngine instance."""
        return PreviewEngine(get_default_config())

    def test_get_yaml_keys_from_cassette(
        self, engine: PreviewEngine, cassettes_dir: Path
    ) -> None:
        """Test extracting keys from VCR cassette."""
        cassette = cassettes_dir / "example_api.yaml"
        keys = engine.get_yaml_keys(cassette)

        assert "version" in keys
        assert "interactions" in keys
        assert "interactions[0]" in keys
        assert "interactions[0].request" in keys
        assert "interactions[0].response.body.string" in keys

    def test_get_yaml_keys_nonexistent_file(
        self, engine: PreviewEngine, tmp_path: Path
    ) -> None:
        """Test getting keys from non-existent file raises error."""
        nonexistent = tmp_path / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError):
            engine.get_yaml_keys(nonexistent)


class TestPreviewKey:
    """Tests for previewing specific keys."""

    @pytest.fixture
    def config(self) -> Config:
        """Return a config with test extraction rules."""
        channel = Channel(
            name="test",
            glob_patterns=["*.yaml"],
            extraction_rules=[
                ExtractionRule(
                    path="interactions[].response.body.string",
                    formatter="json",
                    label="Response Body",
                    metadata_keys=["interactions[0].request.method"],
                ),
                ExtractionRule(
                    path="interactions[].request.method",
                    formatter="text",
                    label="Request Method",
                ),
            ],
        )
        return Config(channels={"test": channel}, default_channel="test")

    @pytest.fixture
    def engine(self, config: Config) -> PreviewEngine:
        """Return a PreviewEngine instance."""
        return PreviewEngine(config)

    def test_preview_key_with_matching_rule(
        self, engine: PreviewEngine, cassettes_dir: Path
    ) -> None:
        """Test previewing a key that matches extraction rule."""
        cassette = cassettes_dir / "example_api.yaml"
        result = engine.preview_key(
            cassette, "interactions[0].response.body.string"
        )

        assert result is not None
        assert isinstance(result, PreviewResult)
        assert result.content
        assert result.formatter == "json"
        assert "John Doe" in result.content

    def test_preview_key_with_metadata(
        self, engine: PreviewEngine, cassettes_dir: Path
    ) -> None:
        """Test that metadata is extracted correctly."""
        cassette = cassettes_dir / "example_api.yaml"
        result = engine.preview_key(
            cassette, "interactions[0].response.body.string"
        )

        assert result is not None
        assert "interactions[0].request.method" in result.metadata

    def test_preview_key_no_matching_rule(
        self, engine: PreviewEngine, cassettes_dir: Path
    ) -> None:
        """Test previewing a key with no matching rule returns None."""
        cassette = cassettes_dir / "example_api.yaml"
        result = engine.preview_key(cassette, "version")

        assert result is None

    def test_preview_key_nonexistent_file(
        self, engine: PreviewEngine, tmp_path: Path
    ) -> None:
        """Test previewing key from non-existent file returns None."""
        nonexistent = tmp_path / "nonexistent.yaml"
        result = engine.preview_key(nonexistent, "some.key")

        assert result is None

    def test_preview_key_with_label(
        self, engine: PreviewEngine, cassettes_dir: Path
    ) -> None:
        """Test that preview result includes rule label."""
        cassette = cassettes_dir / "example_api.yaml"
        result = engine.preview_key(
            cassette, "interactions[0].response.body.string"
        )

        assert result is not None
        assert result.label == "Response Body"


class TestPreviewFile:
    """Tests for previewing entire files."""

    @pytest.fixture
    def config(self) -> Config:
        """Return a config with test extraction rules."""
        channel = Channel(
            name="test",
            glob_patterns=["*.yaml"],
            extraction_rules=[
                ExtractionRule(
                    path="interactions[].response.body.string",
                    formatter="json",
                ),
                ExtractionRule(
                    path="interactions[].request.method",
                    formatter="text",
                ),
            ],
        )
        return Config(channels={"test": channel}, default_channel="test")

    @pytest.fixture
    def engine(self, config: Config) -> PreviewEngine:
        """Return a PreviewEngine instance."""
        return PreviewEngine(config)

    def test_preview_file_returns_multiple_results(
        self, engine: PreviewEngine, cassettes_dir: Path
    ) -> None:
        """Test that preview_file returns multiple matching keys."""
        cassette = cassettes_dir / "example_api.yaml"
        results = engine.preview_file(cassette)

        assert len(results) > 0
        # Should have results for both interactions
        assert any("interactions[0]" in key for key in results)
        assert any("interactions[1]" in key for key in results)

    def test_preview_file_nonexistent(
        self, engine: PreviewEngine, tmp_path: Path
    ) -> None:
        """Test previewing non-existent file returns empty dict."""
        nonexistent = tmp_path / "nonexistent.yaml"
        results = engine.preview_file(nonexistent)

        assert results == {}

    def test_preview_file_all_values_formatted(
        self, engine: PreviewEngine, cassettes_dir: Path
    ) -> None:
        """Test that all preview results are properly formatted."""
        cassette = cassettes_dir / "example_api.yaml"
        results = engine.preview_file(cassette)

        for key, result in results.items():
            assert isinstance(result, PreviewResult)
            assert result.content
            assert result.formatter in ["json", "text"]


class TestGetPreviewableKeys:
    """Tests for getting list of previewable keys."""

    @pytest.fixture
    def config(self) -> Config:
        """Return a config with specific extraction rules."""
        channel = Channel(
            name="test",
            glob_patterns=["*.yaml"],
            extraction_rules=[
                ExtractionRule(
                    path="interactions[].response.body.string",
                    formatter="json",
                ),
            ],
        )
        return Config(channels={"test": channel}, default_channel="test")

    @pytest.fixture
    def engine(self, config: Config) -> PreviewEngine:
        """Return a PreviewEngine instance."""
        return PreviewEngine(config)

    def test_get_previewable_keys(
        self, engine: PreviewEngine, cassettes_dir: Path
    ) -> None:
        """Test getting list of previewable keys."""
        cassette = cassettes_dir / "example_api.yaml"
        keys = engine.get_previewable_keys(cassette)

        # Should only return keys matching the extraction rule
        assert len(keys) > 0
        assert all("response.body.string" in key for key in keys)

    def test_get_previewable_keys_filters_non_matching(
        self, engine: PreviewEngine, cassettes_dir: Path
    ) -> None:
        """Test that non-matching keys are filtered out."""
        cassette = cassettes_dir / "example_api.yaml"
        all_keys = engine.get_yaml_keys(cassette)
        previewable_keys = engine.get_previewable_keys(cassette)

        # Previewable should be subset of all keys
        assert len(previewable_keys) < len(all_keys)

    def test_get_previewable_keys_nonexistent_file(
        self, engine: PreviewEngine, tmp_path: Path
    ) -> None:
        """Test getting previewable keys from non-existent file."""
        nonexistent = tmp_path / "nonexistent.yaml"
        keys = engine.get_previewable_keys(nonexistent)

        assert keys == []


class TestIntegration:
    """Integration tests with real VCR cassettes."""

    @pytest.fixture
    def engine(self) -> PreviewEngine:
        """Return engine with default config."""
        return PreviewEngine(get_default_config())

    def test_complete_workflow(
        self, engine: PreviewEngine, cassettes_dir: Path
    ) -> None:
        """Test complete workflow: discover, extract keys, preview."""
        # 1. Discover files
        files = engine.discover_files(cassettes_dir)
        assert len(files) > 0

        # 2. Get keys from first file
        first_file = files[0]
        keys = engine.get_yaml_keys(first_file)
        assert len(keys) > 0

        # 3. Get previewable keys
        previewable = engine.get_previewable_keys(first_file)
        assert len(previewable) > 0

        # 4. Preview a key
        if previewable:
            result = engine.preview_key(first_file, previewable[0])
            assert result is not None
            assert result.content

    def test_preview_vcr_json_response(
        self, engine: PreviewEngine, cassettes_dir: Path
    ) -> None:
        """Test previewing JSON response from VCR cassette."""
        cassette = cassettes_dir / "example_api.yaml"

        # Find response body keys
        keys = engine.get_yaml_keys(cassette)
        response_keys = [k for k in keys if "response.body.string" in k]

        if response_keys:
            result = engine.preview_key(cassette, response_keys[0], "vcr")
            assert result is not None
            # Should be formatted as JSON
            assert "John" in result.content or "Jane" in result.content

    def test_preview_html_response(
        self, engine: PreviewEngine, cassettes_dir: Path
    ) -> None:
        """Test previewing HTML response from VCR cassette."""
        cassette = cassettes_dir / "html_response.yaml"

        keys = engine.get_yaml_keys(cassette)
        response_keys = [k for k in keys if "response.body.string" in k]

        if response_keys:
            result = engine.preview_key(cassette, response_keys[0], "vcr")
            assert result is not None
            assert result.content

    def test_preview_empty_response(
        self, engine: PreviewEngine, cassettes_dir: Path
    ) -> None:
        """Test previewing cassette with empty response."""
        cassette = cassettes_dir / "empty_response.yaml"

        keys = engine.get_yaml_keys(cassette)
        response_keys = [k for k in keys if "response.body.string" in k]

        if response_keys:
            result = engine.preview_key(cassette, response_keys[0], "vcr")
            # Empty response should still create a preview result
            assert result is not None
