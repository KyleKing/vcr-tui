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

- ~~`engine.discover_files` runs `directory.rglob("*")` once per glob
  pattern~~ — done: one walk, every pattern matched against each path.
- ~~`_normalize_path` is a no-op~~ — deleted; `_path_matches_rule` already
  handled the `[]` wildcard through its `startswith` branch.
- ~~`format_content` has an unreachable `case _:` fallback~~ — it is
  `assert_never(formatter)`, which is the real error path already.
- `_format_text` translates the literal `\n` and `\t` escapes and drops a
  literal `\r`, so a CRLF body renders as LF. Real carriage returns are not
  affected (this entry used to claim they were). Left as is: a CR in a preview
  pane moves the cursor rather than showing anything.
- ~~`Config.merge` replaces nothing for existing channels~~ — done: a
  same-named channel in the later layer replaces the earlier one in place,
  matching how `root` and `default_channel` already resolved.
- `preview_file` ignores all but `extraction_rules[0]` of a channel and returns
  empty metadata; a file-level preview could run the rule end-to-end for
  interaction 0 instead.
- ~~`main_screen._load_files` does discovery synchronously on the UI
  thread~~ — done: a `@work(thread=True, exclusive=True)` worker posts
  `FilesDiscovered` back to the screen for the widget updates.

## 3. TUI functionality gaps

- ~~No channel switching in the UI~~ — done: `c` cycles the enabled channels
  and the header carries the active one.
- ~~No search/filtering in the file list~~ — done: `/` focuses a filter input
  over the list, escape clears it. The YAML key viewer still has none.
- ~~No reload~~ — done: `r` re-runs discovery and keeps the selection when
  the file survives.
- README documents `j`/`k` navigation; verify the widgets actually implement
  it and keep the docs in sync.

## 4. Housekeeping

- `src/vcr_tui/utils/` is an empty package — delete or use it.
- Stray empty `__init__.py` files in `tests/test_ui`, `tests/test_config`,
  `tests/integration` (directories with no tests); keep the structure only as
  tests are actually added.
- `fixtures/cassettes/example_api.yaml` is used nowhere in the code — make it
  the shared fixture for the test suite.
- ~~Stray top-level docs~~ — done. `textual-guide.md` replaced the truncated
  `.claude/skills/textual/guide.md` and both root copies went, since the
  quick reference was byte-identical to the skill's; `SKILLS_SUMMARY.md`
  moved to `.claude/skills/SUMMARY.md`; `gemini-deep-research.txt` went, as
  the pipeline it recommends is what `preview/` implements. `.freshen.md`
  stays: it is a running session log rather than a duplicate doc.
