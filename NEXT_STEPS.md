# Next Steps

A prioritized roadmap written from the actual state of the tree: ~900 lines of
working code in `src/vcr_tui` (CLI + Textual TUI for previewing VCR cassettes),
one fixture cassette in `fixtures/cassettes/example_api.yaml`, and **zero
tests** — `tests/` contains only empty `__init__.py` files.

## 1. Tests (highest priority)

There is no test coverage at all. Add tests in this order, using the existing
fixture cassette:

- **`preview/yaml_parser.py`** — pure logic, easiest wins: `load_yaml`,
  `get_yaml_keys`, `get_value_at_path` (dict access, list indexing, missing
  keys, the `.` root path).
- **`preview/formatters.py`** — `format_content` for all five formatters
  (`json`, `yaml`, `text`, `html`, `toml`), including the string-with-embedded
  JSON case and malformed input fallbacks.
- **`preview/engine.py`** — `discover_files` against a `tmp_path` tree
  (including `EXCLUDED_DIRS` filtering), `preview_key` / `preview_file` with
  the default `vcr` channel, `_path_matches_rule` edge cases, metadata
  extraction.
- **`config/`** — `Config.from_dict`, `Config.merge`, `load_config` layering
  (defaults → global → local files, `root = true` stopping the upward walk).
- **CLI** — `files`, `keys`, `preview`, `channels` via `click.testing.CliRunner`.
- **UI** — snapshot tests with `pytest-textual-snapshot` (already a dev
  dependency) for `MainScreen` and the four widgets.

Note: `pyproject.toml` configures mypy, not `ty`; align whichever type checker
is actually in use and remove the stale one.

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
- The `tests/` tree has empty `__init__.py` files in directories with no
  tests; keep the structure only as tests are actually added.
- `fixtures/cassettes/example_api.yaml` is used nowhere in the code — make it
  the shared fixture for the test suite (item 1).
- Stray top-level docs (`textual-guide.md`, `textual-quick-reference.md`,
  `gemini-deep-research.txt`, `SKILLS_SUMMARY.md`, `.freshen.md`) duplicate or
  predate the real code; consider pruning.
