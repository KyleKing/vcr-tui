from vcr_tui.config.models import Channel, Config, ExtractionRule


def get_default_config() -> Config:
    return Config(
        root=False,
        channels=(
            Channel(
                name="vcr",
                glob_patterns=(
                    "**/cassettes/*.yaml",
                    "**/cassettes/*.yml",
                    "**/cassettes/**/*.yaml",
                    "**/cassettes/**/*.yml",
                ),
                extraction_rules=(
                    ExtractionRule(
                        path=".interactions[].response.body.string",
                        formatter="json",
                        label="Response Body",
                        metadata_keys=("status.code", "request.method", "request.uri"),
                    ),
                    ExtractionRule(
                        path=".interactions[].request.body.string",
                        formatter="json",
                        label="Request Body",
                        metadata_keys=("request.method", "request.uri"),
                    ),
                ),
            ),
            Channel(
                name="yaml",
                glob_patterns=("**/*.yaml", "**/*.yml"),
                extraction_rules=(
                    ExtractionRule(
                        path=".",
                        formatter="yaml",
                        label="Full YAML",
                    ),
                ),
            ),
        ),
        default_channel="vcr",
    )
