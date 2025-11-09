# Comprehensive Textual Framework Guide

A complete guide to building TUI (Text User Interface) applications with Textual.

## Table of Contents

1. [Core Concepts & Architecture](#core-concepts--architecture)
2. [Directory Structure & Code Organization](#directory-structure--code-organization)
3. [Testing](#testing)
4. [Design & Best Practices](#design--best-practices)
5. [Common Errors & Pitfalls](#common-errors--pitfalls)
6. [Architectural Patterns](#architectural-patterns)

---

## Core Concepts & Architecture

### How Textual Applications Work

**Event-Driven Architecture:**
- When you call `app.run()`, Textual enters "application mode," taking control of the terminal
- Uses an **asynchronous message queue system** where events are processed sequentially
- Each App and Widget has its own message queue for handling events
- Messages are dispatched to handler methods asynchronously
- The system guarantees message handling even when handlers aren't immediately available

**The DOM (Document Object Model):**
- Textual implements a DOM-like structure where widgets form a tree hierarchy
- Widgets can contain child widgets, similar to web browsers
- Query and manipulate widgets using CSS selectors:
  - `query_one()` - retrieves a single widget
  - `query()` - returns a DOMQuery object (list-like) of matching widgets
  - Supports refinement: `first()`, `last()`, `filter()`, `exclude()`

**Event Bubbling:**
- Events bubble up the DOM hierarchy by default
- Input events propagate from child widgets to parents
- Call `event.stop()` to halt propagation when a widget has handled an event

### Key Components

#### App Class

The foundation class serving as the entry point for all Textual applications.

**Key Attributes:**
- `CSS_PATH` - reference external .tcss files
- `CSS` - inline styles
- `TITLE` / `SUB_TITLE` - header information
- `SCREENS` - map screen names to screen classes
- `BINDINGS` - keyboard shortcuts
- `MODES` - independent screen stacks for different contexts

**Basic Example:**
```python
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Static

class MyApp(App):
    CSS_PATH = "styles.tcss"
    TITLE = "My Application"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Welcome to my app!")
        yield Button("Click me", id="main-button")
        yield Footer()

    def on_mount(self) -> None:
        """Called after entering application mode."""
        # Initialize application state
        pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        self.query_one(Static).update("Button was clicked!")

if __name__ == "__main__":
    app = MyApp()
    app.run()  # Returns exit value
```

#### Screens

Containers for widgets that occupy the entire terminal dimensions.

**Key Points:**
- Only one screen is active at any time
- Textual auto-creates a default screen if you don't specify one
- Screens function like mini-apps: support key bindings, compose methods, and CSS
- Can be pushed, popped, and switched dynamically

**Screen Stack Management:**
```python
# Push screen onto stack (becomes active)
self.push_screen("settings")

# Pop topmost screen (at least one must remain)
self.pop_screen()

# Replace top screen with new one
self.switch_screen("help")

# Pop screen and pass data to callback
self.dismiss(result_data)
```

**Modal Screens:**
```python
from textual.screen import ModalScreen

class ConfirmDialog(ModalScreen[bool]):
    """Type-safe modal that returns a boolean."""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Are you sure?")
            with Horizontal():
                yield Button("Yes", id="yes")
                yield Button("No", id="no")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes":
            self.dismiss(True)
        else:
            self.dismiss(False)

# Usage in app
def action_delete(self) -> None:
    def handle_result(confirmed: bool) -> None:
        if confirmed:
            self.delete_item()

    self.push_screen(ConfirmDialog(), handle_result)
```

**Modes - Multiple Screen Stacks:**
```python
class MyApp(App):
    MODES = {
        "default": "main",
        "settings": "settings_screen",
        "help": "help_screen",
    }

    DEFAULT_MODE = "default"

    def action_open_settings(self) -> None:
        self.switch_mode("settings")
```

#### Widgets

Reusable UI components managing rectangular screen regions.

**Creating Custom Widgets:**
```python
from textual.widget import Widget

class Hello(Widget):
    def render(self) -> str:
        return "Hello, [b]World[/b]!"  # Supports Rich markup
```

**The Static Widget:**
- Caches render results for performance
- Provides `update()` method for refreshing content without full redraws
- Best for simple text display widgets

```python
from textual.widgets import Static

class StatusWidget(Static):
    def update_status(self, message: str) -> None:
        self.update(f"Status: {message}")
```

**Widget Features:**
```python
class CustomWidget(Widget):
    DEFAULT_CSS = """
    CustomWidget {
        border: solid blue;
        padding: 1;
    }
    """

    can_focus = True  # Make widget focusable

    BINDINGS = [
        ("enter", "select", "Select item"),
        ("space", "toggle", "Toggle"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.border_title = "My Widget"
        self.tooltip = "This is a helpful tooltip"
```

#### Containers

Layout-organizing components for arranging widgets.

**Built-in Containers:**
- `Vertical` - stack widgets vertically
- `Horizontal` - arrange widgets horizontally
- `Grid` - grid-based layout
- `Center` - center contents
- `Container` - general-purpose container

**Using Context Managers for Cleaner Composition:**
```python
from textual.containers import Vertical, Horizontal

def compose(self) -> ComposeResult:
    with Vertical():
        yield Header()
        with Horizontal():
            yield Sidebar()
            yield ContentArea()
        yield Footer()
```

### CSS Styling System (TCSS)

**Philosophy:** CSS separates how your app looks from how it works.

**Key Features:**
- External `.tcss` files via `CSS_PATH` or inline with `CSS` class variable
- Supports live editing with `textual run --dev my_app.py`
- Changes reflect in terminal within milliseconds

**Selectors:**
```css
/* Type selector */
Button {
    background: green;
}

/* ID selector */
#next {
    outline: red;
}

/* Class selector */
.success {
    background: green;
}

/* Universal selector */
* {
    border: solid white;
}

/* Pseudo classes */
Button:hover {
    background: blue;
}

Button:focus {
    border: solid yellow;
}

.form-input:disabled {
    opacity: 0.5;
}
```

**Combinators:**
```css
/* Descendant - any nested descendant */
#dialog Button {
    margin: 1;
}

/* Child - only direct children */
#sidebar > Button {
    width: 100%;
}
```

**Advanced Features:**
```css
/* CSS Variables */
Screen {
    background: $surface;
}

Button {
    background: $primary;
}

/* Nesting with & selector */
Button {
    background: $primary;

    &:hover {
        background: $primary-lighten-1;
    }

    &.danger {
        background: $error;
    }
}

/* !important for override (use sparingly) */
.critical {
    background: red !important;
}

/* initial to reset to defaults */
Button {
    border: initial;
}
```

**Example TCSS File:**
```css
/* app.tcss */
Screen {
    background: $surface;
}

#header {
    dock: top;
    height: 3;
    background: $primary;
    color: $text;
}

#sidebar {
    dock: left;
    width: 30;
    background: $panel;
}

Button {
    margin: 1;

    &:hover {
        background: $accent;
    }

    &.success {
        background: $success;
    }

    &.danger {
        background: $error;
    }
}
```

### Reactive System & Data Binding

Reactive attributes are class-level attributes that automatically trigger UI updates when changed.

**Basic Usage:**
```python
from textual.reactive import reactive
from textual.widget import Widget

class Counter(Widget):
    count = reactive(0)  # Reactive attribute

    def render(self) -> str:
        return f"Count: {self.count}"

    def on_button_pressed(self) -> None:
        self.count += 1  # Automatically triggers render()
```

**Key Features:**

**1. Smart Refresh:**
- Multiple changes trigger only one refresh for efficiency
- Automatic calls to `render()` when reactive values change

**2. Validation:**
```python
class Counter(Widget):
    count = reactive(0)

    def validate_count(self, value: int) -> int:
        """Constrain values before assignment."""
        return max(0, min(value, 100))
```

**3. Watch Methods:**
```python
class Counter(Widget):
    count = reactive(0)

    def watch_count(self, old_value: int, new_value: int) -> None:
        """React to changes."""
        if new_value > 10:
            self.add_class("high")
        else:
            self.remove_class("high")
```

**4. Computed Properties:**
```python
class Calculator(Widget):
    count = reactive(0)
    doubled = reactive(0)

    def compute_doubled(self) -> int:
        """Auto-recalculates when count changes."""
        return self.count * 2
```

**5. Recompose:**
```python
class ViewSwitcher(Widget):
    mode = reactive("list", recompose=True)

    def compose(self) -> ComposeResult:
        if self.mode == "list":
            yield ListView()
        else:
            yield GridView()

    def toggle_mode(self) -> None:
        self.mode = "grid" if self.mode == "list" else "list"
        # Widget automatically recomposes
```

**6. Data Binding:**
```python
class ParentWidget(Widget):
    value = reactive(0)

    def compose(self) -> ComposeResult:
        child = ChildWidget()
        # Bind child's display_value to parent's value
        child.data_bind(self, display_value="value")
        yield child

class ChildWidget(Widget):
    display_value = reactive(0)

    def render(self) -> str:
        return f"Value: {self.display_value}"
```

**Advanced Control:**
```python
from textual.reactive import var

class MyWidget(Widget):
    # var() - reactive without refresh/layout changes
    internal_counter = var(0)

    def __init__(self) -> None:
        super().__init__()
        # set_reactive() - set without invoking watchers
        self.set_reactive(MyWidget.count, 10)

    def update_list(self) -> None:
        my_list = [1, 2, 3]
        my_list.append(4)
        # mutate_reactive() - notify system of changes to mutable objects
        self.mutate_reactive(MyWidget.my_list)
```

---

## Directory Structure & Code Organization

### Recommended Project Structures

#### Option 1: Separated Screens and Widgets

Best for medium to large applications with clear separation of concerns.

```
project_name/
├── src/
│   ├── __init__.py
│   ├── __main__.py          # Entry point
│   ├── app.py               # Main App class
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── main_screen.py
│   │   ├── settings_screen.py
│   │   └── help_screen.py
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── status_bar.py
│   │   ├── data_grid.py
│   │   └── custom_input.py
│   └── business_logic/
│       ├── __init__.py
│       ├── models.py        # Data models
│       ├── services.py      # API calls, business logic
│       └── validators.py    # Validation functions
├── static/                  # Optional: external CSS
│   ├── app.tcss
│   ├── screens/
│   │   └── main_screen.tcss
│   └── widgets/
│       └── status_bar.tcss
├── tests/
│   ├── test_app.py
│   ├── test_screens/
│   └── test_widgets/
├── pyproject.toml
└── README.md
```

#### Option 2: Component-Based Structure

Best for smaller applications or when you want to keep related files together.

```
project_name/
├── __init__.py
├── __main__.py
├── app.py
└── components/
    ├── __init__.py
    ├── constants.py
    ├── utils.py
    ├── header/
    │   ├── __init__.py
    │   ├── header.py
    │   └── header.tcss
    ├── sidebar/
    │   ├── __init__.py
    │   ├── sidebar.py
    │   └── sidebar.tcss
    └── content/
        ├── __init__.py
        ├── content.py
        └── content.tcss
```

### Organization Best Practices

#### 1. Widget Communication Pattern

**"Attributes down, messages up"** - Textual's recommended data flow pattern.

- A widget can update a child by setting its attributes or calling methods
- Widgets should only send messages to their parent
- This creates uni-directional data flow

```python
# Parent widget
class ParentWidget(Widget):
    def compose(self) -> ComposeResult:
        yield ChildWidget(initial_value=10)

    def on_child_updated(self, message: ChildWidget.Updated) -> None:
        """Handle message from child."""
        self.log(f"Child updated: {message.new_value}")

# Child widget
class ChildWidget(Widget):
    class Updated(Message):
        """Posted when child value changes."""
        def __init__(self, new_value: int) -> None:
            super().__init__()
            self.new_value = new_value

    def __init__(self, initial_value: int = 0) -> None:
        super().__init__()
        self.value = initial_value

    def increment(self) -> None:
        self.value += 1
        self.post_message(self.Updated(self.value))
```

#### 2. CSS Organization

**For Widgets:**
- Use `DEFAULT_CSS` class variable to bundle styling with distributable widgets
- CSS_PATH only available for App and Screen classes

```python
class StatusBar(Widget):
    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: $panel;
        color: $text-muted;
    }
    """
```

**For Apps:**
- Keep CSS in external files for live editing during development
- Organize by screens and major components

#### 3. Compound Widgets

Build complex widgets from simpler ones through composition.

**Rule of thumb:** A widget should handle one piece of data or one logical UI component.

```python
# Simple widgets
class StatusIcon(Widget):
    def render(self) -> str:
        return "✓"

class StatusText(Static):
    pass

class StatusButton(Button):
    pass

# Compound widget
class StatusPanel(Widget):
    """Combines multiple simple widgets."""

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield StatusIcon()
            yield StatusText("Ready")
            yield StatusButton("Refresh")
```

#### 4. Entry Point Pattern

```python
# app.py
from textual.app import App
# ... imports

class MyApp(App):
    # App implementation
    pass

# __main__.py
from .app import MyApp

def main() -> None:
    app = MyApp()
    app.run()

if __name__ == "__main__":
    main()
```

#### 5. Separation of Concerns

Keep business logic separate from UI components.

```python
# Good structure
# business_logic/services.py
class DataService:
    async def fetch_data(self) -> dict:
        # API calls, data processing
        pass

# business_logic/models.py
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    email: str

# widgets/user_panel.py
from textual.widget import Widget
from ..business_logic.services import DataService
from ..business_logic.models import User

class UserPanel(Widget):
    def __init__(self) -> None:
        super().__init__()
        self.service = DataService()

    async def load_user(self, user_id: int) -> None:
        data = await self.service.fetch_data()
        user = User(**data)
        self.display_user(user)
```

---

## Testing

### Testing Framework Setup

**Recommended Stack:**
- **pytest** - testing framework
- **pytest-asyncio** - async test support
- **pytest-textual-snapshot** - visual regression testing (optional)

**Installation:**
```bash
pip install pytest pytest-asyncio pytest-textual-snapshot
```

**pytest.ini configuration:**
```ini
[pytest]
asyncio_mode = auto
```

### Core Testing Pattern

**The `run_test()` Context Manager:**
- Runs app in "headless" mode (no terminal rendering)
- Returns `Pilot` object for simulating user interactions
- Maintains normal app behavior for assertions

**Basic Test Example:**
```python
import pytest
from my_app import MyApp

@pytest.mark.asyncio
async def test_button_click():
    app = MyApp()
    async with app.run_test() as pilot:
        # Simulate user pressing button
        await pilot.click("#submit-button")

        # Wait for async processing
        await pilot.pause()

        # Assertions
        result = app.query_one("#result", Static)
        assert result.renderable == "Success"
```

### Pilot Methods for Simulation

**Keyboard Input:**
```python
# Single key press
await pilot.press("enter")

# Multiple keys
await pilot.press("h", "e", "l", "l", "o")

# Modifiers
await pilot.press("ctrl+c")
await pilot.press("shift+tab")

# Named keys
await pilot.press("tab", "down", "up", "escape", "pagedown")
```

**Mouse Interaction:**
```python
# Click by selector
await pilot.click("#my-button")

# Click by widget type
await pilot.click(Button)

# Click by coordinates
await pilot.click(offset=(10, 5))

# Double/triple click
await pilot.click("#item", times=2)

# Click with modifiers
await pilot.click("#file", shift=True)
await pilot.click("#item", ctrl=True)
```

**Screen Manipulation:**
```python
# Custom terminal size
async with app.run_test(size=(80, 24)) as pilot:
    # Test responsive behavior
    pass
```

**Async Handling:**
```python
# Wait for pending messages to process
await pilot.pause()

# Essential before assertions to ensure UI has updated
# This is the most common mistake in testing!
```

### Complete Test Example

```python
import pytest
from textual.widgets import Button, Input, Static
from my_app import MyApp

@pytest.mark.asyncio
async def test_user_input_flow():
    """Test complete user interaction flow."""
    app = MyApp()

    async with app.run_test() as pilot:
        # Enter text in input field
        input_widget = app.query_one(Input)
        input_widget.value = "test@example.com"

        # Or use pilot to simulate typing
        await pilot.click(Input)
        await pilot.press("t", "e", "s", "t")

        # Submit form
        await pilot.click("#submit-button")

        # Wait for processing
        await pilot.pause()

        # Verify results
        status = app.query_one("#status", Static)
        assert "Success" in str(status.renderable)

        # Check CSS classes
        assert app.query_one("#form").has_class("submitted")

@pytest.mark.asyncio
async def test_navigation():
    """Test keyboard navigation."""
    app = MyApp()

    async with app.run_test() as pilot:
        # Tab through focusable elements
        await pilot.press("tab")
        await pilot.pause()

        # Check focus
        assert app.focused.id == "first-button"

        # Navigate further
        await pilot.press("tab", "tab")
        await pilot.pause()

        assert app.focused.id == "third-button"

@pytest.mark.asyncio
async def test_screen_switching():
    """Test screen navigation."""
    app = MyApp()

    async with app.run_test() as pilot:
        # Initial screen
        assert app.screen.name == "main"

        # Navigate to settings
        app.push_screen("settings")
        await pilot.pause()

        assert app.screen.name == "settings"

        # Go back
        app.pop_screen()
        await pilot.pause()

        assert app.screen.name == "main"
```

### Snapshot Testing (Optional)

**Purpose:** Visual regression testing through SVG screenshots.

**Basic Usage:**
```python
async def test_ui_appearance(snap_compare):
    """Test that UI matches expected appearance."""
    assert await snap_compare("path/to/app.py")
```

**Advanced Snapshot Testing:**
```python
async def test_after_interaction(snap_compare):
    """Test UI appearance after user interaction."""
    assert await snap_compare(
        "path/to/app.py",
        press=["tab", "enter"],      # Simulate keypresses
        terminal_size=(100, 30),      # Custom size
    )
```

**Updating Snapshots:**
```bash
# Only update after visually confirming output is correct!
pytest --snapshot-update
```

### Testing Best Practices

**1. Always Use `await pilot.pause()`:**
```python
# WRONG - race condition
await pilot.click("#button")
assert app.query_one("#status").text == "Done"  # May fail!

# RIGHT
await pilot.click("#button")
await pilot.pause()  # Wait for message processing
assert app.query_one("#status").text == "Done"
```

**2. Query Widgets for Assertions:**
```python
# Get specific widget by ID
result = app.query_one("#result", Static)
assert result.renderable == "Expected text"

# Get by type
button = app.query_one(Button)
assert button.label == "Click me"

# Check multiple widgets
buttons = app.query("Button.enabled")
assert len(buttons) == 3

# Check widget state
assert widget.has_class("active")
assert widget.disabled is False
```

**3. Test Reactive Behavior:**
```python
async def test_reactive_updates():
    app = MyApp()

    async with app.run_test() as pilot:
        widget = app.query_one(Counter)

        # Trigger reactive change
        widget.count = 5
        await pilot.pause()

        # Verify render update
        assert "Count: 5" in str(widget.render())
```

**4. Test Custom Messages:**
```python
async def test_custom_message():
    app = MyApp()

    async with app.run_test() as pilot:
        # Post custom message
        app.post_message(CustomEvent(data="test"))
        await pilot.pause()

        # Verify handler was called
        assert app.custom_event_handled is True
```

**5. Test with Different Terminal Sizes:**
```python
@pytest.mark.asyncio
async def test_responsive_layout():
    app = MyApp()

    # Test small screen
    async with app.run_test(size=(40, 20)) as pilot:
        assert app.query_one("#sidebar").has_class("compact")

    # Test large screen
    async with app.run_test(size=(120, 40)) as pilot:
        assert not app.query_one("#sidebar").has_class("compact")
```

---

## Design & Best Practices

### UI/UX Best Practices for TUI Apps

#### 1. Start with a Visual Sketch

- Use pen and paper to draw rectangles representing UI elements
- Annotate with content and behavior (scrolling, fixed positioning, etc.)
- Prevents costly redesigns later
- Helps identify layout patterns early

#### 2. Work Outside-In

> "Like sculpting with a block of marble, work from outside towards center"

- Implement fixed elements first (headers, footers, sidebars)
- Then add flexible content areas
- This creates a stable layout foundation

**Example:**
```python
def compose(self) -> ComposeResult:
    # 1. Fixed elements first
    yield Header()

    # 2. Container for main layout
    with Horizontal():
        # 3. Fixed sidebar
        yield Sidebar()

        # 4. Flexible content area (fills remaining space)
        yield ContentArea()

    # 5. Fixed footer
    yield Footer()
```

#### 3. Docking for Fixed Elements

```css
#header {
    dock: top;
    height: 3;
}

#footer {
    dock: bottom;
    height: 1;
}

#sidebar {
    dock: left;
    width: 30;
}
```

#### 4. Use FR Units for Flexible Space

```css
#content {
    width: 1fr;   /* Fill available width */
    height: 1fr;  /* Fill available height */
}

/* Split area into proportional sections */
#left-panel {
    width: 1fr;   /* Takes 1 part */
}

#right-panel {
    width: 2fr;   /* Takes 2 parts (twice as wide) */
}
```

#### 5. Leverage Container Widgets

Pre-built containers come styled with FR units, eliminating redundant CSS.

```python
from textual.containers import Vertical, Horizontal

def compose(self) -> ComposeResult:
    with Vertical():  # Automatically stacks children vertically
        yield Widget1()
        yield Widget2()

    with Horizontal():  # Automatically arranges children horizontally
        yield Widget3()
        yield Widget4()
```

### Layout Patterns

#### Centering UI Elements

**Single Widget:**
```css
Screen {
    align: center middle;
}

#widget {
    width: auto;
    height: auto;
}
```

**Multi-line Text:**
```css
#widget {
    width: 40;
    text-align: center;           /* Center each line */
    content-align: center middle; /* Center content block */
}
```

**Multiple Independent Centered Widgets:**
```python
from textual.containers import Center

def compose(self) -> ComposeResult:
    with Center():
        yield Widget1()
    with Center():
        yield Widget2()
```

#### Grid Layout

```css
#container {
    layout: grid;
    grid-size: 3 2;           /* 3 columns, 2 rows */
    grid-columns: 1fr 2fr 1fr;
    grid-rows: auto auto;
    grid-gutter: 1 2;         /* vertical horizontal spacing */
}

#wide-widget {
    column-span: 2;           /* Span multiple columns */
}

#tall-widget {
    row-span: 2;              /* Span multiple rows */
}
```

**Example:**
```python
from textual.containers import Grid

def compose(self) -> ComposeResult:
    with Grid():
        yield Widget1()  # Column 0, Row 0
        yield Widget2()  # Column 1, Row 0
        yield Widget3()  # Column 2, Row 0
        yield Widget4()  # Column 0, Row 1
        yield Widget5()  # Column 1, Row 1
        yield Widget6()  # Column 2, Row 1
```

### Theme System & Colors

#### 11 Base Colors Generate Complete Palette

**Semantic Color Roles:**
- `$primary` - primary branding color
- `$secondary` - alternative branding
- `$warning` - warning status
- `$error` - error status
- `$success` - success status
- `$accent` - accent highlights
- `$background` - main background
- `$surface` - raised surface
- `$panel` - panel backgrounds
- `$boost` - attention-grabbing elements
- `$dark` - dark elements

**Auto-generated Shades:**
Each color gets 3 light + 3 dark variants:
- `-darken-1`, `-darken-2`, `-darken-3`
- `-lighten-1`, `-lighten-2`, `-lighten-3`
- `-muted` - desaturated variant for secondary areas

**Text Colors with Legibility Guarantees:**
- `$text` - auto-adjusts to light/dark based on background
- `$text-muted` - secondary information
- `$text-disabled` - non-interactive elements

**Best Practices:**
```css
/* GOOD - semantic colors */
#header {
    background: $primary;
    color: $text;
}

.warning-message {
    background: $warning;
    color: $text;
}

#sidebar {
    background: $surface;
}

/* AVOID - hardcoded colors */
#header {
    background: #3498db;  /* What does this represent? */
}
```

### Performance Considerations

#### 1. Target 60fps

Modern terminals support hardware acceleration - smooth performance is achievable.

#### 2. Eliminate Flicker

- Overwrite content rather than clear and redraw
- Write updates in single operations
- Textual uses Synchronized Output protocol automatically

#### 3. Use Immutable Objects

```python
from dataclasses import dataclass
from typing import NamedTuple

# Immutable data structures
@dataclass(frozen=True)
class UserData:
    id: int
    name: str
    email: str

class Point(NamedTuple):
    x: int
    y: int

# Easier to reason about, cache, and test
# Reduces side-effects in layout calculations
```

#### 4. Cache Aggressively

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def calculate_layout(width: int, height: int) -> Layout:
    """Expensive calculation - cache results."""
    # ... complex layout logic
    return layout
```

#### 5. Leverage Static Widget

```python
from textual.widgets import Static

# Static caches render results automatically
class StatusDisplay(Static):
    def update_status(self, message: str) -> None:
        # Only updates when content changes
        self.update(message)
```

### Accessibility Features

**Built-in Accessibility:**
- Screen reader integration
- Monochrome mode
- High-contrast themes
- Color-blind friendly themes
- Full keyboard navigation support

**Keyboard Navigation Best Practices:**
```python
class MyWidget(Widget):
    can_focus = True

    BINDINGS = [
        ("enter", "select", "Select item"),
        ("space", "toggle", "Toggle"),
        ("escape", "cancel", "Cancel"),
        ("?", "help", "Show help"),
    ]

    def action_select(self) -> None:
        """Handle selection."""
        pass
```

**Focus Management:**
```python
# Make widget focusable
widget.can_focus = True

# Programmatic focus
widget.focus()

# Focus next/previous
self.focus_next()
self.focus_previous()

# Check focus state
if self.has_focus:
    # Widget is focused
    pass
```

### Responsive Design Patterns

**Terminal Size Adaptation:**
```python
from textual import events

class ResponsiveWidget(Widget):
    def on_resize(self, event: events.Resize) -> None:
        """Adjust layout based on terminal size."""
        if event.size.width < 80:
            self.add_class("compact")
        else:
            self.remove_class("compact")
```

**CSS for Different Modes:**
```css
/* Base styles */
#sidebar {
    width: 30;
}

#content {
    padding: 2;
}

/* Compact mode for smaller terminals */
.compact #sidebar {
    width: 20;
}

.compact #content {
    padding: 1;
}
```

---

## Common Errors & Pitfalls

### Typical Mistakes Beginners Make

#### 1. Forgetting Async/Await

```python
# WRONG
def on_button_pressed(self):
    self.mount(Widget())  # Missing await

# RIGHT
async def on_button_pressed(self):
    await self.mount(Widget())
```

Many Textual methods are async and must be awaited:
- `mount()`, `unmount()`, `remove()`
- `push_screen()`, `pop_screen()`, `switch_screen()`
- Any method that returns a coroutine

#### 2. Not Waiting for Message Processing in Tests

```python
# WRONG - assertion may run before UI updates
async def test_feature():
    await pilot.click("#button")
    assert app.query_one("#status").text == "Done"  # Race condition!

# RIGHT
async def test_feature():
    await pilot.click("#button")
    await pilot.pause()  # Wait for messages to process
    assert app.query_one("#status").text == "Done"
```

#### 3. Modifying Reactive Attributes in `__init__`

```python
# WRONG - triggers watchers before widget is mounted
def __init__(self):
    super().__init__()
    self.count = 10  # Triggers watch_count before ready!

# RIGHT - Option 1: use set_reactive
def __init__(self):
    super().__init__()
    self.set_reactive(MyWidget.count, 10)  # No watcher invocation

# RIGHT - Option 2: set in on_mount
def __init__(self):
    super().__init__()

def on_mount(self):
    self.count = 10  # Safe to trigger watchers now
```

#### 4. CSS Specificity Confusion

```css
/* Specificity: ID (100) > Class (10) > Type (1) */
Button { background: red; }        /* Specificity: 1 */
.primary { background: blue; }     /* Specificity: 10 */
#submit { background: green; }     /* Specificity: 100 */

/* #submit wins even if Button rule comes after */
```

**Solution:** Understand specificity or use `!important` sparingly.

#### 5. Forgetting to Yield in compose()

```python
# WRONG
def compose(self) -> ComposeResult:
    return [Header(), Footer()]  # Don't return a list!

# RIGHT
def compose(self) -> ComposeResult:
    yield Header()
    yield Footer()
```

#### 6. Not Handling Widget Removal Properly

```python
# WRONG
def remove_widget(self):
    widget = self.query_one("#my-widget")
    widget.remove()
    widget.update("text")  # Widget already removed - error!

# RIGHT
async def remove_widget(self):
    widget = self.query_one("#my-widget")
    await widget.remove()  # Wait for removal to complete
    # Don't use widget after this point
```

#### 7. Blocking the Event Loop

```python
# WRONG - blocks UI
def on_button_pressed(self):
    response = requests.get("https://api.example.com")  # Blocking!
    self.display_result(response.json())

# RIGHT - use workers
from textual.worker import work

@work(exclusive=True)
async def on_button_pressed(self):
    # Use async HTTP library
    response = await httpx.get("https://api.example.com")
    self.display_result(response.json())
```

#### 8. Emoji and Unicode Issues

- Emoji support varies across terminals
- Unicode versions differ
- Multi-codepoint characters (like flags) render unpredictably
- Width calculations can be incorrect

**Best Practice:** Stick to Unicode 9.0 for maximum compatibility, or test thoroughly on target terminals.

### Anti-Patterns to Avoid

#### 1. Excessive Nesting

```python
# AVOID - too deep
def compose(self):
    with Container():
        with Container():
            with Container():
                with Container():
                    yield Widget()  # 4 levels deep!

# BETTER - flatten structure
def compose(self):
    with Container():
        yield Widget()
```

#### 2. Manual Refresh Calls

```python
# AVOID - unnecessary with reactive
def update_status(self, value):
    self.status_text = value
    self.refresh()  # Not needed!

# BETTER - use reactive
class MyWidget(Widget):
    status_text = reactive("")  # Auto-refreshes on change

    def update_status(self, value):
        self.status_text = value  # Automatic refresh
```

#### 3. Direct Child Widget Manipulation

```python
# AVOID - breaks encapsulation
def parent_method(self):
    child = self.query_one(ChildWidget)
    child.internal_state = "modified"  # Don't reach into child internals!

# BETTER - use public API
def parent_method(self):
    child = self.query_one(ChildWidget)
    child.update_value("new")  # Use public method

# OR use messages
def parent_method(self):
    self.post_message(UpdateChild(value="new"))
```

#### 4. Hardcoded Colors

```css
/* AVOID - not themeable */
#header {
    background: #3498db;
    color: white;
}

/* BETTER - use theme variables */
#header {
    background: $primary;
    color: $text;
}
```

#### 5. Ignoring Widget Lifecycle

```python
# AVOID - setup too early
class MyWidget(Widget):
    def __init__(self):
        super().__init__()
        self.api_connection = connect_to_api()  # Widget not mounted yet!

# BETTER - use lifecycle methods
class MyWidget(Widget):
    def on_mount(self):
        """Called after widget is mounted."""
        self.api_connection = connect_to_api()

    async def on_unmount(self):
        """Called before widget is removed."""
        await self.api_connection.close()
```

### Debugging Strategies

#### 1. Development Console

**Terminal 1 - Start console:**
```bash
textual console
```

**Terminal 2 - Run app with dev mode:**
```bash
textual run --dev my_app.py
```

**In your code:**
```python
from textual import log

def on_button_pressed(self):
    log("Button pressed!")
    log("Current state:", self.state)
    log(locals())  # Log all local variables
```

**Console Options:**
- `-v` - increase verbosity (show events)
- `-x EVENT` - exclude specific message types
- `--port 7777` - custom port

#### 2. Visual Debugging with Borders

```css
/* Temporarily add borders to see layout structure */
* {
    border: solid red;
}

/* Or specific widgets */
.debug {
    border: solid yellow;
}
```

#### 3. Screenshots for Analysis

```bash
# Capture screenshot after 5 seconds
textual run --screenshot 5 my_app.py

# Or press Ctrl+S in dev mode for manual capture
```

#### 4. Live CSS Editing

```bash
# Dev mode with auto-reload
textual run --dev my_app.py

# Edit .tcss files and see changes immediately
```

#### 5. Widget Tree Inspection

```python
from textual import log

def on_key(self, event):
    if event.key == "d":  # Press 'd' for debug
        # Log entire widget tree
        log(self.tree)

        # Log specific queries
        log("All buttons:", self.query("Button"))
        log("Focused widget:", self.focused)
```

#### 6. Breakpoint Debugging

```python
async def on_button_pressed(self):
    breakpoint()  # Python debugger
    # Use pdb commands: n (next), s (step), c (continue)
    await self.some_action()
```

---

## Architectural Patterns

### Simple vs Complex App Patterns

#### Simple App Pattern

Best for:
- Prototyping or proof-of-concept
- Single-purpose tools (< 500 lines)
- No complex state management
- Limited user interaction flows

**Example:**
```python
# simple_app.py
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Static

class SimpleApp(App):
    """A simple single-file application."""

    CSS = """
    Screen {
        align: center middle;
    }

    #counter {
        margin: 1;
        padding: 1;
        border: solid green;
    }

    Button {
        margin: 1;
    }
    """

    counter = 0

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(f"Count: {self.counter}", id="counter")
        yield Button("Increment", id="inc")
        yield Button("Decrement", id="dec")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "inc":
            self.counter += 1
        elif event.button.id == "dec":
            self.counter -= 1

        self.query_one("#counter", Static).update(f"Count: {self.counter}")

if __name__ == "__main__":
    SimpleApp().run()
```

#### Complex App Pattern

Best for:
- Production applications
- Multiple screens/views
- External API integration
- Team collaboration
- Long-term maintenance

**Structure:**
```python
# app.py
from textual.app import App, ComposeResult
from .screens.main import MainScreen
from .screens.settings import SettingsScreen
from .screens.help import HelpScreen

class ComplexApp(App):
    """Production-ready multi-screen application."""

    CSS_PATH = "app.tcss"

    SCREENS = {
        "main": MainScreen,
        "settings": SettingsScreen,
        "help": HelpScreen,
    }

    MODES = {
        "default": "main",
        "config": "settings",
    }

    BINDINGS = [
        ("ctrl+s", "switch_mode('config')", "Settings"),
        ("ctrl+h", "push_screen('help')", "Help"),
        ("ctrl+q", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        self.push_screen("main")

# screens/main.py
from textual.screen import Screen
from textual.widgets import Header, Footer
from ..widgets.content import ContentPanel
from ..widgets.sidebar import Sidebar

class MainScreen(Screen):
    CSS_PATH = "screens/main.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield Sidebar()
            yield ContentPanel()
        yield Footer()

# widgets/content.py
from textual.widget import Widget
from textual.worker import work
from ..business_logic.services import DataService

class ContentPanel(Widget):
    DEFAULT_CSS = """
    ContentPanel {
        width: 1fr;
        padding: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.service = DataService()

    @work(exclusive=True)
    async def load_data(self) -> None:
        """Load data asynchronously."""
        data = await self.service.fetch_data()
        self.display_data(data)
```

### Composition vs Inheritance

#### Prefer Composition

> "Build compound widgets by combining simpler ones"

**Why?**
- More flexible and reusable
- Easier to test individual components
- Follows "has-a" relationships naturally
- Reduces coupling

**Example:**
```python
# GOOD - Composition
class UserCard(Widget):
    """Composed of smaller, focused widgets."""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Avatar()           # Simple widget
            yield UserName()         # Simple widget
            yield UserEmail()        # Simple widget
            yield ActionButtons()    # Simple widget

class Avatar(Static):
    """Single-purpose: display avatar."""
    def render(self) -> str:
        return "👤"

class UserName(Static):
    """Single-purpose: display name."""
    pass

class UserEmail(Static):
    """Single-purpose: display email."""
    pass

class ActionButtons(Widget):
    """Single-purpose: action buttons."""
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Button("Edit")
            yield Button("Delete")
```

#### Use Inheritance Sparingly

**When to use inheritance:**
- Implementing framework integration (extending `Widget`, `Screen`, etc.)
- Creating widget variants with different default behavior
- Following "is-a" relationships

**When NOT to use inheritance:**
- Deep inheritance chains (> 2 levels)
- Just to share code (use composition or mixins instead)

**Example:**
```python
# GOOD - Shallow inheritance for framework integration
class CustomButton(Button):
    """A button with custom default styling."""

    DEFAULT_CSS = """
    CustomButton {
        background: $primary;
        border: solid $accent;
    }
    """

# AVOID - Deep inheritance chain
class A(Widget): pass
class B(A): pass
class C(B): pass
class D(C): pass  # Too deep, hard to maintain
```

### State Management Approaches

#### 1. Local Widget State (Simple)

Best for: Widget-specific state that doesn't need to be shared.

```python
class Counter(Widget):
    count = reactive(0)

    def increment(self) -> None:
        self.count += 1

    def render(self) -> str:
        return f"Count: {self.count}"
```

#### 2. App-Level State (Medium)

Best for: Global application state accessible from any widget.

```python
class MyApp(App):
    # App-level reactive state
    user_name = reactive("")
    is_authenticated = reactive(False)
    theme_mode = reactive("light")

    def login(self, username: str) -> None:
        self.user_name = username
        self.is_authenticated = True

    def logout(self) -> None:
        self.user_name = ""
        self.is_authenticated = False

# Any widget can access via self.app
class UserWidget(Widget):
    def render(self) -> str:
        if self.app.is_authenticated:
            return f"Welcome, {self.app.user_name}!"
        return "Please log in"
```

#### 3. Data Binding (Complex)

Best for: Parent-child synchronization of reactive values.

```python
class ParentWidget(Widget):
    selected_value = reactive(0)

    def compose(self) -> ComposeResult:
        child = ChildWidget()
        # Bind child's display to parent's selected_value
        child.data_bind(self, display="selected_value")
        yield child

class ChildWidget(Widget):
    display = reactive(0)

    def render(self) -> str:
        return f"Selected: {self.display}"

    # display auto-updates when parent's selected_value changes
```

#### 4. Message-Based State (Complex)

Best for: Decoupled communication between widgets, event-driven updates.

```python
class DataUpdated(Message):
    """Posted when data changes."""
    def __init__(self, data: dict) -> None:
        super().__init__()
        self.data = data

class DataWidget(Widget):
    def update_data(self, data: dict) -> None:
        """Update data and notify listeners."""
        self.data = data
        self.post_message(DataUpdated(data))

class ListenerWidget(Widget):
    def on_data_updated(self, message: DataUpdated) -> None:
        """Handle data updates from any source."""
        self.refresh_display(message.data)

# Messages bubble up, so parent can handle child events
class ParentWidget(Widget):
    def on_data_updated(self, message: DataUpdated) -> None:
        """Handle data updates from children."""
        self.log(f"Data changed: {message.data}")
```

### How to Keep Code Simple and Maintainable

#### 1. Single Responsibility Principle

Each widget should have one clear purpose.

```python
# AVOID - widget doing too much
class UserPanel(Widget):
    def compose(self) -> ComposeResult:
        # UI composition
        pass

    def fetch_user_data(self) -> dict:
        # API calls
        pass

    def validate_input(self, data: dict) -> bool:
        # Validation logic
        pass

    def save_to_database(self, data: dict) -> None:
        # Database operations
        pass

# BETTER - separate concerns
class UserPanel(Widget):
    """Only handles UI presentation."""

    def __init__(self) -> None:
        super().__init__()
        self.service = UserService()
        self.validator = UserValidator()

    def compose(self) -> ComposeResult:
        # Just UI
        yield UserForm()
        yield UserActions()

    async def on_submit(self) -> None:
        data = self.get_form_data()
        if self.validator.validate(data):
            await self.service.save(data)

# business_logic/services.py
class UserService:
    async def fetch_user(self, user_id: int) -> User:
        # API calls
        pass

    async def save(self, data: dict) -> None:
        # Database operations
        pass

# business_logic/validators.py
class UserValidator:
    def validate(self, data: dict) -> bool:
        # Validation logic
        pass
```

#### 2. Use Actions for Common Operations

```python
class MyApp(App):
    BINDINGS = [
        ("ctrl+s", "save", "Save"),
        ("ctrl+r", "refresh", "Refresh"),
        ("ctrl+q", "quit", "Quit"),
    ]

    def action_save(self) -> None:
        """Reusable save action - can be called from anywhere."""
        self.save_data()

    def action_refresh(self) -> None:
        """Reusable refresh action."""
        self.load_data()

# Can call actions programmatically
def on_button_pressed(self) -> None:
    self.action_save()
```

#### 3. Keep CSS External

```python
# app.py - Clean Python code
class MyApp(App):
    CSS_PATH = "app.tcss"  # All styling in external file

# app.tcss - All styling here
Screen {
    background: $surface;
}

Button {
    margin: 1;

    &:hover {
        background: $accent;
    }
}
```

#### 4. Limit Reactive Watchers

```python
# AVOID - too many watchers
class MyWidget(Widget):
    value1 = reactive(0)
    value2 = reactive(0)
    value3 = reactive(0)

    def watch_value1(self, v): pass
    def watch_value2(self, v): pass
    def watch_value3(self, v): pass
    # ... 10 more watchers

# BETTER - consolidated state
from dataclasses import dataclass

@dataclass
class WidgetState:
    value1: int = 0
    value2: int = 0
    value3: int = 0

class MyWidget(Widget):
    state = reactive(WidgetState())

    def watch_state(self, state: WidgetState) -> None:
        # Single handler for all state changes
        self.handle_state_change(state)
```

#### 5. Use Type Hints

```python
from textual.app import App, ComposeResult
from textual.widgets import Button, Static

class MyApp(App):
    def compose(self) -> ComposeResult:
        yield Button("Click", id="main-button")
        yield Static("Status", id="status")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button: Button = event.button
        button.label = "Clicked"

        status: Static = self.query_one("#status", Static)
        status.update("Button was clicked")
```

#### 6. Document Complex Widgets

```python
class ComplexWidget(Widget):
    """
    Displays user data with real-time updates.

    This widget fetches user data from the API every `refresh_interval`
    seconds and displays it in a formatted panel.

    Attributes:
        user_id: Current user identifier being displayed
        refresh_interval: Seconds between automatic data refreshes

    Messages:
        UserUpdated: Posted when user data is refreshed

    Example:
        >>> widget = ComplexWidget(user_id=123)
        >>> await widget.load_user()
    """

    user_id = reactive("")
    refresh_interval = reactive(5)
```

#### 7. Extract Reusable Components

```python
# AVOID - duplicated code
class Screen1(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Static("Title")
            yield Button("Action")
        yield Footer()

class Screen2(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Static("Title")
            yield Button("Action")
        yield Footer()

# BETTER - reusable components
class TitledPanel(Widget):
    def __init__(self, title: str, action: str) -> None:
        super().__init__()
        self.title = title
        self.action = action

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(self.title)
            yield Button(self.action)

class Screen1(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield TitledPanel("Screen 1", "Action 1")
        yield Footer()

class Screen2(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield TitledPanel("Screen 2", "Action 2")
        yield Footer()
```

---

## Conclusion

This guide covers the essential concepts, patterns, and best practices for building maintainable TUI applications with Textual. Key takeaways:

1. **Architecture**: Event-driven with reactive programming
2. **Organization**: Separate UI from business logic, prefer composition
3. **Testing**: Use pytest with Pilot for simulation
4. **Design**: Sketch first, work outside-in, use semantic colors
5. **Performance**: Cache aggressively, use immutable objects, target 60fps
6. **Maintainability**: Keep widgets focused, use type hints, document complex code

For more information, visit the [official Textual documentation](https://textual.textualize.io).
