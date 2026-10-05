# vcr-tui

A beautiful terminal user interface for previewing [VCR](https://github.com/vcr/vcr) cassettes and other structured YAML files.

> **Browse VCR cassettes with ease**: Navigate files, inspect YAML structure, and preview formatted content — all in your terminal.

## Features

✨ **Intuitive TUI** - Clean, keyboard-driven interface built with [Textual](https://textual.textualize.io/)
🗂️ **File Browser** - Navigate VCR cassettes and YAML files in any directory
🌳 **Hierarchical View** - Explore YAML structure as an expandable tree
🎨 **Syntax Highlighting** - Pretty-printed JSON, YAML, HTML with Rich
⚙️ **Configurable** - Define custom channels and extraction rules
📊 **Live Metadata** - See file info, key paths, and content size in real-time
⌨️ **Vim Bindings** - Navigate with j/k, plus standard arrow keys
❓ **Built-in Help** - Press `?` for keyboard shortcuts

## Installation

```bash
# From PyPI (when published)
pip install vcr-tui

# From source
git clone https://github.com/KyleKing/vcr-tui
cd vcr-tui
pip install -e ".[dev]"
```

## Quick Start

### TUI Mode (Interactive)

Launch the terminal UI:

```bash
# Browse current directory
vcr-tui

# Browse specific directory
vcr-tui --directory ./fixtures/cassettes

# Use specific channel
vcr-tui --channel vcr
```

**Keyboard Shortcuts:**
- `Tab/Shift+Tab` - Cycle focus between widgets
- `↑/↓` or `j/k` - Navigate items
- `Enter` - Select file/key
- `Space` - Toggle tree expand/collapse
- `?` - Show help
- `q` - Quit

### CLI Mode (Scripting)

Use the command-line interface for automation:

```bash
# Discover files
vcr-tui-cli discover --directory ./fixtures

# List keys in a file
vcr-tui-cli keys cassette.yaml

# Preview specific key
vcr-tui-cli preview cassette.yaml "interactions[0].response.body.string"

# List previewable keys
vcr-tui-cli previewable cassette.yaml
```

## Configuration

VCR-TUI uses a hierarchical configuration system with TOML files.

### Configuration Files

Configuration is loaded from (in order):
1. **Global**: `~/.config/vcr-tui/config.toml` (or platform-specific config dir)
2. **Local**: `vcr-tui.toml` or `.vcr-tui.toml` in current directory
3. **Parent**: Walks up directory tree until `root = true` or filesystem root

### Default Channels

**VCR Channel** - For VCR cassette files:
```toml
[channels.vcr]
glob_patterns = ["**/*.yaml", "**/*.yml"]
enabled = true

[[channels.vcr.extraction_rules]]
path = "interactions[].response.body.string"
formatter = "text"
label = "Response Body (Text)"

[[channels.vcr.extraction_rules]]
path = "interactions[].response.body.string"
formatter = "json"
label = "Response Body (JSON)"
```

**YAML Channel** - For generic YAML files:
```toml
[channels.yaml]
glob_patterns = ["**/*.yaml", "**/*.yml"]
enabled = true

[[channels.yaml.extraction_rules]]
path = "data"
formatter = "yaml"
```

### Custom Configuration Example

Create `.vcr-tui.toml` in your project:

```toml
# Stop searching parent directories
root = true

# Set default channel
default_channel = "api"

# Custom channel for API responses
[channels.api]
glob_patterns = ["**/responses/*.json"]
enabled = true

[[channels.api.extraction_rules]]
path = "body"
formatter = "json"
label = "API Response"
metadata_keys = ["status", "headers.content-type"]

[[channels.api.extraction_rules]]
path = "error"
formatter = "text"
label = "Error Message"
```

### Extraction Rules

Extraction rules use path expressions to locate data in YAML:

- **Nested keys**: `user.address.city`
- **Array indices**: `items[0].id`
- **Array iteration**: `items[].name` (extracts all names)
- **Complex paths**: `interactions[].response.body.string`

**Supported Formatters:**
- `json` - Pretty-printed JSON
- `yaml` - Formatted YAML
- `text` - Plain text with escape sequences decoded
- `html` - HTML with entities decoded
- `toml` - TOML formatting

## Architecture

VCR-TUI is built with a clean, layered architecture:

```
┌─────────────────────────────────────┐
│  TUI (Textual)   │   CLI (Click)    │
├─────────────────────────────────────┤
│         Preview Engine              │
├─────────────────────────────────────┤
│  YAML Parser  │  Extractors  │ Fmt  │
├─────────────────────────────────────┤
│        Configuration System         │
└─────────────────────────────────────┘
```

**Key Components:**
- **Config System**: Hierarchical TOML configuration with channel management
- **Preview Engine**: Discovers files, extracts keys, formats content
- **YAML Parser**: Navigates nested YAML structures with ruamel.yaml
- **Extractors**: Path-based extraction with array iteration support
- **Formatters**: Syntax highlighting and format conversion
- **UI Widgets**: FileList, YAMLViewer (Tree), PreviewPanel (Rich)

## Development

### Running Tests

```bash
# All tests (332 tests, 80%+ coverage)
pytest

# Specific module
pytest tests/test_ui/

# With coverage report
pytest --cov --cov-report=html

# Watch mode
pytest-watch
```

### Code Quality

```bash
# Type checking
mypy src/

# Linting
ruff check .

# Auto-fix
ruff check --fix .

# Format
ruff format .
```

### Project Structure

```
vcr-tui/
├── src/vcr_tui/
│   ├── __main__.py          # TUI entry point
│   ├── cli.py               # CLI commands
│   ├── app.py               # Main TUI application
│   ├── config/              # Configuration system
│   │   ├── models.py        # Data classes
│   │   ├── defaults.py      # Built-in channels
│   │   └── loader.py        # Config loading
│   ├── preview/             # Preview engine
│   │   ├── yaml_parser.py   # YAML navigation
│   │   ├── extractors.py    # Path extraction
│   │   ├── formatters.py    # Content formatting
│   │   └── engine.py        # Core engine
│   └── ui/                  # TUI widgets
│       ├── file_list.py     # File browser
│       ├── yaml_viewer.py   # Tree viewer
│       └── preview_panel.py # Content display
├── tests/                   # 332 tests
│   ├── test_config/         # Config tests (63)
│   ├── test_preview/        # Engine tests (161)
│   ├── test_ui/             # Widget tests (81)
│   └── test_cli.py          # CLI tests (27)
├── fixtures/                # Test fixtures
│   ├── cassettes/           # Sample VCR cassettes
│   └── configs/             # Sample configs
└── pyproject.toml           # Project config
```

## Use Cases

### VCR Cassette Inspection
Quickly browse and verify HTTP interactions recorded by VCR during testing.

### API Response Debugging
Inspect JSON/YAML API responses with syntax highlighting and easy navigation.

### Configuration File Review
Navigate complex YAML configuration files with hierarchical tree view.

### Test Data Analysis
Examine test fixtures and recorded responses without opening multiple files.

## Roadmap

- [x] **Phase 1**: Foundation (config, preview engine, CLI)
- [x] **Phase 2**: Core UI (widgets, layout, event handling)
- [x] **Phase 3**: Navigation & Polish (keyboard shortcuts, help, metadata)
- [x] **Phase 4**: Testing (332 tests, 80%+ coverage)
- [x] **Phase 5**: Documentation & Deployment
- [ ] **Future**: Search, filter, export, custom themes

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `pytest`
5. Run type checking: `mypy src/`
6. Run linting: `ruff check .`
7. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

Built with:
- [Textual](https://textual.textualize.io/) - TUI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [ruamel.yaml](https://yaml.readthedocs.io/) - YAML parsing
- [Click](https://click.palletsprojects.com/) - CLI framework

Inspired by the need to quickly inspect VCR cassettes during test development.
