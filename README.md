# vcr-tui

TUI for previewing VCR cassettes and machine-generated files

`vcr-tui` is a [Textual](https://textual.textualize.io/) TUI plus a
[Click](https://click.palletsprojects.com/) CLI for browsing and previewing VCR
cassettes (YAML) and other machine-generated files.

Documentation can be found on [GitHub (./docs)](./docs), [PyPi](https://pypi.org/project/vcr_tui/), or [Hosted](https://vcr-tui.kyleking.me/)!

## Installation

Requires Python 3.11+.

```sh
uv tool install vcr-tui
# or: pipx install vcr-tui
```

## Usage

Launch the interactive TUI for a directory of cassettes:

```sh
vcr-tui path/to/cassettes
```

Or use the CLI subcommands for quick inspection without the TUI:

```sh
vcr-tui files                    # list discoverable cassette files
vcr-tui keys cassette.yaml       # print the YAML key structure
vcr-tui preview cassette.yaml    # render a formatted preview
vcr-tui channels                 # list configured preview channels
```

Configuration is layered TOML: built-in defaults → global config in your
platform config dir → a `vcr-tui.toml` found walking up from the start
directory (`root = true` stops the walk).

For more example code, see the [scripts] directory or the [tests].

## Project Status

See the `Open Issues` and/or the [CODE_TAG_SUMMARY]. For release history, see the [CHANGELOG].

## Contributing

Pull requests are welcome! See the [developer guide][developer_guide] and [style guide][style_guide]. By contributing, you agree to release your contributions under the [license].

## Contact

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

