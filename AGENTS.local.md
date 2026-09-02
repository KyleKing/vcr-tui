# vcr-tui project guidance (loaded by template-owned AGENTS.md)

## What this is

`vcr-tui` — a Textual TUI plus a Click CLI for previewing VCR cassettes
(YAML) and other machine-generated files. Python 3.11+, src layout
(`src/vcr_tui/`), packaged with the uv build backend.

## Layout

- `src/vcr_tui/cli.py` — Click CLI (`vcr-tui [dir]`, subcommands `files`,
  `keys`, `preview`, `channels`); `app.py` — the Textual `App`.
- `src/vcr_tui/config/` — TOML config: defaults, dataclass models,
  layered loader (defaults → global in platformdirs config dir → `vcr-tui.toml`
  found walking up from the start directory, `root = true` stops the walk).
- `src/vcr_tui/preview/` — the core, UI-free logic: YAML parsing/key
  extraction (`yaml_parser.py`), formatters (`json`/`yaml`/`text`/`html`/`toml`),
  and `PreviewEngine` (file discovery + extraction rules per "channel").
- `src/vcr_tui/ui/` — Textual screen and widgets; styles in
  `ui/styles/app.tcss`.
- `tests/` — mirrors the package layout; `fixtures/cassettes/` holds a sample
  cassette.
- `NEXT_STEPS.md` — current roadmap.

## Working here

Use [uv](https://docs.astral.sh/uv/):

```bash
uv sync --dev   # set up env with dev deps
uv run vcr-tui  # run the app
uv run vcr-tui files  # CLI subcommands
```

Always reach a tool through `uv run`, never through `.venv/bin/…`.

Checks (run via `uv run`):

- **ruff** — lint, line length 100, py311 target:
  `uv run ruff check .`
- **ty** — type checking: `uv run ty check src`
- **pytest** — tests, asyncio auto mode: `uv run pytest`

Keep `src/vcr_tui/preview/` free of UI imports — it is the testable core.
The TUI (`ui/`) should only consume it.
