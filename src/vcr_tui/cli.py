"""Command-line interface for vcr-tui preview engine."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from vcr_tui.config.loader import load_config
from vcr_tui.preview.engine import PreviewEngine


@click.group()
@click.version_option(package_name="vcr-tui")
def main() -> None:
    """VCR-TUI: Terminal UI for previewing VCR cassettes and structured data files."""
    pass


@main.command()
@click.argument(
    "directory",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=".",
)
@click.option(
    "--channel",
    "-c",
    help="Channel to use for file discovery",
)
def discover(directory: Path, channel: str | None) -> None:
    """Discover files matching channel's glob patterns.

    \b
    Examples:
        vcr-tui discover
        vcr-tui discover ./fixtures/cassettes
        vcr-tui discover -c vcr
    """
    config = load_config(directory)
    engine = PreviewEngine(config)

    files = engine.discover_files(directory, channel)

    if not files:
        click.echo("No files found", err=True)
        sys.exit(1)

    click.echo(f"Found {len(files)} file(s):")
    for file in files:
        click.echo(f"  {file}")


@main.command()
@click.argument(
    "file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--channel",
    "-c",
    help="Channel to use for extraction rules",
)
def keys(file: Path, channel: str | None) -> None:
    """List all keys in a YAML file.

    \b
    Examples:
        vcr-tui keys cassette.yaml
        vcr-tui keys cassette.yaml -c vcr
    """
    config = load_config(file.parent)
    engine = PreviewEngine(config)

    try:
        all_keys = engine.get_yaml_keys(file)
    except (FileNotFoundError, ValueError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    if not all_keys:
        click.echo("No keys found in file", err=True)
        sys.exit(1)

    click.echo(f"Keys in {file.name}:")
    for key in all_keys:
        click.echo(f"  {key}")


@main.command()
@click.argument(
    "file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--channel",
    "-c",
    help="Channel to use for extraction rules",
)
def previewable(file: Path, channel: str | None) -> None:
    """List previewable keys (keys with matching extraction rules).

    \b
    Examples:
        vcr-tui previewable cassette.yaml
        vcr-tui previewable cassette.yaml -c vcr
    """
    config = load_config(file.parent)
    engine = PreviewEngine(config)

    try:
        preview_keys = engine.get_previewable_keys(file, channel)
    except (FileNotFoundError, ValueError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    if not preview_keys:
        click.echo("No previewable keys found", err=True)
        sys.exit(1)

    click.echo(f"Previewable keys in {file.name}:")
    for key in preview_keys:
        click.echo(f"  {key}")


@main.command()
@click.argument(
    "file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.argument("key")
@click.option(
    "--channel",
    "-c",
    help="Channel to use for extraction rules",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["content", "metadata", "all"], case_sensitive=False),
    default="content",
    help="Output format (content, metadata, or all)",
)
def preview(
    file: Path,
    key: str,
    channel: str | None,
    output_format: str,
) -> None:
    """Preview a specific key from a YAML file.

    \b
    Examples:
        vcr-tui preview cassette.yaml "interactions[0].response.body.string"
        vcr-tui preview cassette.yaml "interactions[0].response.body.string" -c vcr
        vcr-tui preview cassette.yaml "interactions[0].response.body.string" -f all
    """
    config = load_config(file.parent)
    engine = PreviewEngine(config)

    try:
        result = engine.preview_key(file, key, channel)
    except (FileNotFoundError, ValueError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    if not result:
        click.echo(f"No preview available for key: {key}", err=True)
        click.echo(
            "Key may not match any extraction rules. Try 'previewable' command.",
            err=True,
        )
        sys.exit(1)

    # Output based on format choice
    if output_format == "metadata":
        if result.metadata:
            click.echo("Metadata:")
            for k, v in result.metadata.items():
                click.echo(f"  {k}: {v}")
        else:
            click.echo("No metadata available")
    elif output_format == "all":
        if result.label:
            click.echo(f"Label: {result.label}")
        click.echo(f"Formatter: {result.formatter}")
        click.echo(f"Source Path: {result.source_path}")
        if result.metadata:
            click.echo("\nMetadata:")
            for k, v in result.metadata.items():
                click.echo(f"  {k}: {v}")
        click.echo("\nContent:")
        click.echo(result.content)
    else:  # content
        click.echo(result.content)


if __name__ == "__main__":
    main()
