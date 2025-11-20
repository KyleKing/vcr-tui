# VCR-TUI Application Plan

## Overview

A Textual TUI application for previewing machine-generated file types (especially VCR YAML cassettes) with:
- Configuration-driven file discovery and content extraction
- Decoupled preview engine usable as CLI or TUI
- Vim-like navigation (j/k) for exploring YAML structures
- Syntax highlighting and formatted previews
- Comprehensive testing with snapshot tests

---

## 1. Project Structure

```
vcr-tui/
├── src/
│   ├── vcr_tui/
│   │   ├── __init__.py
│   │   ├── __main__.py              # Entry point
│   │   ├── app.py                    # Main Textual App
│   │   ├── cli.py                    # CLI interface (uses preview engine)
│   │   │
│   │   ├── config/                   # Configuration system
│   │   │   ├── __init__.py
│   │   │   ├── loader.py             # Load local/global configs
│   │   │   ├── models.py             # TOML schema models
│   │   │   ├── defaults.py           # Built-in default configs
│   │   │   └── channels.py           # Channel system (like television)
│   │   │
│   │   ├── preview/                  # Decoupled preview engine
│   │   │   ├── __init__.py
│   │   │   ├── engine.py            # Core preview logic
│   │   │   ├── extractors.py        # yq/jq extraction logic
│   │   │   ├── formatters.py        # HTML/JSON/text/TOML formatting
│   │   │   ├── yaml_parser.py        # YAML parsing and key extraction
│   │   │   └── types.py              # Type definitions
│   │   │
│   │   ├── ui/                       # Textual UI components
│   │   │   ├── __init__.py
│   │   │   ├── screens/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── main_screen.py    # Main file browser screen
│   │   │   │   └── preview_screen.py # Large preview screen
│   │   │   ├── widgets/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── file_list.py      # File browser widget
│   │   │   │   ├── yaml_viewer.py    # Condensed YAML key viewer
│   │   │   │   ├── preview_panel.py  # Formatted preview widget
│   │   │   │   ├── metadata_bar.py   # Metadata display
│   │   │   │   └── syntax_highlighter.py # Syntax highlighting
│   │   │   └── styles/
│   │   │       ├── app.tcss          # Main stylesheet
│   │   │       └── widgets.tcss     # Widget-specific styles
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── file_discovery.py     # Glob pattern matching
│   │       └── path_utils.py        # Config path resolution
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py               # Pytest fixtures
│   │   ├── test_config/
│   │   │   ├── test_loader.py
│   │   │   ├── test_models.py
│   │   │   └── test_channels.py
│   │   ├── test_preview/
│   │   │   ├── test_engine.py
│   │   │   ├── test_extractors.py
│   │   │   ├── test_formatters.py
│   │   │   └── test_yaml_parser.py
│   │   ├── test_ui/
│   │   │   ├── test_screens/
│   │   │   │   ├── test_main_screen.py
│   │   │   │   └── test_preview_screen.py
│   │   │   └── test_widgets/
│   │   │       ├── test_file_list.py
│   │   │       ├── test_yaml_viewer.py
│   │   │       └── test_preview_panel.py
│   │   └── integration/
│   │       ├── __init__.py
│   │       ├── snapshots/            # Snapshot test outputs
│   │       ├── test_file_browser.py
│   │       ├── test_navigation.py
│   │       └── test_preview_flow.py
│   │
│   ├── fixtures/                     # Test data
│   │   ├── cassettes/                # Sample VCR cassettes
│   │   │   ├── example1.yaml
│   │   │   └── example2.yaml
│   │   └── configs/                  # Test configs
│   │       ├── test_config.toml
│   │       └── global_config.toml
│   │
│   ├── docs/
│   │   ├── USER_GUIDE.md             # User documentation
│   │   ├── CONFIGURATION.md          # Configuration guide
│   │   └── ARCHITECTURE.md           # Developer docs
│   │
│   ├── pyproject.toml                # Project config
│   ├── README.md
│   └── .cursorrules                  # Already exists
│
└── .claude/skills/                   # Existing skills
```

---

## 2. Configuration System

### 2.1 TOML Schema Design

**File: `src/vcr_tui/config/models.py`**

```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path

@dataclass
class ExtractionRule:
    """Rule for extracting and processing data from files."""
    path: str  # yq/jq path expression (e.g., ".body.string")
    formatter: str  # "html", "json", "text", "toml", "yaml"
    label: Optional[str] = None  # Display label
    metadata_keys: Optional[List[str]] = None  # Keys to show as metadata

@dataclass
class Channel:
    """A channel defines file patterns and extraction rules."""
    name: str
    glob_patterns: List[str]  # e.g., ["**/*.yaml", "**/*.yml"]
    extraction_rules: List[ExtractionRule]
    enabled: bool = True

@dataclass
class Config:
    """Complete configuration."""
    root: bool = False  # Stop searching for parent configs (like editorconfig)
    channels: List[Channel] = None
    default_channel: Optional[str] = None
    
    @classmethod
    def from_toml(cls, data: Dict[str, Any]) -> "Config":
        """Load from TOML dict."""
        # Implementation
        pass
    
    def to_toml(self) -> Dict[str, Any]:
        """Convert to TOML-serializable dict."""
        # Implementation
        pass
```

### 2.2 Configuration Loading

**File: `src/vcr_tui/config/loader.py`**

**Requirements:**
- Search for `vcr-tui.toml` or `.vcr-tui.toml` starting from current directory
- Walk up directory tree until `root = true` is found or filesystem root
- Load global config from OS-appropriate location:
  - macOS: `~/Library/Application Support/vcr-tui/config.toml`
  - Linux: `~/.config/vcr-tui/config.toml`
  - Windows: `%APPDATA%/vcr-tui/config.toml`
- Merge configs: local overrides global
- Return merged `Config` object

**Implementation:**
```python
from pathlib import Path
from typing import Optional
import platformdirs
import tomli  # or tomllib for Python 3.11+

def find_config_files(start_path: Path) -> List[Path]:
    """Find all config files from start_path up to root."""
    configs = []
    current = start_path.resolve()
    
    while current != current.parent:
        for name in ["vcr-tui.toml", ".vcr-tui.toml"]:
            config_path = current / name
            if config_path.exists():
                configs.append(config_path)
                # Check if root=true
                with open(config_path, "rb") as f:
                    data = tomli.load(f)
                    if data.get("root", False):
                        return configs
        current = current.parent
    
    return configs

def load_global_config() -> Optional[Config]:
    """Load global configuration."""
    config_dir = Path(platformdirs.user_config_dir("vcr-tui"))
    config_file = config_dir / "config.toml"
    
    if config_file.exists():
        with open(config_file, "rb") as f:
            data = tomli.load(f)
            return Config.from_toml(data)
    return None

def load_config(start_path: Path = None) -> Config:
    """Load merged configuration."""
    if start_path is None:
        start_path = Path.cwd()
    
    # Start with defaults
    config = get_default_config()
    
    # Merge global config
    global_config = load_global_config()
    if global_config:
        config = merge_configs(config, global_config)
    
    # Merge local configs (from deepest to shallowest)
    local_configs = find_config_files(start_path)
    for config_file in reversed(local_configs):
        with open(config_file, "rb") as f:
            data = tomli.load(f)
            local_config = Config.from_toml(data)
            config = merge_configs(config, local_config)
    
    return config
```

### 2.3 Built-in Defaults

**File: `src/vcr_tui/config/defaults.py`**

```python
def get_default_config() -> Config:
    """Return built-in default configuration."""
    return Config(
        root=False,
        channels=[
            Channel(
                name="vcr",
                glob_patterns=["**/*.yaml", "**/*.yml"],
                extraction_rules=[
                    ExtractionRule(
                        path=".body.string",
                        formatter="text",
                        label="Response Body",
                        metadata_keys=["status", "method", "uri"]
                    ),
                    ExtractionRule(
                        path=".body.json",
                        formatter="json",
                        label="JSON Response",
                        metadata_keys=["status", "method", "uri"]
                    ),
                    ExtractionRule(
                        path=".request.body",
                        formatter="text",
                        label="Request Body",
                        metadata_keys=["method", "uri"]
                    ),
                ],
            ),
            Channel(
                name="yaml",
                glob_patterns=["**/*.yaml", "**/*.yml"],
                extraction_rules=[
                    ExtractionRule(
                        path=".",
                        formatter="yaml",
                        label="Full YAML",
                    ),
                ],
            ),
        ],
        default_channel="vcr",
    )
```

### 2.4 Channel System

**File: `src/vcr_tui/config/channels.py`**

Similar to television's channel concept:
- Each channel defines file patterns and extraction rules
- User can switch between channels
- Channels can be enabled/disabled
- Default channel used when none specified

---

## 3. Preview Engine (Decoupled from Textual)

### 3.1 Core Engine

**File: `src/vcr_tui/preview/engine.py`**

**Purpose:** Pure Python logic, no Textual dependencies. Usable as CLI.

```python
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class PreviewResult:
    """Result of preview operation."""
    content: str  # Formatted content
    formatter: str  # Used formatter name
    metadata: Dict[str, Any]  # Extracted metadata
    source_path: str  # yq/jq path used

class PreviewEngine:
    """Core preview engine - no UI dependencies."""
    
    def __init__(self, config: Config):
        self.config = config
        self.extractors = ExtractorRegistry()
        self.formatters = FormatterRegistry()
    
    def discover_files(self, directory: Path, channel: Optional[str] = None) -> List[Path]:
        """Discover files matching channel patterns."""
        # Implementation
        pass
    
    def get_yaml_keys(self, file_path: Path) -> List[str]:
        """Extract all YAML keys as flat list (unwrapped)."""
        # Returns: ["interactions[0].request.method", "interactions[0].request.uri", ...]
        pass
    
    def preview_key(self, file_path: Path, key_path: str, channel: Optional[str] = None) -> PreviewResult:
        """Preview a specific key with formatting."""
        # 1. Load YAML file
        # 2. Extract value using yq/jq path
        # 3. Find matching extraction rule
        # 4. Format using appropriate formatter
        # 5. Extract metadata
        # 6. Return PreviewResult
        pass
    
    def preview_file(self, file_path: Path, channel: Optional[str] = None) -> Dict[str, PreviewResult]:
        """Preview all previewable keys in a file."""
        # Returns dict mapping key_path -> PreviewResult
        pass
```

### 3.2 Extractors

**File: `src/vcr_tui/preview/extractors.py`**

Support for yq/jq-like path expressions:
- `.body.string` - simple key access
- `.interactions[0].request.method` - array indexing
- `.body.json` - nested object access

**Implementation options:**
1. Use `yq` library (Python wrapper for yq)
2. Use `jq` library (Python wrapper for jq)
3. Custom implementation using `ruamel.yaml` or `pyyaml`

**Recommendation:** Start with custom implementation using `ruamel.yaml` for better control, with option to use yq/jq libraries if needed.

```python
class ExtractorRegistry:
    """Registry of extraction methods."""
    
    def extract(self, data: Any, path: str) -> Any:
        """Extract value from data using path expression."""
        # Parse path expression
        # Navigate data structure
        # Return value
        pass
```

### 3.3 Formatters

**File: `src/vcr_tui/preview/formatters.py`**

```python
class FormatterRegistry:
    """Registry of content formatters."""
    
    def format(self, content: Any, formatter_name: str) -> str:
        """Format content using specified formatter."""
        if formatter_name == "html":
            return self.format_html(content)
        elif formatter_name == "json":
            return self.format_json(content)
        elif formatter_name == "text":
            return self.format_text(content)  # Convert \n to actual newlines
        elif formatter_name == "toml":
            return self.format_toml(content)
        elif formatter_name == "yaml":
            return self.format_yaml(content)
        else:
            raise ValueError(f"Unknown formatter: {formatter_name}")
    
    def format_text(self, content: str) -> str:
        """Format text, converting escape sequences."""
        return content.replace("\\n", "\n").replace("\\t", "\t")
    
    def format_json(self, content: Any) -> str:
        """Pretty-print JSON."""
        import json
        return json.dumps(content, indent=2)
    
    def format_html(self, content: str) -> str:
        """Format HTML (could use html.parser for pretty printing)."""
        # Basic implementation or use library
        return content
    
    def format_yaml(self, content: Any) -> str:
        """Format YAML."""
        import ruamel.yaml
        yaml = ruamel.yaml.YAML()
        yaml.preserve_quotes = True
        stream = StringIO()
        yaml.dump(content, stream)
        return stream.getvalue()
```

### 3.4 YAML Parser

**File: `src/vcr_tui/preview/yaml_parser.py`**

```python
class YAMLParser:
    """Parse YAML and extract key paths."""
    
    def load(self, file_path: Path) -> Any:
        """Load YAML file."""
        pass
    
    def get_all_keys(self, data: Any, prefix: str = "") -> List[str]:
        """Recursively extract all key paths."""
        # Returns flat list: ["interactions[0].request.method", ...]
        # Keys are unwrapped (not nested) for easy navigation
        pass
    
    def is_previewable(self, key_path: str, config: Config, channel: Optional[str] = None) -> bool:
        """Check if key matches any extraction rule."""
        pass
```

---

## 4. UI Components

### 4.1 Main Screen

**File: `src/vcr_tui/ui/screens/main_screen.py`**

**Layout:**
```
┌─────────────────────────────────────────┐
│ Header (shows current directory)        │
├──────────┬──────────────────────────────┤
│          │                              │
│ File     │  YAML Key Viewer             │
│ List     │  (condensed, unwrapped)      │
│          │                              │
│ (Tabs)   │  ┌────────────────────────┐ │
│          │  │ Preview Panel           │ │
│          │  │ (formatted content)     │ │
│          │  └────────────────────────┘ │
│          │  ┌────────────────────────┐ │
│          │  │ Metadata Bar           │ │
│          │  │ (status, method, uri)   │ │
│          │  └────────────────────────┘ │
├──────────┴──────────────────────────────┤
│ Footer (key bindings)                  │
└─────────────────────────────────────────┘
```

**Key Bindings:**
- `j` / `down` - Navigate down in key list
- `k` / `up` - Navigate up in key list
- `enter` - Show large preview screen
- `tab` - Switch between file list and key viewer
- `q` - Quit
- `?` - Help

**Implementation:**
```python
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Tabs

class MainScreen(Screen):
    """Main file browser and preview screen."""
    
    CSS_PATH = "ui/styles/main_screen.tcss"
    
    def __init__(self, directory: Path, config: Config):
        super().__init__()
        self.directory = directory
        self.config = config
        self.engine = PreviewEngine(config)
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield FileListWidget(id="file-list")
            with Vertical():
                yield YAMLViewerWidget(id="yaml-viewer")
                yield PreviewPanelWidget(id="preview-panel")
                yield MetadataBarWidget(id="metadata-bar")
        yield Footer()
    
    def on_mount(self) -> None:
        """Load files and initialize."""
        self.load_files()
    
    async def load_files(self) -> None:
        """Discover and load files."""
        files = self.engine.discover_files(self.directory)
        file_list = self.query_one("#file-list", FileListWidget)
        await file_list.set_files(files)
```

### 4.2 File List Widget

**File: `src/vcr_tui/ui/widgets/file_list.py`**

```python
from textual.widgets import ListView, ListItem, Label

class FileListWidget(ListView):
    """Widget displaying discovered files."""
    
    DEFAULT_CSS = """
    FileListWidget {
        width: 30;
        border: solid $primary;
    }
    """
    
    files = reactive([])
    selected_file = reactive(None)
    
    def watch_files(self, files: List[Path]) -> None:
        """Update list when files change."""
        self.clear()
        for file in files:
            self.append(ListItem(Label(str(file.name))))
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle file selection."""
        self.selected_file = self.files[event.item_index]
        self.post_message(FileSelected(self.selected_file))
```

### 4.3 YAML Viewer Widget

**File: `src/vcr_tui/ui/widgets/yaml_viewer.py`**

**Purpose:** Show all YAML keys in condensed, unwrapped format for quick navigation.

```python
from textual.widgets import ListView, ListItem
from textual.reactive import reactive

class YAMLViewerWidget(ListView):
    """Condensed YAML key viewer with vim-like navigation."""
    
    DEFAULT_CSS = """
    YAMLViewerWidget {
        height: 1fr;
        border: solid $accent;
    }
    
    YAMLViewerWidget > ListItem {
        padding: 0 1;
    }
    
    YAMLViewerWidget > ListItem:focus {
        background: $primary;
    }
    """
    
    keys = reactive([])
    current_file = reactive(None)
    
    BINDINGS = [
        ("j", "down", "Down"),
        ("k", "up", "Up"),
    ]
    
    def watch_current_file(self, file_path: Optional[Path]) -> None:
        """Load keys when file changes."""
        if file_path:
            self.load_keys(file_path)
    
    async def load_keys(self, file_path: Path) -> None:
        """Load and display YAML keys."""
        keys = self.app.engine.get_yaml_keys(file_path)
        self.keys = keys
        self.clear()
        for key in keys:
            self.append(ListItem(Label(key)))
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle key selection - show preview."""
        selected_key = self.keys[event.item_index]
        self.post_message(KeySelected(selected_key))
```

### 4.4 Preview Panel Widget

**File: `src/vcr_tui/ui/widgets/preview_panel.py`**

```python
from textual.widgets import Static
from textual.reactive import reactive
from rich.syntax import Syntax

class PreviewPanelWidget(Static):
    """Widget displaying formatted preview content."""
    
    DEFAULT_CSS = """
    PreviewPanelWidget {
        height: 2fr;
        border: solid $success;
        padding: 1;
    }
    """
    
    preview_result = reactive(None)
    
    def watch_preview_result(self, result: Optional[PreviewResult]) -> None:
        """Update preview when result changes."""
        if result:
            self.update_preview(result)
    
    def update_preview(self, result: PreviewResult) -> None:
        """Render formatted content with syntax highlighting."""
        syntax = Syntax(
            result.content,
            result.formatter,  # Use formatter as lexer
            theme="monokai",
            line_numbers=True,
        )
        self.update(syntax)
```

### 4.5 Metadata Bar Widget

**File: `src/vcr_tui/ui/widgets/metadata_bar.py`**

```python
from textual.widgets import Static
from textual.reactive import reactive

class MetadataBarWidget(Static):
    """Display metadata for current preview."""
    
    DEFAULT_CSS = """
    MetadataBarWidget {
        height: 3;
        border: solid $warning;
        padding: 0 1;
    }
    """
    
    metadata = reactive({})
    
    def watch_metadata(self, metadata: Dict[str, Any]) -> None:
        """Update metadata display."""
        if metadata:
            lines = [f"{k}: {v}" for k, v in metadata.items()]
            self.update("\n".join(lines))
        else:
            self.update("")
```

### 4.6 Preview Screen (Large)

**File: `src/vcr_tui/ui/screens/preview_screen.py`**

Full-screen preview for detailed viewing.

```python
from textual.screen import Screen
from textual.widgets import Header, Footer, Static

class PreviewScreen(ModalScreen):
    """Full-screen preview modal."""
    
    def __init__(self, preview_result: PreviewResult):
        super().__init__()
        self.preview_result = preview_result
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(self.preview_result.content, id="preview-content")
        yield Footer()
    
    BINDINGS = [
        ("escape", "dismiss", "Close"),
        ("q", "dismiss", "Close"),
    ]
```

---

## 5. CLI Interface

**File: `src/vcr_tui/cli.py`**

```python
import click
from pathlib import Path
from vcr_tui.config.loader import load_config
from vcr_tui.preview.engine import PreviewEngine

@click.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--channel", help="Channel to use")
@click.option("--key", help="Specific key to preview")
def main(directory: Path, channel: str = None, key: str = None):
    """VCR-TUI CLI - Preview machine-generated files."""
    config = load_config(directory)
    engine = PreviewEngine(config)
    
    if key:
        # Preview specific key
        files = engine.discover_files(directory, channel)
        if files:
            result = engine.preview_key(files[0], key, channel)
            print(result.content)
    else:
        # List previewable keys
        files = engine.discover_files(directory, channel)
        for file in files:
            keys = engine.get_yaml_keys(file)
            for key_path in keys:
                print(f"{file}:{key_path}")
```

---

## 6. Testing Strategy

### 6.1 Unit Tests

**Following Textual best practices:**

1. **Config Tests** (`tests/test_config/`)
   - Test config loading (local, global, merging)
   - Test channel system
   - Test default configs

2. **Preview Engine Tests** (`tests/test_preview/`)
   - Test file discovery with glob patterns
   - Test YAML key extraction
   - Test extraction rules (yq/jq paths)
   - Test formatters (HTML, JSON, text, TOML, YAML)
   - Test metadata extraction

3. **UI Widget Tests** (`tests/test_ui/`)
   - Test file list widget
   - Test YAML viewer widget
   - Test preview panel widget
   - Test metadata bar widget
   - Test screen navigation

**Example test pattern:**
```python
import pytest
from textual.widgets import ListView

@pytest.mark.asyncio
async def test_yaml_viewer_navigation():
    """Test j/k navigation in YAML viewer."""
    widget = YAMLViewerWidget()
    widget.keys = ["key1", "key2", "key3"]
    
    async with widget.app.run_test() as pilot:
        # Initial state
        assert widget.highlighted == 0
        
        # Press 'j' to go down
        await pilot.press("j")
        await pilot.pause()
        assert widget.highlighted == 1
        
        # Press 'k' to go up
        await pilot.press("k")
        await pilot.pause()
        assert widget.highlighted == 0
```

### 6.2 Integration Tests

**File: `tests/integration/test_file_browser.py`**

```python
@pytest.mark.asyncio
async def test_file_browser_flow():
    """Test complete file browser workflow."""
    app = VCRTUIApp(directory=Path("fixtures/cassettes"))
    
    async with app.run_test(size=(120, 40)) as pilot:
        # Wait for files to load
        await pilot.pause()
        
        # Select first file
        await pilot.click("#file-list")
        await pilot.press("enter")
        await pilot.pause()
        
        # Navigate keys with j/k
        await pilot.press("j", "j")
        await pilot.pause()
        
        # Verify preview updated
        preview = app.query_one("#preview-panel")
        assert preview.preview_result is not None
```

### 6.3 Snapshot Tests

**File: `tests/integration/test_snapshots.py`**

Using `pytest-textual-snapshot`:

```python
@pytest.mark.asyncio
async def test_main_screen_appearance(snap_compare):
    """Test main screen visual appearance."""
    assert await snap_compare(
        "src/vcr_tui/app.py",
        press=["tab", "j", "j"],
        terminal_size=(120, 40),
    )

@pytest.mark.asyncio
async def test_preview_screen(snap_compare):
    """Test preview screen appearance."""
    assert await snap_compare(
        "src/vcr_tui/app.py",
        press=["tab", "enter"],  # Select key and open preview
        terminal_size=(120, 40),
    )
```

**Snapshot Update:**
```bash
pytest --snapshot-update tests/integration/test_snapshots.py
```

### 6.4 Test Fixtures

**File: `tests/conftest.py`**

```python
import pytest
from pathlib import Path
from vcr_tui.config.loader import load_config
from vcr_tui.config.models import Config

@pytest.fixture
def test_config() -> Config:
    """Load test configuration."""
    return load_config(Path("fixtures/configs"))

@pytest.fixture
def sample_cassette() -> Path:
    """Path to sample VCR cassette."""
    return Path("fixtures/cassettes/example1.yaml")

@pytest.fixture
def preview_engine(test_config):
    """Preview engine instance."""
    from vcr_tui.preview.engine import PreviewEngine
    return PreviewEngine(test_config)
```

---

## 7. Documentation

### 7.1 User Guide

**File: `docs/USER_GUIDE.md`**

**Sections:**
1. Installation
2. Quick Start
3. Navigation (j/k, tab, enter)
4. Configuration overview
5. Channels
6. Examples

### 7.2 Configuration Guide

**File: `docs/CONFIGURATION.md`**

**High-level user requirements:**

1. **Configuration Files**
   - Local: `vcr-tui.toml` or `.vcr-tui.toml` in project directory
   - Global: OS-appropriate location (see loader.py)
   - Inheritance: Local overrides global, walk up directory tree until `root = true`

2. **Configuration Structure**
   ```toml
   root = false  # Stop searching parent directories

   [channels.vcr]
   glob_patterns = ["**/*.yaml", "**/*.yml"]
   
   [[channels.vcr.extraction_rules]]
   path = ".body.string"
   formatter = "text"
   label = "Response Body"
   metadata_keys = ["status", "method", "uri"]
   
   [[channels.vcr.extraction_rules]]
   path = ".body.json"
   formatter = "json"
   label = "JSON Response"
   ```

3. **Built-in Defaults**
   - VCR channel with common extraction rules
   - YAML channel for general YAML files
   - Reference defaults in documentation

4. **Channels**
   - Similar to television's channel concept
   - Each channel defines file patterns and rules
   - Switch channels to change behavior
   - Default channel used when none specified

5. **Extraction Rules**
   - `path`: yq/jq-like path expression
   - `formatter`: How to display content (html, json, text, toml, yaml)
   - `label`: Display name
   - `metadata_keys`: Keys to show in metadata bar

### 7.3 Architecture Documentation

**File: `docs/ARCHITECTURE.md`**

**Sections:**
1. Overview
2. Configuration System
3. Preview Engine (decoupled design)
4. UI Components
5. Testing Strategy
6. Extension Points

---

## 8. Implementation Order

### Phase 1: Foundation
1. ✅ Project structure setup
2. ✅ Configuration system (models, loader, defaults)
3. ✅ Preview engine core (no UI)
4. ✅ CLI interface (test preview engine)

### Phase 2: Core UI
5. ✅ Main screen layout
6. ✅ File list widget
7. ✅ YAML viewer widget (condensed keys)
8. ✅ Preview panel widget
9. ✅ Metadata bar widget

### Phase 3: Navigation & Polish
10. ✅ Vim-like navigation (j/k)
11. ✅ Preview screen (full-screen)
12. ✅ Tab switching
13. ✅ Syntax highlighting

### Phase 4: Testing
14. ✅ Unit tests for all components
15. ✅ Integration tests
16. ✅ Snapshot tests

### Phase 5: Documentation
17. ✅ User guide
18. ✅ Configuration guide
19. ✅ Architecture docs

---

## 9. Dependencies

**File: `pyproject.toml`**

```toml
[project]
name = "vcr-tui"
version = "0.1.0"
description = "TUI for previewing VCR cassettes and machine-generated files"
requires-python = ">=3.11"
dependencies = [
    "textual>=0.50.0",
    "ruamel.yaml>=0.18.0",
    "platformdirs>=3.0.0",
    "tomli>=2.0.0",  # or tomllib for Python 3.11+
    "rich>=13.0.0",
    "click>=8.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-textual-snapshot>=0.1.0",
    "mypy>=1.0.0",
    "ruff>=0.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

## 10. Key Design Decisions

1. **Decoupled Preview Engine**
   - Preview logic in `preview/` module with no Textual imports
   - Enables CLI usage and testing without UI
   - UI components use engine as service

2. **Configuration Inheritance**
   - Follows editorconfig pattern (`root = true`)
   - Local configs override global
   - Walk up directory tree until root found

3. **Channel System**
   - Inspired by television's channels
   - Allows multiple configurations for same file types
   - User can switch channels

4. **Vim-like Navigation**
   - j/k for up/down navigation
   - Familiar to developers
   - Can be extended with more vim bindings

5. **Condensed YAML View**
   - All keys shown unwrapped (flat list)
   - Easy to scan and navigate
   - Preview shows formatted content separately

6. **Testing Strategy**
   - Unit tests for all logic
   - Integration tests for workflows
   - Snapshot tests for UI regression
   - Follow Textual best practices (await pilot.pause())

---

## 11. Future Enhancements

1. **Advanced Extraction**
   - Support for actual yq/jq libraries
   - Custom extraction scripts
   - Regex-based extraction

2. **More Formatters**
   - XML formatting
   - CSV preview
   - Image preview (if terminal supports)

3. **Search & Filter**
   - Search keys by pattern
   - Filter files by name
   - Filter keys by type

4. **Export**
   - Export previews to files
   - Copy formatted content to clipboard
   - Generate reports

5. **Themes**
   - Multiple color themes
   - Customizable key bindings
   - Layout customization

---

## 12. Success Criteria

✅ **Functional:**
- Launch in directory, see files
- Navigate YAML keys with j/k
- Preview formatted content
- See metadata
- Configuration works locally and globally

✅ **Architectural:**
- Preview engine usable as CLI
- No Textual dependencies in preview engine
- Clean separation of concerns

✅ **Testing:**
- >80% code coverage
- All integration tests pass
- Snapshot tests for UI

✅ **Documentation:**
- User guide complete
- Configuration guide with examples
- Architecture documented

---

This plan provides a comprehensive roadmap for building the VCR-TUI application following Textual best practices and the requirements specified.
