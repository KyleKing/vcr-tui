# Next Steps

A prioritized roadmap written from the actual state of the tree: ~900 lines of
working code in `src/vcr_tui` (CLI + Textual TUI for previewing VCR cassettes),
one fixture cassette in `fixtures/cassettes/example_api.yaml`, and 56 passing
tests covering `preview/formatters.py` and `preview/yaml_parser.py` only.

## 0. Template adoption follow-ups

The calcipy_template was adopted (`.copier-answers.yml`, `./run` task runner,
mkdocs docs, pre-commit, nox, commitizen, uv build backend with `src/` layout).
Still open from that migration:

- `docs/README.md` still carries the template's placeholder text (`poetry add
  vcr_tui`, TODO example) while root `README.md` is real — rewrite the docs
  copy to match.
- `pyproject.toml` carries both a `[tool.mypy]` config and the project's `ty`
  type checker; align on one and remove the stale config.
- ~~Decide whether gates run via `./run main` (calcipy tasks) or direct
  `uv run ruff/ty/pytest`~~ — decided: gates are `uv run ruff check .`,
  `uv run ty check src`, and `uv run pytest` (see AGENTS.local.md). `./run`
  stays as the calcipy convenience wrapper until this project adopts the
  calcipy ruff standard; revisit only then.
- Ruff currently uses this project's narrow `select` list; migrating to the
  calcipy `select = ['ALL']` standard is ~155 fixes, mostly docstrings.

## 1. Tests

Covered so far: `preview/formatters.py` (`test_formatters.py`) and
`preview/yaml_parser.py` (`test_yaml_parser.py`) — 56 tests plus the
template's version smoke test. Still to write, in this order, using the
existing fixture cassette:

- **`preview/engine.py`** — `discover_files` against a `tmp_path` tree
  (including `EXCLUDED_DIRS` filtering), `preview_key` / `preview_file` with
  the default `vcr` channel, `_path_matches_rule` edge cases, metadata
  extraction.
- **`config/`** — `Config.from_dict`, `Config.merge`, `load_config` layering
  (defaults → global → local files, `root = true` stopping the upward walk).
- **CLI** — `files`, `keys`, `preview`, `channels` via `click.testing.CliRunner`.
- **UI** — snapshot tests with `pytest-textual-snapshot` (already a dev
  dependency) for `MainScreen` and the four widgets. `tests/test_ui`,
  `tests/integration`, and `tests/test_config` currently hold only empty
  `__init__.py` files.

## 2. Real bugs and rough edges found in the code

- `engine.discover_files` runs `directory.rglob("*")` once **per glob
  pattern** — a full tree walk per pattern. Walk once, then match all patterns.
- `_normalize_path` is a no-op: `re.sub(r"\[(\d+)\]", r"[\1]", path)` replaces
  text with itself.
- `format_content` has an unreachable `case _:` fallback on a `Literal` type;
  either narrow it or make it a real error path.
- `_format_text` unconditionally strips `\r`; real carriage returns in content
  are lost.
- `Config.merge` replaces nothing for existing channels — a local config cannot
  override a channel defined in a global one, only add new ones. Confirm this
  is intended and document it, or implement per-channel override.
- `preview_file` ignores all but `extraction_rules[0]` of a channel and returns
  empty metadata; a file-level preview could run the rule end-to-end for
  interaction 0 instead.
- `main_screen._load_files` does discovery and YAML parsing synchronously on
  the UI thread; large cassette directories will stutter. Move to workers.

## 3. TUI functionality gaps

- No channel switching in the UI (the `--channel` flag exists on the CLI but
  there is no keybinding/screen to change it live).
- No search/filtering in the file list or YAML key viewer.
- No reload (e.g. `r` to re-scan the directory) — the file list is built once
  at mount.
- README documents `j`/`k` navigation; verify the widgets actually implement
  it and keep the docs in sync.

## 4. Housekeeping

- `src/vcr_tui/utils/` is an empty package — delete or use it.
- Stray empty `__init__.py` files in `tests/test_ui`, `tests/test_config`,
  `tests/integration` (directories with no tests); keep the structure only as
  tests are actually added.
- `fixtures/cassettes/example_api.yaml` is used nowhere in the code — make it
  the shared fixture for the test suite.
- Stray top-level docs (`textual-guide.md`, `textual-quick-reference.md`,
  `gemini-deep-research.txt`, `SKILLS_SUMMARY.md`, `.freshen.md`) duplicate or
  predate the real code; consider pruning.
