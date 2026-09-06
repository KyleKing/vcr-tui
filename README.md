# vcr-tui

TUI for previewing VCR cassettes and machine-generated files, but you probably want to
use one of these primarily open-source applications instead:

| Service                                                         | Notes                                                                                                                         |
| --------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| [betamax](https://github.com/betamaxpy/betamax)                 | "A VCR imitation designed only for python-requests."                                                                          |
| [Charles Proxy](https://www.charlesproxy.com/)                  | "Web Debugging Proxy Application for Windows, Mac OS and Linux" (Closed source)                                               |
| [chromeHAR](https://github.com/ericduran/chromeHAR)             | "HAR viewer that mimics (or at least tries really hard to) Chromes network tab"                                               |
| [dasel](https://github.com/TomWright/dasel)                     | "Unified querying, transformation, and modification of JSON, TOML, YAML, XML, INI, HCL, KDL and CSV."                         |
| [fx](https://github.com/antonmedv/fx)                           | "Terminal JSON viewer & processor"                                                                                            |
| [gron](https://github.com/tomnomnom/gron)                       | "Make JSON greppable!"                                                                                                        |
| [Insomnia](https://github.com/Kong/insomnia)                    | "The open-source, cross-platform API client for GraphQL, REST, WebSockets, SSE and gRPC. With Cloud, Local and Git storage."  |
| [jless](https://github.com/PaulJuliusMartinez/jless)            | "jless is a command-line JSON viewer designed for reading, exploring, and searching through JSON data."                       |
| [jnv](https://github.com/ynqa/jnv)                              | "Interactive JSON filter using jq"                                                                                            |
| [jq](https://github.com/jqlang/jq)                              | "Command-line JSON processor"                                                                                                 |
| [mitmproxy](https://github.com/mitmproxy/mitmproxy)             | "An interactive TLS-capable intercepting HTTP proxy for penetration testers and software developers."                         |
| [Mockoon](https://github.com/mockoon/mockoon)                   | "Mockoon is the easiest and quickest way to run mock APIs locally. No remote deployment, no account required, open source."   |
| [Polly.js](https://github.com/Netflix/pollyjs)                  | "Record, Replay, and Stub HTTP Interactions."                                                                                 |
| [Proxyman](https://proxyman.com/)                               | "Best-in-class HTTP debugging proxy built for developers. Fast, modern, and delightful." (Closed source)                      |
| [pytest-recording](https://github.com/kiwicom/pytest-recording) | "A pytest plugin powered by VCR.py to record and replay HTTP traffic."                                                        |
| [VCR (Ruby)](https://github.com/vcr/vcr)                        | "Record your test suite's HTTP interactions and replay them during future test runs for fast, deterministic, accurate tests." |
| [vcrpy](https://github.com/kevin1024/vcrpy)                     | "Automatically mock your HTTP interactions to simplify and speed up testing"                                                  |
| [WireMock](https://github.com/wiremock/wiremock)                | "WireMock is the industry standard for scalable API simulation."                                                              |
| [yq](https://github.com/mikefarah/yq)                           | "yq is a portable command-line YAML, JSON, XML, CSV, TOML, HCL and properties processor"                                      |

`vcr-tui` is a [Textual](https://textual.textualize.io/) TUI plus a
[Click](https://click.palletsprojects.com/) CLI for browsing and previewing VCR
cassettes (YAML) and other machine-generated files.

Documentation can be found on [GitHub (./docs)](./docs),
[PyPi](https://pypi.org/project/vcr_tui/), or [Hosted](https://vcr-tui.kyleking.me/)!

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

See the `Open Issues` and/or the [CODE_TAG_SUMMARY].
For release history, see the [CHANGELOG].

## Contributing

Pull requests are welcome! See the [developer guide][developer_guide] and
[style guide][style_guide].
By contributing, you agree to release your contributions under the [license].

## Contact

If you have any security issue to report, please contact the project maintainers
privately.
You can reach us at [dev.act.kyle@gmail.com](mailto:dev.act.kyle@gmail.com).

## License

[LICENSE]

[changelog]: https://vcr-tui.kyleking.me/docs/CHANGELOG
[code_tag_summary]: https://vcr-tui.kyleking.me/docs/CODE_TAG_SUMMARY
[developer_guide]: https://vcr-tui.kyleking.me/docs/DEVELOPER_GUIDE
[license]: https://github.com/kyleking/vcr-tui/blob/main/LICENSE
[scripts]: https://github.com/kyleking/vcr-tui/blob/main/scripts
[style_guide]: https://vcr-tui.kyleking.me/docs/STYLE_GUIDE
[tests]: https://github.com/kyleking/vcr-tui/blob/main/tests
