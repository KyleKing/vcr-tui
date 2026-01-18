# VCR-TUI

A TUI for previewing VCR cassettes and machine-generated files.

## Installation

```bash
uv sync
```

## Usage

```bash
# Launch TUI in current directory
vcr-tui

# Launch TUI in specific directory
vcr-tui /path/to/cassettes

# List discovered files
vcr-tui files

# Show YAML keys for a file
vcr-tui keys path/to/cassette.yaml

# Preview a file or specific key
vcr-tui preview path/to/cassette.yaml
vcr-tui preview path/to/cassette.yaml --key "interactions[0].response.body.string"
```

## Key Bindings

- `j` / `Down` - Navigate down
- `k` / `Up` - Navigate up
- `Tab` - Switch focus between panels
- `q` - Quit
