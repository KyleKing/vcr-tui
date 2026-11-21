# Copyright (c) 2026 Kyle King
# SPDX-License-Identifier: MIT
"""Command-line entry points for the VCR-TUI tool."""

import json
from pathlib import Path

import click

from vcr_tui.app import VCRTUIApp
from vcr_tui.config import load_config
from vcr_tui.config.models import Config
from vcr_tui.preview import PreviewEngine
from vcr_tui.preview.audit import (
    DEFAULT_MAX_BODY_BYTES,
    AuditOptions,
    audit as run_audit,
    render_report,
    report_to_dict,
)
from vcr_tui.preview.cassette import format_row, render_text


@click.group(invoke_without_command=True)
@click.argument(
    'directory',
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default='.',
)
@click.option('--channel', '-c', help='Channel to use for file matching')
@click.pass_context
def main(ctx: click.Context, directory: Path, channel: str | None) -> None:
    """Load config for the directory and launch the TUI when no subcommand runs."""
    ctx.ensure_object(dict)
    ctx.obj['directory'] = directory.resolve()
    ctx.obj['channel'] = channel
    ctx.obj['config'] = load_config(directory)
    ctx.obj['engine'] = PreviewEngine(ctx.obj['config'])

    if ctx.invoked_subcommand is None:
        _launch_tui(ctx.obj['directory'], ctx.obj['config'], channel)


def _launch_tui(directory: Path, config: Config, channel: str | None) -> None:
    app = VCRTUIApp(directory=directory, config=config, channel=channel)
    app.run()


@main.command()
@click.pass_context
def files(ctx: click.Context) -> None:
    """Print each discovered cassette file relative to the directory."""
    engine: PreviewEngine = ctx.obj['engine']
    directory: Path = ctx.obj['directory']
    channel: str | None = ctx.obj['channel']

    discovered = engine.discover_files(directory, channel)
    for file_path in discovered:
        click.echo(file_path.relative_to(directory))


@main.command()
@click.argument('file', type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.pass_context
def keys(ctx: click.Context, file: Path) -> None:
    """Print the selectable keys of a file as an indented tree."""
    engine: PreviewEngine = ctx.obj['engine']

    yaml_keys = engine.get_keys(file)
    for key in yaml_keys:
        indent = '  ' * key.depth
        click.echo(f'{indent}{key.display}')


@main.command()
@click.argument('file', type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option('--key', '-k', help='Specific key path to preview')
@click.pass_context
def preview(ctx: click.Context, file: Path, key: str | None) -> None:
    """Print the formatted preview of a file or one of its keys."""
    engine: PreviewEngine = ctx.obj['engine']
    channel: str | None = ctx.obj['channel']

    result = engine.preview_key(file, key, channel) if key else engine.preview_file(file, channel)

    if result.metadata:
        for meta_key, meta_value in result.metadata.items():
            click.echo(f'{meta_key}: {meta_value}', err=True)
        click.echo('---', err=True)

    click.echo(result.content)


@main.command()
@click.argument('file', type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    '--index',
    '-i',
    type=int,
    help='Print the full request and response of the interaction at this index',
)
@click.pass_context
def interactions(ctx: click.Context, file: Path, index: int | None) -> None:
    """List a cassette's recorded HTTP interactions, or show one in full."""
    engine: PreviewEngine = ctx.obj['engine']

    found = engine.get_interactions(file)
    if found is None:
        msg = f'{file} is not a VCR cassette'
        raise click.ClickException(msg)

    if index is None:
        for interaction in found:
            click.echo(format_row(interaction))
        return

    match = next((i for i in found if i.index == index), None)
    if match is None:
        msg = f'no interaction {index} in {file} ({len(found)} recorded)'
        raise click.ClickException(msg)
    click.echo(render_text(match))


@main.command()
@click.option(
    '--format',
    'output_format',
    type=click.Choice(['text', 'json']),
    default='text',
    show_default=True,
    help='Report format',
)
@click.option(
    '--fail-on',
    type=click.Choice(['error', 'warning', 'info', 'never']),
    default='error',
    show_default=True,
    help='Exit 1 when any finding is at or above this severity',
)
@click.option(
    '--skip',
    multiple=True,
    metavar='CODE',
    help='Finding code to ignore, e.g. email or no-test (repeatable)',
)
@click.option(
    '--max-body',
    type=int,
    default=DEFAULT_MAX_BODY_BYTES,
    show_default=True,
    help='Flag response bodies larger than this many bytes',
)
@click.pass_context
def audit(
    ctx: click.Context,
    output_format: str,
    fail_on: str,
    skip: tuple[str, ...],
    max_body: int,
) -> None:
    """Summarize every cassette under the directory and flag what needs review.

    Reports hosts, endpoints by status code, and findings: unredacted secrets
    (errors), cookies, oversized bodies, empty or unreadable cassettes, and
    cassettes whose test no longer exists (warnings), plus duplicates, recorded
    5xx responses, and email addresses (info).
    """
    engine: PreviewEngine = ctx.obj['engine']
    directory: Path = ctx.obj['directory']
    channel: str | None = ctx.obj['channel']

    cassettes, unreadable = engine.load_cassettes(directory, channel)
    options = AuditOptions(max_body_bytes=max_body, skip=frozenset(skip))
    report = run_audit(cassettes, options, unreadable)

    if output_format == 'json':
        click.echo(json.dumps(report_to_dict(report, directory), indent=2))
    else:
        click.echo(render_report(report, directory))

    if report.failed(fail_on):
        ctx.exit(1)


@main.command()
@click.pass_context
def channels(ctx: click.Context) -> None:
    """Print the configured channels, their status, and their patterns."""
    config = ctx.obj['config']

    for channel in config.channels:
        status = 'enabled' if channel.enabled else 'disabled'
        default = ' (default)' if channel.name == config.default_channel else ''
        click.echo(f'{channel.name}: {status}{default}')
        for pattern in channel.glob_patterns:
            click.echo(f'  - {pattern}')


if __name__ == '__main__':
    main()
