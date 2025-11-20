# VCR-TUI: Next Steps Plan

**Date:** 2025-11-20
**Current Phase:** Planning Complete → Implementation Ready
**Branch:** `claude/plan-next-steps-01R7MnPifxmisAZPgvvEgas9`

---

## Executive Summary

The vcr-tui project has **completed comprehensive planning** and is ready for implementation. All architectural decisions are documented, the Claude Skills system is operational, and deep research has validated the approach.

**Status:**
- ✅ Planning & Documentation: 100% Complete
- ✅ Claude Skills System: Operational
- ✅ Architecture Design: Finalized
- ⏳ Implementation: 0% (Ready to start)

---

## Current State Analysis

### Completed Assets

1. **IMPLEMENTATION_PLAN.md** (33 KB)
   - Complete architectural design
   - Detailed implementation phases
   - Code examples and patterns
   - Success criteria defined

2. **Claude Skills System** (~172 KB)
   - Framework skills: `textual`, `hk`
   - Meta-skills: `skill-manager`, `skill-analyzer`, `skill-sync`
   - Cross-tool integration (.cursorrules)
   - Automatic invocation system

3. **Deep Research** (gemini-deep-research.txt - 24 KB)
   - Expert analysis of VCR cassette inspection
   - CLI pipeline strategies
   - Tool comparisons and recommendations
   - Validates the yq|jq approach

4. **Reference Documentation**
   - textual-guide.md (49 KB)
   - textual-quick-reference.md (20 KB)
   - Skills documentation (README, DIAGRAM)

### What's Missing

- ❌ No source code (`src/` directory doesn't exist)
- ❌ No `pyproject.toml` (project not installable)
- ❌ No tests (testing infrastructure not set up)
- ❌ No fixtures (sample VCR cassettes needed)
- ❌ No CLI interface (can't test core logic)

---

## Implementation Roadmap

### 🎯 Phase 1: Foundation (Weeks 1-2)

**Goal:** Create the core preview engine and configuration system without any UI.

#### Sprint 1.1: Project Setup (Days 1-2)

**Tasks:**
1. Create `pyproject.toml` with build system and dependencies
   - Build system: hatchling
   - Core: textual, ruamel.yaml, platformdirs, tomli, rich, click
   - Dev: pytest, pytest-asyncio, pytest-textual-snapshot, mypy, ruff

2. Create directory structure:
   ```
   src/vcr_tui/
   ├── __init__.py
   ├── config/
   ├── preview/
   ├── ui/
   ├── utils/
   tests/
   ├── test_config/
   ├── test_preview/
   ├── test_ui/
   ├── integration/
   fixtures/
   ├── cassettes/
   ├── configs/
   ```

3. Set up development tools:
   - Initialize hk for git hooks
   - Configure ruff for linting
   - Configure mypy for type checking
   - Set up pytest configuration

**Deliverable:** Installable Python package structure

#### Sprint 1.2: Configuration System (Days 3-5)

**Tasks:**
1. Implement `config/models.py`:
   - `@dataclass ExtractionRule`
   - `@dataclass Channel`
   - `@dataclass Config`
   - TOML serialization methods

2. Implement `config/defaults.py`:
   - Built-in VCR channel with extraction rules
   - Default YAML channel
   - Helper function `get_default_config()`

3. Implement `config/loader.py`:
   - `find_config_files()` - Walk up directory tree
   - `load_global_config()` - OS-specific paths
   - `load_config()` - Merge local + global + defaults
   - `merge_configs()` - Config merging logic

4. Create test fixtures:
   - `fixtures/cassettes/example1.yaml` - Sample VCR cassette
   - `fixtures/cassettes/example2.yaml` - Multi-interaction cassette
   - `fixtures/configs/test_config.toml` - Test configuration

5. Write tests:
   - Test config loading and merging
   - Test channel system
   - Test default configs
   - Test config file discovery

**Deliverable:** Working configuration system with tests

#### Sprint 1.3: Preview Engine Core (Days 6-10)

**Tasks:**
1. Implement `preview/types.py`:
   - Type definitions for PreviewResult

2. Implement `preview/yaml_parser.py`:
   - Load YAML files
   - Extract all keys recursively (unwrapped format)
   - Helper: `get_all_keys(data) -> List[str]`

3. Implement `preview/extractors.py`:
   - `ExtractorRegistry` class
   - Parse yq/jq-like path expressions
   - Navigate nested YAML structures
   - Handle array indexing

4. Implement `preview/formatters.py`:
   - `FormatterRegistry` class
   - `format_text()` - Convert escape sequences
   - `format_json()` - Pretty-print JSON
   - `format_html()` - Basic HTML formatting
   - `format_yaml()` - YAML pretty-printing
   - `format_toml()` - TOML formatting

5. Implement `preview/engine.py`:
   - `PreviewEngine` class (no Textual dependencies!)
   - `discover_files()` - Find files by glob patterns
   - `get_yaml_keys()` - Extract all keys from file
   - `preview_key()` - Preview specific key path
   - `preview_file()` - Preview all keys in file

6. Write comprehensive tests:
   - Test YAML parsing
   - Test path extraction
   - Test all formatters
   - Test engine methods
   - Test edge cases (empty bodies, malformed YAML)

**Deliverable:** Fully functional preview engine (CLI-ready)

#### Sprint 1.4: CLI Interface (Days 11-14)

**Tasks:**
1. Implement `cli.py`:
   - Click-based CLI
   - Commands: list files, list keys, preview key
   - Config loading integration
   - Channel selection

2. Implement `__main__.py`:
   - Entry point setup
   - Version display
   - Help text

3. Integration testing:
   - Test CLI with real fixtures
   - Validate config loading
   - Test preview output formatting

4. Create example usage scripts

**Deliverable:** Working CLI tool for testing preview engine

**Phase 1 Exit Criteria:**
- ✅ Preview engine works without Textual
- ✅ CLI can discover files, extract keys, and format content
- ✅ Config system loads local and global configs
- ✅ All core tests pass (>80% coverage)

---

### 🎨 Phase 2: Core UI (Weeks 3-4)

**Goal:** Build the Textual TUI application with core widgets.

#### Sprint 2.1: Basic TUI Shell (Days 15-17)

**Tasks:**
1. Implement `app.py`:
   - Main `VCRTUIApp` class
   - Initialize PreviewEngine
   - Set up key bindings
   - Basic screen management

2. Implement `ui/screens/main_screen.py`:
   - Main layout (horizontal split)
   - Header/Footer
   - Container structure

3. Create `ui/styles/app.tcss`:
   - Main color scheme
   - Layout styling
   - Basic theme

**Deliverable:** Empty TUI shell that launches

#### Sprint 2.2: File List Widget (Days 18-19)

**Tasks:**
1. Implement `ui/widgets/file_list.py`:
   - `FileListWidget` based on ListView
   - Reactive file list
   - Selection handling
   - File loading from engine

2. Write widget tests:
   - Test file loading
   - Test selection events
   - Test rendering

**Deliverable:** Working file browser widget

#### Sprint 2.3: YAML Viewer Widget (Days 20-22)

**Tasks:**
1. Implement `ui/widgets/yaml_viewer.py`:
   - `YAMLViewerWidget` with condensed key display
   - Vim-like j/k navigation bindings
   - Reactive key list
   - Selection highlighting

2. Integration with preview engine:
   - Load keys when file selected
   - Handle large key lists
   - Performance optimization

3. Write tests:
   - Test j/k navigation
   - Test key loading
   - Test selection events

**Deliverable:** Working YAML key navigator

#### Sprint 2.4: Preview & Metadata Widgets (Days 23-25)

**Tasks:**
1. Implement `ui/widgets/preview_panel.py`:
   - Display formatted content
   - Syntax highlighting with Rich
   - Scrolling support
   - Reactive preview updates

2. Implement `ui/widgets/metadata_bar.py`:
   - Display extracted metadata
   - Dynamic layout
   - Reactive updates

3. Wire widgets together:
   - File selection → load keys
   - Key selection → show preview + metadata
   - Update flow testing

4. Create `ui/styles/widgets.tcss`:
   - Widget-specific styling
   - Color schemes
   - Border styles

**Deliverable:** Complete main screen with all widgets working

**Phase 2 Exit Criteria:**
- ✅ All widgets functional and tested
- ✅ Navigation between widgets works
- ✅ Preview updates on key selection
- ✅ Metadata displays correctly

---

### ⚡ Phase 3: Navigation & Polish (Week 5)

**Goal:** Add advanced navigation and full-screen preview.

#### Sprint 3.1: Advanced Navigation (Days 26-28)

**Tasks:**
1. Enhanced key bindings:
   - Tab switching between widgets
   - Focus management
   - Keyboard shortcuts

2. Implement `ui/screens/preview_screen.py`:
   - Full-screen modal preview
   - Scrolling support
   - Esc/q to dismiss

3. Channel switching:
   - Implement channel selection
   - Dynamic channel switching
   - UI feedback

**Deliverable:** Full navigation system

#### Sprint 3.2: Polish & UX (Days 29-31)

**Tasks:**
1. Syntax highlighting:
   - Configure Rich syntax themes
   - Support multiple formats
   - Color customization

2. Error handling:
   - Graceful handling of malformed files
   - User-friendly error messages
   - Empty state displays

3. Performance:
   - Large file handling
   - Lazy loading
   - Caching strategies

**Deliverable:** Polished, production-ready UI

**Phase 3 Exit Criteria:**
- ✅ All navigation works smoothly
- ✅ Full-screen preview functional
- ✅ Syntax highlighting beautiful
- ✅ Error handling graceful

---

### 🧪 Phase 4: Testing (Week 6)

**Goal:** Achieve comprehensive test coverage.

#### Sprint 4.1: Test Infrastructure (Days 32-34)

**Tasks:**
1. Set up pytest-textual-snapshot
2. Create integration test fixtures
3. Configure test coverage reporting
4. Set up CI-ready test suite

**Deliverable:** Complete test infrastructure

#### Sprint 4.2: Comprehensive Testing (Days 35-38)

**Tasks:**
1. Unit tests:
   - All config modules
   - All preview modules
   - All UI widgets

2. Integration tests:
   - Complete workflows
   - File browser flow
   - Preview flow
   - Channel switching

3. Snapshot tests:
   - Main screen appearance
   - Preview screen appearance
   - Different file types

4. Edge case testing:
   - Empty cassettes
   - Malformed YAML
   - Large files
   - Missing configs

**Deliverable:** >80% test coverage, all tests passing

**Phase 4 Exit Criteria:**
- ✅ Test coverage >80%
- ✅ All integration tests pass
- ✅ Snapshot tests established
- ✅ CI-ready test suite

---

### 📚 Phase 5: Documentation (Week 7)

**Goal:** User-facing documentation and guides.

#### Sprint 5.1: Core Documentation (Days 39-42)

**Tasks:**
1. Create `README.md`:
   - Project overview
   - Installation instructions
   - Quick start guide
   - Screenshots/demos

2. Create `docs/USER_GUIDE.md`:
   - Detailed usage instructions
   - Navigation guide
   - Configuration overview
   - Examples

3. Create `docs/CONFIGURATION.md`:
   - TOML schema reference
   - Channel system explained
   - Extraction rules
   - Built-in defaults
   - Examples

4. Create `docs/ARCHITECTURE.md`:
   - System overview
   - Component descriptions
   - Extension points
   - Developer guide

**Deliverable:** Complete documentation suite

#### Sprint 5.2: Polish & Release Prep (Days 43-45)

**Tasks:**
1. Final polish:
   - Code cleanup
   - Documentation review
   - Example configurations
   - Demo cassettes

2. Release preparation:
   - Version tagging
   - CHANGELOG.md
   - Distribution testing
   - PyPI setup (if applicable)

**Deliverable:** Release-ready package

**Phase 5 Exit Criteria:**
- ✅ All documentation complete
- ✅ README has clear examples
- ✅ Installation tested
- ✅ Ready for users

---

## Immediate First Steps

### Today (Day 1)

1. **Create pyproject.toml** ✓
   - Define project metadata
   - List all dependencies
   - Configure build system

2. **Set up directory structure** ✓
   - Create src/vcr_tui/ with subdirectories
   - Create tests/ with subdirectories
   - Create fixtures/ directory

3. **Create basic __init__.py files** ✓
   - Package initialization
   - Version info

4. **Initialize development tools** ✓
   - Set up hk for git hooks
   - Configure ruff
   - Configure pytest

### This Week (Days 1-5)

Complete Sprint 1.1 (Project Setup) and Sprint 1.2 (Configuration System):
- Working package structure
- Configuration system fully implemented
- Basic test suite operational
- Sample fixtures created

---

## Success Metrics

### Phase 1 (Foundation)
- [ ] CLI tool can preview VCR cassettes
- [ ] Config system loads and merges configs
- [ ] Preview engine extracts and formats correctly
- [ ] Test coverage >70% for core modules

### Phase 2 (Core UI)
- [ ] TUI launches and displays file list
- [ ] YAML keys display in condensed format
- [ ] Preview panel shows formatted content
- [ ] j/k navigation works smoothly

### Phase 3 (Polish)
- [ ] All navigation features work
- [ ] Full-screen preview functional
- [ ] Syntax highlighting looks professional
- [ ] Error handling is graceful

### Phase 4 (Testing)
- [ ] Overall test coverage >80%
- [ ] All integration tests pass
- [ ] Snapshot tests capture UI state
- [ ] Tests run in CI

### Phase 5 (Documentation)
- [ ] README complete with examples
- [ ] User guide covers all features
- [ ] Configuration guide has examples
- [ ] Architecture documented

---

## Risk Assessment & Mitigation

### Technical Risks

**Risk:** YAML parsing complexity
**Mitigation:** Use proven library (ruamel.yaml), extensive testing

**Risk:** Textual TUI complexity
**Mitigation:** Have comprehensive Textual skill, follow best practices

**Risk:** Performance with large files
**Mitigation:** Implement lazy loading, caching early

### Process Risks

**Risk:** Scope creep
**Mitigation:** Stick to defined phases, defer enhancements

**Risk:** Testing overhead
**Mitigation:** Test as you go, use TDD approach

---

## Development Environment Setup

### Required Tools

```bash
# Python 3.11+
python3 --version

# Install in development mode
pip install -e ".[dev]"

# Set up git hooks
hk init

# Run tests
pytest

# Run linting
ruff check .

# Type checking
mypy src/
```

### Recommended IDE Setup

- VS Code with Python extension
- Cursor with .cursorrules integration
- Claude Code CLI for AI assistance

---

## Questions to Answer Before Starting

1. **Target Python version?**
   - Recommendation: Python 3.11+ (for tomllib)

2. **Distribution strategy?**
   - PyPI? GitHub releases? Internal only?

3. **CI/CD requirements?**
   - GitHub Actions? GitLab CI?

4. **License?**
   - MIT? Apache 2.0? Proprietary?

5. **Project name final?**
   - "vcr-tui" confirmed?

---

## Next Conversation Starters

**To begin implementation:**
```
"Let's start Phase 1. Create the pyproject.toml and directory structure."
```

**To review architecture:**
```
"Review the configuration system design before we implement it."
```

**To create fixtures:**
```
"Help me create realistic sample VCR cassette fixtures."
```

**To get implementation guidance:**
```
"How should I implement the YAML key extraction in preview/yaml_parser.py?"
```

---

## Resources

### Internal Documentation
- IMPLEMENTATION_PLAN.md - Detailed architectural design
- .claude/skills/textual/SKILL.md - Textual TUI framework guidance
- .claude/skills/hk/SKILL.md - Git hooks management
- gemini-deep-research.txt - VCR inspection deep dive

### External Resources
- Textual Documentation: https://textual.textualize.io
- ruamel.yaml: https://yaml.readthedocs.io
- pytest-textual-snapshot: https://github.com/Textualize/pytest-textual-snapshot
- hk: https://github.com/jdx/hk

---

## Summary

**Current Status:** Planning complete, ready to code
**Next Phase:** Phase 1 - Foundation (Weeks 1-2)
**First Task:** Create pyproject.toml and directory structure
**Estimated Completion:** 7 weeks for MVP
**Success Criteria:** Working TUI that can inspect VCR cassettes with beautiful formatting

**Let's build this! 🚀**
