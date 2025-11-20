"""Tests for default configuration."""

from __future__ import annotations

import pytest

from vcr_tui.config.defaults import get_default_config
from vcr_tui.config.models import Config


class TestDefaultConfig:
    """Tests for get_default_config()."""

    def test_returns_config_instance(self) -> None:
        """Test that get_default_config() returns a Config instance."""
        config = get_default_config()

        assert isinstance(config, Config)

    def test_has_default_channel(self) -> None:
        """Test that default config has a default channel set."""
        config = get_default_config()

        assert config.default_channel is not None
        assert config.default_channel == "vcr"

    def test_root_is_false(self) -> None:
        """Test that default config has root=False."""
        config = get_default_config()

        assert config.root is False

    @pytest.mark.parametrize(
        "channel_name",
        ["vcr", "yaml"],
    )
    def test_has_required_channels(self, channel_name: str) -> None:
        """Test that default config has required channels."""
        config = get_default_config()

        assert channel_name in config.channels
        assert config.channels[channel_name].name == channel_name
        assert config.channels[channel_name].enabled is True

    def test_vcr_channel_has_glob_patterns(self) -> None:
        """Test that vcr channel has appropriate glob patterns."""
        config = get_default_config()
        vcr_channel = config.channels["vcr"]

        assert len(vcr_channel.glob_patterns) > 0
        assert any("yaml" in pattern for pattern in vcr_channel.glob_patterns)

    def test_vcr_channel_has_extraction_rules(self) -> None:
        """Test that vcr channel has extraction rules."""
        config = get_default_config()
        vcr_channel = config.channels["vcr"]

        assert len(vcr_channel.extraction_rules) > 0

    @pytest.mark.parametrize(
        ("channel_name", "min_rules"),
        [
            ("vcr", 2),  # At least request and response rules
            ("yaml", 1),  # At least full YAML rule
        ],
    )
    def test_channels_have_minimum_rules(
        self,
        channel_name: str,
        min_rules: int,
    ) -> None:
        """Test that channels have minimum number of extraction rules."""
        config = get_default_config()
        channel = config.channels[channel_name]

        assert len(channel.extraction_rules) >= min_rules

    def test_extraction_rules_have_required_fields(self) -> None:
        """Test that all extraction rules have required fields."""
        config = get_default_config()

        for channel in config.channels.values():
            for rule in channel.extraction_rules:
                assert rule.path
                assert rule.formatter
                # label and metadata_keys are optional

    @pytest.mark.parametrize(
        "formatter",
        ["text", "json"],
    )
    def test_vcr_channel_has_formatters(self, formatter: str) -> None:
        """Test that vcr channel has text and json formatters."""
        config = get_default_config()
        vcr_channel = config.channels["vcr"]

        formatters = [rule.formatter for rule in vcr_channel.extraction_rules]
        assert formatter in formatters

    def test_yaml_channel_has_yaml_formatter(self) -> None:
        """Test that yaml channel has yaml formatter."""
        config = get_default_config()
        yaml_channel = config.channels["yaml"]

        formatters = [rule.formatter for rule in yaml_channel.extraction_rules]
        assert "yaml" in formatters

    def test_default_config_is_serializable(self) -> None:
        """Test that default config can be serialized and deserialized."""
        config = get_default_config()

        # Should be able to convert to dict and back
        data = config.to_dict()
        assert isinstance(data, dict)

        # Should be able to recreate from dict
        from vcr_tui.config.models import Config

        recreated = Config.from_dict(data)
        assert isinstance(recreated, Config)
        assert len(recreated.channels) == len(config.channels)

    def test_get_default_channel_works(self) -> None:
        """Test that get_channel() returns the default channel."""
        config = get_default_config()

        default_channel = config.get_channel()

        assert default_channel is not None
        assert default_channel.name == "vcr"

    def test_repeated_calls_return_independent_configs(self) -> None:
        """Test that repeated calls return independent config instances."""
        config1 = get_default_config()
        config2 = get_default_config()

        # Should be independent instances
        assert config1 is not config2

        # Modifying one shouldn't affect the other
        config1.default_channel = "yaml"
        assert config2.default_channel == "vcr"
