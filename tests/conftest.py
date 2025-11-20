"""Shared pytest fixtures for vcr-tui tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from vcr_tui.config.models import Channel, Config, ExtractionRule


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to fixtures directory."""
    return Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def cassettes_dir(fixtures_dir: Path) -> Path:
    """Return path to cassettes fixtures directory."""
    return fixtures_dir / "cassettes"


@pytest.fixture
def configs_dir(fixtures_dir: Path) -> Path:
    """Return path to configs fixtures directory."""
    return fixtures_dir / "configs"


@pytest.fixture
def sample_extraction_rule() -> ExtractionRule:
    """Return a sample ExtractionRule for testing."""
    return ExtractionRule(
        path=".body.string",
        formatter="text",
        label="Response Body",
        metadata_keys=["status", "method"],
    )


@pytest.fixture
def sample_channel(sample_extraction_rule: ExtractionRule) -> Channel:
    """Return a sample Channel for testing."""
    return Channel(
        name="test_channel",
        glob_patterns=["**/*.yaml"],
        extraction_rules=[sample_extraction_rule],
        enabled=True,
    )


@pytest.fixture
def sample_config(sample_channel: Channel) -> Config:
    """Return a sample Config for testing."""
    return Config(
        root=False,
        channels={"test_channel": sample_channel},
        default_channel="test_channel",
    )
