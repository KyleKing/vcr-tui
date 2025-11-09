# hk Reference Documentation

This document provides comprehensive reference information for hk configuration and usage.

## Complete Configuration Schema

### Top-Level Configuration Fields

```pkl
amends "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Config.pkl"

// Global settings
jobs = 4                           // Number of parallel jobs (0 = auto-detect)
fail_fast = true                   // Stop on first failure
check_first = true                 // Run check before fix
exclude = ["*.min.js", "dist/**"]  // Global file exclusions

// Environment variables (inherited by all linters)
env {
  ["NODE_ENV"] = "production"
  ["PATH"] = "/custom/bin:$PATH"
}

// Linter definitions
linters {
  ["linter-name"] {
    glob = "**/*.ext"
    check = "command"
    fix = "command"
    // ... additional linter properties
  }
}

// Hook definitions
hooks {
  ["pre-commit"] {
    fix = true
    stash = "git"
    steps { /* ... */ }
  }
}

// Conditional linter groups
profiles {
  ["strict"] {
    // Profile-specific linters
  }
}
```

## Linter Configuration Reference

### All Linter Properties

```pkl
linters {
  ["example-linter"] {
    // File matching
    glob = "**/*.py"                    // Required: File pattern to match
    include = ["src/**"]                // Optional: Additional includes
    exclude = ["tests/**"]              // Optional: Exclusions for this linter

    // Commands
    check = "command {files}"           // Read-only validation command
    fix = "command {files}"             // Modification command

    // Staging behavior
    stage = "**/*.py"                   // Files to stage after fix

    // Execution control
    batch = true                        // Process files in batches
    exclusive = false                   // Block concurrent execution
    parallel = true                     // Run in parallel with other steps

    // Workspace
    workspace_indicator = "pyproject.toml"  // File identifying workspace root
    root = "."                          // Directory to run from

    // Conditions
    condition = "git diff --cached --name-only | grep -q '.py$'"

    // Environment
    env {
      ["PYTHONPATH"] = "src:lib"
    }

    // Testing (for built-in tests)
    tests {
      ["test-name"] {
        fixture = "test.py"
        check {
          exit_code = 1
          stdout_contains = "error"
        }
        fix {
          exit_code = 0
          fixed = "test.py"
        }
      }
    }
  }
}
```

### Command Placeholders

Commands can use these placeholders:

- `{files}` - Space-separated list of matching files
- `{file}` - Single file (for non-batch mode)
- `{root}` - Workspace root directory
- `{workspace}` - Workspace directory

Example:

```pkl
check = "eslint {files}"
fix = "prettier --write {files}"
```

## Hook Configuration Reference

### Available Hooks

```pkl
hooks {
  // Git hooks
  ["pre-commit"] { /* ... */ }
  ["pre-push"] { /* ... */ }
  ["commit-msg"] { /* ... */ }
  ["post-commit"] { /* ... */ }

  // Manual hooks
  ["check"] { /* ... */ }
  ["fix"] { /* ... */ }
}
```

### Hook Properties

```pkl
hooks {
  ["pre-commit"] {
    // Behavior
    fix = true                    // Enable fix mode (default: false for git hooks)
    stash = "git"                 // Stash strategy: "git", "patch-file", "none"
    fail_fast = true              // Override global fail_fast

    // Step execution
    steps {
      ["linter-name"] {
        // Step-specific overrides
        env {
          ["VAR"] = "value"
        }
        condition = "expression"
      }
    }

    // Skip control
    skip_steps = ["slow-linter"]  // Skip specific steps in this hook
  }
}
```

### Stash Strategies

- `"git"` - Use git stash to preserve unstaged changes (default)
- `"patch-file"` - Use patch file for stashing (faster for large repos)
- `"none"` - Don't stash (dangerous: may modify unstaged changes)

## Built-in Linters Reference

### Language-Specific Linters

**JavaScript/TypeScript:**
- `prettier` - Code formatter
- `eslint` - Linter and fixer
- `biome` - Fast formatter and linter
- `oxlint` - Extremely fast linter

**Python:**
- `black` - Code formatter
- `ruff` - Fast linter and formatter
- `pylint` - Comprehensive linter
- `mypy` - Type checker
- `isort` - Import sorter

**Rust:**
- `rustfmt` - Code formatter
- `clippy` - Linter

**Go:**
- `gofmt` - Code formatter
- `golangci-lint` - Meta-linter

**Shell:**
- `shellcheck` - Shell script linter
- `shfmt` - Shell formatter

**Infrastructure:**
- `terraform-fmt` - Terraform formatter
- `actionlint` - GitHub Actions linter

**General:**
- `typos` - Spell checker
- `markdownlint` - Markdown linter
- `yamllint` - YAML linter

### Extending Built-in Linters

```pkl
import "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Builtins.pkl"

linters {
  // Use built-in as-is
  ["prettier"] = Builtins.linters["prettier"]

  // Extend built-in
  ["custom-eslint"] = (Builtins.linters["eslint"]) {
    glob = "src/**/*.ts"
    env {
      ["ESLINT_USE_FLAT_CONFIG"] = "true"
    }
  }
}
```

## Command-Line Interface Reference

### hk check

```bash
# Check staged files
hk check

# Check all files
hk check --all

# Check changes since ref
hk check --from-ref main
hk check --from-ref HEAD~5

# Check specific files
hk check file1.py file2.py

# Verbose output
hk check --verbose

# Fail fast or continue on error
hk check --fail-fast
hk check --no-fail-fast
```

### hk fix

```bash
# Fix staged files
hk fix

# Fix all files
hk fix --all

# Fix changes since ref
hk fix --from-ref main

# Fix specific files
hk fix file1.py file2.py

# Skip check before fix
hk fix --no-check-first
```

### hk run

```bash
# Run specific hook
hk run pre-commit
hk run pre-push
hk run check

# Run hook on all files
hk run pre-commit --all

# Run with flags
hk run pre-commit --verbose --fail-fast
```

### hk install

```bash
# Install hooks into .git/hooks
hk install

# Install specific hooks
hk install --hook pre-commit
hk install --hook pre-push

# Uninstall
hk uninstall
```

### Global Flags

```bash
# Set job count
hk check --jobs 8
hk fix -j 8

# Skip specific steps
hk check --skip-step slow-linter --skip-step another

# Skip entire hooks
hk check --skip-hook pre-push

# Use specific config file
hk check --config custom.pkl

# Set log level
hk check --log-level debug
```

## Environment Variables

### Configuration

- `HK_JOBS` - Number of parallel jobs
- `HK_FAIL_FAST` - Stop on first failure (true/false)
- `HK_CONFIG` - Path to config file
- `HK_LOG_LEVEL` - Log level (trace, debug, info, warn, error)

### Feature Flags

- `HK_CHECK_FIRST` - Run check before fix (true/false)
- `HK_STASH` - Stash strategy (git, patch-file, none)

### Git Integration

- `HK_FROM_REF` - Reference to check changes from
- `GIT_DIR` - Git directory location

## Profiles

Profiles enable conditional linter groups:

```pkl
profiles {
  ["strict"] {
    condition = "env.CI == 'true'"
    linters {
      ["strict-eslint"] {
        glob = "**/*.ts"
        check = "eslint --max-warnings 0"
      }
    }
  }

  ["local-only"] {
    condition = "env.CI != 'true'"
    linters {
      ["quick-lint"] {
        glob = "**/*.ts"
        check = "eslint"
      }
    }
  }
}
```

## Expression Syntax (Conditions)

Conditions use [expr-rs](https://github.com/ISibboI/evalexpr) syntax:

```pkl
// String operations
condition = "env.ENVIRONMENT == 'production'"
condition = "env.BRANCH matches '^main$'"

// File operations
condition = "file_exists('package.json')"
condition = "dir_exists('src')"

// Git operations
condition = "git_diff_cached() contains '.ts'"
condition = "git_branch() == 'main'"

// Logical operations
condition = "env.CI == 'true' && git_branch() == 'main'"
condition = "env.SKIP_LINT != 'true' || env.FORCE_LINT == 'true'"
```

## Performance Tuning

### Parallel Execution

```pkl
// Increase parallelism
jobs = 16

// Enable batch mode for linters
linters {
  ["fast-lint"] {
    glob = "**/*.js"
    check = "eslint {files}"
    batch = true  // Process multiple files per invocation
  }
}
```

### Exclusions

```pkl
// Global exclusions (apply to all linters)
exclude = [
  "node_modules/**",
  "dist/**",
  "build/**",
  "*.min.js",
  "*.map",
  ".git/**"
]

// Per-linter exclusions
linters {
  ["eslint"] {
    glob = "**/*.js"
    exclude = ["scripts/vendor/**"]
    check = "eslint"
  }
}
```

### Skip Expensive Checks Locally

```pkl
hooks {
  ["pre-commit"] {
    steps {
      ["quick-format"] {}
      ["expensive-test"] {
        condition = "env.CI == 'true'"  // Only run in CI
      }
    }
  }
}
```

## Git Configuration Integration

hk can read configuration from git config:

```bash
# Set via git config
git config hk.jobs 8
git config hk.fail-fast false

# Global settings
git config --global hk.exclude "*.min.js,dist/**"

# Read config
git config --get hk.jobs
```

## Testing Configuration

### Dry Run

```bash
# See what would run without executing
hk check --all --dry-run
```

### Verbose Output

```bash
# Show detailed execution
hk check --verbose

# Show debug information
hk check --log-level debug
```

### Testing Individual Linters

```bash
# Run specific steps
hk run check --only-step prettier
hk run check --only-step eslint --only-step prettier
```

## Common Patterns

### Pre-commit: Fast Checks

```pkl
hooks {
  ["pre-commit"] {
    fail_fast = true
    steps {
      ["format"] {}
      ["lint-staged"] {}
    }
  }
}
```

### Pre-push: Comprehensive Checks

```pkl
hooks {
  ["pre-push"] {
    steps {
      ["format-check"] {}
      ["lint-all"] {}
      ["test"] {}
      ["build"] {}
    }
  }
}
```

### CI: Full Validation

```pkl
hooks {
  ["check"] {
    steps {
      ["format-check"] {}
      ["lint"] {}
      ["type-check"] {}
      ["test"] {}
      ["security-scan"] {}
    }
  }
}
```

### Monorepo: Workspace-aware

```pkl
linters {
  ["cargo-check"] {
    glob = "**/*.rs"
    workspace_indicator = "Cargo.toml"
    check = "cargo check"
  }

  ["npm-test"] {
    glob = "**/*.ts"
    workspace_indicator = "package.json"
    check = "npm test"
  }
}
```

## Migration from Other Tools

### From pre-commit

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    hooks:
      - id: black
```

Becomes:

```pkl
// hk.pkl
import "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Builtins.pkl"

linters {
  ["black"] = Builtins.linters["black"]
}

hooks {
  ["pre-commit"] {
    steps {
      ["black"] {}
    }
  }
}
```

### From husky

```json
// package.json
{
  "husky": {
    "hooks": {
      "pre-commit": "lint-staged"
    }
  }
}
```

Becomes:

```pkl
// hk.pkl
linters {
  ["lint-staged"] {
    glob = "**/*.{js,ts,jsx,tsx}"
    check = "eslint"
    fix = "eslint --fix"
  }
}

hooks {
  ["pre-commit"] {
    fix = true
    steps {
      ["lint-staged"] {}
    }
  }
}
```

## Troubleshooting Guide

### Issue: Hooks Not Running

**Symptoms:** Git commits without running hk

**Solutions:**

```bash
# Reinstall hooks
hk install

# Check hook files exist
ls -la .git/hooks/

# Verify hook content
cat .git/hooks/pre-commit

# Check git config
git config core.hooksPath
```

### Issue: Files Not Matching

**Symptoms:** Linter not running on expected files

**Solutions:**

```bash
# Test glob pattern
hk check --all --verbose

# List matched files
find . -name "pattern"

# Check exclusions
hk check --all --log-level debug | grep exclude
```

### Issue: Performance Problems

**Symptoms:** hk taking too long

**Solutions:**

```pkl
// Increase parallelism
jobs = 16

// Disable check-first
check_first = false

// Add exclusions
exclude = ["node_modules/**", "dist/**"]

// Use batch mode
linters {
  ["slow-linter"] {
    batch = true
  }
}
```

### Issue: Configuration Errors

**Symptoms:** hk failing with config errors

**Solutions:**

```bash
# Validate config
pkl eval hk.pkl

# Check syntax
hk check --dry-run

# Use verbose logging
hk check --log-level debug
```

## Version Compatibility

This documentation is for hk v1.20.0. Check the package URL in your `hk.pkl` to ensure version compatibility:

```pkl
amends "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Config.pkl"
```

For the latest version, visit: https://github.com/jdx/hk/releases
