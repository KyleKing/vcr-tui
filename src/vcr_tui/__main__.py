"""VCR-TUI command-line entry point."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from vcr_tui.app import run_tui


@click.command()
@click.option(
    "--directory",
    "-d",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Directory to search for files (default: current directory)",
)
@click.option(
    "--channel",
    "-c",
    type=str,
    default=None,
    help="Channel to use for file discovery and extraction",
)
@click.version_option(package_name="vcr-tui")
def main(directory: Path | None, channel: str | None) -> None:
    """VCR-TUI: Terminal UI for previewing VCR cassettes and YAML files.

    Browse and preview VCR cassette files and other structured YAML files
    with a beautiful terminal user interface.

    \b
    Examples:
      # Launch TUI in current directory
      vcr-tui

      # Launch TUI in specific directory
      vcr-tui --directory ./fixtures/cassettes

      # Use a specific channel
      vcr-tui --channel vcr

    \b
    Keyboard Shortcuts:
      Tab/Shift+Tab  - Cycle focus between widgets
      ↑/↓ or j/k     - Navigate items
      Enter          - Select item
      ?              - Show help
      q              - Quit
    """
    try:
        run_tui(directory=directory, channel=channel)
    except KeyboardInterrupt:
        click.echo("\nExiting...", err=True)
        sys.exit(0)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
