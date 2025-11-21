"""Default configuration for vcr-tui."""

from __future__ import annotations

from vcr_tui.config.models import Channel, Config, ExtractionRule


def get_default_config() -> Config:
    """Return the built-in default configuration.

    Provides two built-in channels:
    - vcr: Optimized for VCR cassette inspection with body extraction
    - yaml: General YAML file viewing

    Returns:
        Config with default channels
    """
    vcr_channel = Channel(
        name="vcr",
        glob_patterns=["**/*.yaml", "**/*.yml"],
        extraction_rules=[
            ExtractionRule(
                path="interactions[].response.body.string",
                formatter="text",
                label="Response Body (Text)",
                metadata_keys=[],
            ),
            ExtractionRule(
                path="interactions[].response.body.string",
                formatter="json",
                label="Response Body (JSON)",
                metadata_keys=[],
            ),
            ExtractionRule(
                path="interactions[].request.body",
                formatter="text",
                label="Request Body",
                metadata_keys=[],
            ),
        ],
        enabled=True,
    )

    yaml_channel = Channel(
        name="yaml",
        glob_patterns=["**/*.yaml", "**/*.yml"],
        extraction_rules=[
            ExtractionRule(
                path=".",
                formatter="yaml",
                label="Full YAML",
                metadata_keys=[],
            ),
        ],
        enabled=True,
    )

    return Config(
        root=False,
        channels={
            "vcr": vcr_channel,
            "yaml": yaml_channel,
        },
        default_channel="vcr",
    )
