"""Tests for configuration models."""

from __future__ import annotations

import pytest

from vcr_tui.config.models import Channel, Config, ExtractionRule


class TestExtractionRule:
    """Tests for ExtractionRule model."""

    @pytest.mark.parametrize(
        ("path", "formatter", "label", "metadata_keys"),
        [
            (".body.string", "text", "Response Body", ["status", "method"]),
            (".request.body", "json", None, []),
            (".data", "yaml", "Data", ["timestamp"]),
        ],
    )
    def test_extraction_rule_creation(
        self,
        path: str,
        formatter: str,
        label: str | None,
        metadata_keys: list[str],
    ) -> None:
        """Test creating ExtractionRule with various parameters."""
        rule = ExtractionRule(
            path=path,
            formatter=formatter,
            label=label,
            metadata_keys=metadata_keys,
        )

        assert rule.path == path
        assert rule.formatter == formatter
        assert rule.label == label
        assert rule.metadata_keys == metadata_keys

    @pytest.mark.parametrize(
        ("data", "expected_path", "expected_formatter"),
        [
            (
                {"path": ".body", "formatter": "json"},
                ".body",
                "json",
            ),
            (
                {"path": ".data", "formatter": "yaml", "label": "Test"},
                ".data",
                "yaml",
            ),
            (
                {
                    "path": ".response",
                    "formatter": "text",
                    "metadata_keys": ["status"],
                },
                ".response",
                "text",
            ),
        ],
    )
    def test_from_dict(
        self,
        data: dict[str, object],
        expected_path: str,
        expected_formatter: str,
    ) -> None:
        """Test ExtractionRule.from_dict() deserialization."""
        rule = ExtractionRule.from_dict(data)  # type: ignore[arg-type]

        assert rule.path == expected_path
        assert rule.formatter == expected_formatter

    def test_to_dict_minimal(self) -> None:
        """Test ExtractionRule.to_dict() with minimal data."""
        rule = ExtractionRule(path=".body", formatter="json")
        result = rule.to_dict()

        assert result == {
            "path": ".body",
            "formatter": "json",
        }

    def test_to_dict_complete(self) -> None:
        """Test ExtractionRule.to_dict() with all fields."""
        rule = ExtractionRule(
            path=".body.string",
            formatter="text",
            label="Response",
            metadata_keys=["status", "method"],
        )
        result = rule.to_dict()

        assert result == {
            "path": ".body.string",
            "formatter": "text",
            "label": "Response",
            "metadata_keys": ["status", "method"],
        }

    def test_round_trip_serialization(self) -> None:
        """Test that from_dict(to_dict()) preserves data."""
        original = ExtractionRule(
            path=".test",
            formatter="yaml",
            label="Test Label",
            metadata_keys=["key1", "key2"],
        )

        serialized = original.to_dict()
        deserialized = ExtractionRule.from_dict(serialized)

        assert deserialized.path == original.path
        assert deserialized.formatter == original.formatter
        assert deserialized.label == original.label
        assert deserialized.metadata_keys == original.metadata_keys


class TestChannel:
    """Tests for Channel model."""

    @pytest.mark.parametrize(
        ("name", "patterns", "enabled"),
        [
            ("vcr", ["**/*.yaml"], True),
            ("json", ["**/*.json", "**/*.jsonl"], True),
            ("disabled", ["**/*.txt"], False),
        ],
    )
    def test_channel_creation(
        self,
        name: str,
        patterns: list[str],
        enabled: bool,
    ) -> None:
        """Test creating Channel with various parameters."""
        channel = Channel(
            name=name,
            glob_patterns=patterns,
            enabled=enabled,
        )

        assert channel.name == name
        assert channel.glob_patterns == patterns
        assert channel.enabled == enabled
        assert channel.extraction_rules == []

    def test_channel_with_extraction_rules(self) -> None:
        """Test Channel with extraction rules."""
        rules = [
            ExtractionRule(path=".body", formatter="json"),
            ExtractionRule(path=".data", formatter="yaml"),
        ]
        channel = Channel(
            name="test",
            glob_patterns=["*.yaml"],
            extraction_rules=rules,
        )

        assert len(channel.extraction_rules) == 2
        assert channel.extraction_rules[0].path == ".body"
        assert channel.extraction_rules[1].path == ".data"

    def test_from_dict(self) -> None:
        """Test Channel.from_dict() deserialization."""
        data = {
            "glob_patterns": ["**/*.yaml"],
            "extraction_rules": [
                {"path": ".body", "formatter": "json"},
                {"path": ".data", "formatter": "yaml"},
            ],
            "enabled": True,
        }

        channel = Channel.from_dict("test_channel", data)

        assert channel.name == "test_channel"
        assert channel.glob_patterns == ["**/*.yaml"]
        assert len(channel.extraction_rules) == 2
        assert channel.enabled is True

    def test_to_dict(self) -> None:
        """Test Channel.to_dict() serialization."""
        channel = Channel(
            name="test",
            glob_patterns=["*.yaml"],
            extraction_rules=[
                ExtractionRule(path=".body", formatter="json"),
            ],
            enabled=True,
        )

        result = channel.to_dict()

        assert result["name"] == "test"
        assert result["glob_patterns"] == ["*.yaml"]
        assert len(result["extraction_rules"]) == 1
        assert result["enabled"] is True


class TestConfig:
    """Tests for Config model."""

    def test_config_defaults(self) -> None:
        """Test Config with default values."""
        config = Config()

        assert config.root is False
        assert config.channels == {}
        assert config.default_channel is None

    @pytest.mark.parametrize(
        ("root", "default_channel"),
        [
            (True, "vcr"),
            (False, "json"),
            (True, None),
        ],
    )
    def test_config_creation(
        self,
        root: bool,
        default_channel: str | None,
    ) -> None:
        """Test creating Config with various parameters."""
        config = Config(root=root, default_channel=default_channel)

        assert config.root == root
        assert config.default_channel == default_channel

    def test_get_channel_by_name(self) -> None:
        """Test Config.get_channel() with explicit name."""
        channel = Channel(name="test", glob_patterns=["*.yaml"])
        config = Config(channels={"test": channel})

        result = config.get_channel("test")

        assert result == channel

    def test_get_default_channel(self) -> None:
        """Test Config.get_channel() without name uses default."""
        channel = Channel(name="vcr", glob_patterns=["*.yaml"])
        config = Config(
            channels={"vcr": channel},
            default_channel="vcr",
        )

        result = config.get_channel()

        assert result == channel

    def test_get_channel_not_found(self) -> None:
        """Test Config.get_channel() returns None for missing channel."""
        config = Config()

        result = config.get_channel("nonexistent")

        assert result is None

    def test_from_dict(self) -> None:
        """Test Config.from_dict() deserialization."""
        data = {
            "root": True,
            "default_channel": "vcr",
            "channels": {
                "vcr": {
                    "glob_patterns": ["**/*.yaml"],
                    "extraction_rules": [
                        {"path": ".body", "formatter": "json"},
                    ],
                    "enabled": True,
                },
            },
        }

        config = Config.from_dict(data)

        assert config.root is True
        assert config.default_channel == "vcr"
        assert "vcr" in config.channels
        assert len(config.channels["vcr"].extraction_rules) == 1

    def test_to_dict(self) -> None:
        """Test Config.to_dict() serialization."""
        channel = Channel(
            name="test",
            glob_patterns=["*.yaml"],
            extraction_rules=[
                ExtractionRule(path=".body", formatter="json"),
            ],
        )
        config = Config(
            root=True,
            channels={"test": channel},
            default_channel="test",
        )

        result = config.to_dict()

        assert result["root"] is True
        assert result["default_channel"] == "test"
        assert "test" in result["channels"]

    def test_merge_configs(self) -> None:
        """Test Config.merge() combines two configs correctly."""
        base = Config(
            root=False,
            channels={
                "channel1": Channel(name="channel1", glob_patterns=["*.yaml"]),
            },
            default_channel="channel1",
        )

        override = Config(
            root=True,
            channels={
                "channel2": Channel(name="channel2", glob_patterns=["*.json"]),
            },
            default_channel="channel2",
        )

        merged = base.merge(override)

        assert merged.root is True
        assert merged.default_channel == "channel2"
        assert "channel1" in merged.channels
        assert "channel2" in merged.channels

    def test_merge_preserves_base_when_override_empty(self) -> None:
        """Test Config.merge() preserves base when override is minimal."""
        base = Config(
            root=True,
            default_channel="test",
            channels={
                "test": Channel(name="test", glob_patterns=["*.yaml"]),
            },
        )

        override = Config()

        merged = base.merge(override)

        assert merged.root is True
        assert merged.default_channel == "test"
        assert "test" in merged.channels

    def test_round_trip_serialization(self) -> None:
        """Test that from_dict(to_dict()) preserves config data."""
        original = Config(
            root=True,
            default_channel="vcr",
            channels={
                "vcr": Channel(
                    name="vcr",
                    glob_patterns=["**/*.yaml"],
                    extraction_rules=[
                        ExtractionRule(
                            path=".body.string",
                            formatter="text",
                            label="Response",
                            metadata_keys=["status"],
                        ),
                    ],
                ),
            },
        )

        serialized = original.to_dict()
        deserialized = Config.from_dict(serialized)

        assert deserialized.root == original.root
        assert deserialized.default_channel == original.default_channel
        assert set(deserialized.channels.keys()) == set(original.channels.keys())
