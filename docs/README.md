# vcr-tui

TUI for previewing VCR cassettes and machine-generated files

`vcr-tui` is a [Textual](https://textual.textualize.io/) TUI plus a
[Click](https://click.palletsprojects.com/) CLI for browsing and previewing VCR
cassettes (YAML) and other machine-generated files.

## Installation

Requires Python 3.11+. Install with [uv](https://docs.astral.sh/uv/):

```sh
uv tool install vcr-tui
```

Within a project already managed by uv, add it as a dependency instead:

```sh
uv add vcr-tui
```

## Usage

Open the TUI on a directory of cassettes:

```sh
vcr-tui path/to/cassettes
```

Inside it, `j`/`k` and the arrow keys move, `tab` cycles panes, `/` filters
the focused pane, `c` switches channel, `r` rescans the directory, and `q`
quits.

The same directory is browsable from the shell. `files` lists what the active
channel matches, `keys` lists the key paths inside one file, `preview` renders
a file or a single key, and `channels` lists what is configured. `FILE` is a
path from the current directory rather than from `DIRECTORY`:

```sh
vcr-tui path/to/cassettes files
vcr-tui path/to/cassettes keys path/to/cassettes/example_api.yaml
vcr-tui path/to/cassettes preview path/to/cassettes/example_api.yaml \
  -k 'interactions[0].response.body.string'
vcr-tui path/to/cassettes channels
```

A JSON payload stored as a YAML string is expanded in place rather than shown
escaped, which is the reason this exists:

```yaml
response:
  body:
    string:
      id: 1
      name: John Doe
```

For more example code, see the [scripts] directory or the [tests].

## Project Status

See the `Open Issues` and/or the [CODE_TAG_SUMMARY]. For release history, see the [CHANGELOG].

## Contributing

We welcome pull requests! For your pull request to be accepted smoothly, we suggest that you first open a GitHub issue to discuss your idea. For resources on getting started with the code base, see the below documentation:

- [DEVELOPER_GUIDE]
- [STYLE_GUIDE]

## Code of Conduct

We follow the [Contributor Covenant Code of Conduct][contributor-covenant].

### Open Source Status

We try to reasonably meet most aspects of the "OpenSSF scorecard" from [Open Source Insights](https://deps.dev/pypi/vcr-tui)

## Responsible Disclosure

If you have any security issue to report, please contact the project maintainers privately. You can reach us at [dev.act.kyle@gmail.com](mailto:dev.act.kyle@gmail.com).

## License

[LICENSE]

[changelog]: https://vcr-tui.kyleking.me/docs/CHANGELOG
[code_tag_summary]: https://vcr-tui.kyleking.me/docs/CODE_TAG_SUMMARY
[contributor-covenant]: https://www.contributor-covenant.org
[developer_guide]: https://vcr-tui.kyleking.me/docs/DEVELOPER_GUIDE
[license]: https://github.com/kyleking/vcr-tui/blob/main/LICENSE
[scripts]: https://github.com/kyleking/vcr-tui/blob/main/scripts
[style_guide]: https://vcr-tui.kyleking.me/docs/STYLE_GUIDE
[tests]: https://github.com/kyleking/vcr-tui/blob/main/tests
