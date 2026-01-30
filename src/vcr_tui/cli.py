from pathlib import Path

import click

from vcr_tui.config import load_config
from vcr_tui.preview import PreviewEngine


@click.group(invoke_without_command=True)
@click.argument(
    "directory",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=".",
)
@click.option("--channel", "-c", help="Channel to use for file matching")
@click.pass_context
def main(ctx: click.Context, directory: Path, channel: str | None) -> None:
    ctx.ensure_object(dict)
    ctx.obj["directory"] = directory.resolve()
    ctx.obj["channel"] = channel
    ctx.obj["config"] = load_config(directory)
    ctx.obj["engine"] = PreviewEngine(ctx.obj["config"])

    if ctx.invoked_subcommand is None:
        _launch_tui(ctx.obj["directory"], ctx.obj["config"], channel)


def _launch_tui(directory: Path, config: "Config", channel: str | None) -> None:
    from vcr_tui.app import VCRTUIApp
    app = VCRTUIApp(directory=directory, config=config, channel=channel)
    app.run()


@main.command()
@click.pass_context
def files(ctx: click.Context) -> None:
    engine: PreviewEngine = ctx.obj["engine"]
    directory: Path = ctx.obj["directory"]
    channel: str | None = ctx.obj["channel"]

    discovered = engine.discover_files(directory, channel)
    for file_path in discovered:
        click.echo(file_path.relative_to(directory))


@main.command()
@click.argument("file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.pass_context
def keys(ctx: click.Context, file: Path) -> None:
    engine: PreviewEngine = ctx.obj["engine"]

    yaml_keys = engine.get_keys(file)
    for key in yaml_keys:
        indent = "  " * key.depth
        click.echo(f"{indent}{key.display}")


@main.command()
@click.argument("file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--key", "-k", help="Specific key path to preview")
@click.pass_context
def preview(ctx: click.Context, file: Path, key: str | None) -> None:
    engine: PreviewEngine = ctx.obj["engine"]
    channel: str | None = ctx.obj["channel"]

    if key:
        result = engine.preview_key(file, key, channel)
    else:
        result = engine.preview_file(file, channel)

    if result.metadata:
        for meta_key, meta_value in result.metadata.items():
            click.echo(f"{meta_key}: {meta_value}", err=True)
        click.echo("---", err=True)

    click.echo(result.content)


@main.command()
@click.pass_context
def channels(ctx: click.Context) -> None:
    config = ctx.obj["config"]

    for channel in config.channels:
        status = "enabled" if channel.enabled else "disabled"
        default = " (default)" if channel.name == config.default_channel else ""
        click.echo(f"{channel.name}: {status}{default}")
        for pattern in channel.glob_patterns:
            click.echo(f"  - {pattern}")


if __name__ == "__main__":
    main()
