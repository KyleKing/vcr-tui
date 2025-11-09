# hk Configuration Examples

This document provides ready-to-use hk configurations for common project types and scenarios.

## Quick Start Examples

### Minimal Setup

```pkl
amends "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Config.pkl"

import "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Builtins.pkl"

linters = Builtins.linters.toMap()

hooks {
  ["pre-commit"] {
    steps {
      ["prettier"] {}
    }
  }
}
```

### Language-Specific Examples

## JavaScript/TypeScript Projects

### Node.js with ESLint and Prettier

```pkl
amends "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Config.pkl"

import "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Builtins.pkl"

exclude = ["node_modules/**", "dist/**", "build/**", "*.min.js"]

linters {
  ["prettier"] = (Builtins.linters["prettier"]) {
    glob = "**/*.{js,ts,jsx,tsx,json,css,md}"
  }

  ["eslint"] = (Builtins.linters["eslint"]) {
    glob = "**/*.{js,ts,jsx,tsx}"
    exclude = ["*.config.js"]
  }
}

hooks {
  ["pre-commit"] {
    fix = true
    steps {
      ["prettier"] {}
      ["eslint"] {}
    }
  }

  ["pre-push"] {
    steps {
      ["test"] {
        glob = "**/*.test.ts"
        check = "npm test"
      }
    }
  }
}
```

### TypeScript with Type Checking

```pkl
amends "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Config.pkl"

linters {
  ["prettier"] {
    glob = "**/*.{ts,tsx}"
    fix = "prettier --write {files}"
  }

  ["eslint"] {
    glob = "**/*.{ts,tsx}"
    check = "eslint {files}"
    fix = "eslint --fix {files}"
  }

  ["tsc"] {
    glob = "**/*.{ts,tsx}"
    check = "tsc --noEmit"
    workspace_indicator = "tsconfig.json"
  }
}

hooks {
  ["pre-commit"] {
    fix = true
    steps {
      ["prettier"] {}
      ["eslint"] {}
    }
  }

  ["pre-push"] {
    steps {
      ["tsc"] {}
      ["test"] {
        glob = "**/*.test.ts"
        check = "npm test"
      }
    }
  }
}
```

### React Project with Biome

```pkl
amends "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Config.pkl"

linters {
  ["biome"] {
    glob = "**/*.{js,ts,jsx,tsx,json}"
    check = "biome check {files}"
    fix = "biome check --apply {files}"
    batch = true
  }
}

hooks {
  ["pre-commit"] {
    fix = true
    steps {
      ["biome"] {}
    }
  }
}
```

## Python Projects

### Python with Black and Ruff

```pkl
amends "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Config.pkl"

import "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Builtins.pkl"

exclude = ["__pycache__/**", "*.pyc", ".venv/**", "venv/**"]

linters {
  ["black"] = (Builtins.linters["black"]) {
    glob = "**/*.py"
  }

  ["ruff"] = (Builtins.linters["ruff"]) {
    glob = "**/*.py"
  }

  ["isort"] = (Builtins.linters["isort"]) {
    glob = "**/*.py"
  }
}

hooks {
  ["pre-commit"] {
    fix = true
    steps {
      ["isort"] {}
      ["black"] {}
      ["ruff"] {}
    }
  }
}
```

### Python with Type Checking

```pkl
amends "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Config.pkl"

linters {
  ["black"] {
    glob = "**/*.py"
    check = "black --check {files}"
    fix = "black {files}"
  }

  ["ruff"] {
    glob = "**/*.py"
    check = "ruff check {files}"
    fix = "ruff check --fix {files}"
  }

  ["mypy"] {
    glob = "**/*.py"
    check = "mypy {files}"
    workspace_indicator = "pyproject.toml"
  }

  ["pytest"] {
    glob = "**/*.py"
    check = "pytest"
    workspace_indicator = "pyproject.toml"
  }
}

hooks {
  ["pre-commit"] {
    fix = true
    steps {
      ["black"] {}
      ["ruff"] {}
    }
  }

  ["pre-push"] {
    steps {
      ["mypy"] {}
      ["pytest"] {}
    }
  }
}
```

## Rust Projects

### Basic Rust Setup

```pkl
amends "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Config.pkl"

import "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Builtins.pkl"

linters {
  ["rustfmt"] = (Builtins.linters["rustfmt"]) {
    glob = "**/*.rs"
  }

  ["clippy"] = (Builtins.linters["clippy"]) {
    glob = "**/*.rs"
    workspace_indicator = "Cargo.toml"
  }
}

hooks {
  ["pre-commit"] {
    fix = true
    steps {
      ["rustfmt"] {}
    }
  }

  ["pre-push"] {
    steps {
      ["clippy"] {}
      ["test"] {
        glob = "**/*.rs"
        check = "cargo test"
        workspace_indicator = "Cargo.toml"
      }
    }
  }
}
```

### Rust with Comprehensive Checks

```pkl
amends "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Config.pkl"

linters {
  ["rustfmt"] {
    glob = "**/*.rs"
    check = "cargo fmt -- --check"
    fix = "cargo fmt"
    workspace_indicator = "Cargo.toml"
  }

  ["clippy"] {
    glob = "**/*.rs"
    check = "cargo clippy -- -D warnings"
    workspace_indicator = "Cargo.toml"
  }

  ["test"] {
    glob = "**/*.rs"
    check = "cargo test"
    workspace_indicator = "Cargo.toml"
  }

  ["doc"] {
    glob = "**/*.rs"
    check = "cargo doc --no-deps"
    workspace_indicator = "Cargo.toml"
  }
}

hooks {
  ["pre-commit"] {
    fix = true
    fail_fast = true
    steps {
      ["rustfmt"] {}
      ["clippy"] {}
    }
  }

  ["pre-push"] {
    steps {
      ["test"] {}
      ["doc"] {}
    }
  }
}
```

## Go Projects

### Go with Standard Tools

```pkl
amends "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Config.pkl"

import "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Builtins.pkl"

linters {
  ["gofmt"] = (Builtins.linters["gofmt"]) {
    glob = "**/*.go"
  }

  ["golangci-lint"] = (Builtins.linters["golangci-lint"]) {
    glob = "**/*.go"
  }
}

hooks {
  ["pre-commit"] {
    fix = true
    steps {
      ["gofmt"] {}
      ["golangci-lint"] {}
    }
  }

  ["pre-push"] {
    steps {
      ["test"] {
        glob = "**/*.go"
        check = "go test ./..."
      }
    }
  }
}
```

## Multi-Language Projects

### Full-Stack Project (TypeScript + Python)

```pkl
amends "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Config.pkl"

exclude = [
  "node_modules/**",
  "dist/**",
  "__pycache__/**",
  ".venv/**",
  "*.pyc"
]

linters {
  // Frontend (TypeScript)
  ["prettier-frontend"] {
    glob = "frontend/**/*.{ts,tsx,css,json}"
    check = "prettier --check {files}"
    fix = "prettier --write {files}"
  }

  ["eslint-frontend"] {
    glob = "frontend/**/*.{ts,tsx}"
    check = "eslint {files}"
    fix = "eslint --fix {files}"
  }

  // Backend (Python)
  ["black-backend"] {
    glob = "backend/**/*.py"
    check = "black --check {files}"
    fix = "black {files}"
  }

  ["ruff-backend"] {
    glob = "backend/**/*.py"
    check = "ruff check {files}"
    fix = "ruff check --fix {files}"
  }

  // Shared
  ["markdownlint"] {
    glob = "**/*.md"
    check = "markdownlint {files}"
  }
}

hooks {
  ["pre-commit"] {
    fix = true
    steps {
      ["prettier-frontend"] {}
      ["eslint-frontend"] {}
      ["black-backend"] {}
      ["ruff-backend"] {}
    }
  }

  ["pre-push"] {
    steps {
      ["markdownlint"] {}
      ["frontend-test"] {
        glob = "frontend/**/*.test.ts"
        check = "cd frontend && npm test"
      }
      ["backend-test"] {
        glob = "backend/**/*.py"
        check = "cd backend && pytest"
      }
    }
  }
}
```

## Infrastructure as Code

### Terraform Project

```pkl
amends "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Config.pkl"

import "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Builtins.pkl"

linters {
  ["terraform-fmt"] = (Builtins.linters["terraform-fmt"]) {
    glob = "**/*.tf"
  }

  ["tflint"] {
    glob = "**/*.tf"
    check = "tflint {files}"
  }

  ["terraform-validate"] {
    glob = "**/*.tf"
    check = "terraform validate"
  }
}

hooks {
  ["pre-commit"] {
    fix = true
    steps {
      ["terraform-fmt"] {}
      ["tflint"] {}
    }
  }

  ["pre-push"] {
    steps {
      ["terraform-validate"] {}
    }
  }
}
```

### GitHub Actions Workflow Validation

```pkl
amends "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Config.pkl"

import "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Builtins.pkl"

linters {
  ["actionlint"] = (Builtins.linters["actionlint"]) {
    glob = ".github/workflows/*.{yml,yaml}"
  }

  ["yamllint"] = (Builtins.linters["yamllint"]) {
    glob = "**/*.{yml,yaml}"
  }
}

hooks {
  ["pre-commit"] {
    steps {
      ["yamllint"] {}
      ["actionlint"] {}
    }
  }
}
```

## Advanced Patterns

### Conditional Linting Based on Environment

```pkl
amends "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Config.pkl"

linters {
  ["quick-lint"] {
    glob = "**/*.ts"
    check = "eslint {files}"
  }

  ["strict-lint"] {
    glob = "**/*.ts"
    check = "eslint --max-warnings 0 {files}"
    condition = "env.CI == 'true'"
  }
}

hooks {
  ["pre-commit"] {
    steps {
      ["quick-lint"] {
        condition = "env.CI != 'true'"
      }
      ["strict-lint"] {
        condition = "env.CI == 'true'"
      }
    }
  }
}
```

### Monorepo with Workspace Detection

```pkl
amends "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Config.pkl"

linters {
  ["node-workspaces"] {
    glob = "**/package.json"
    workspace_indicator = "package.json"
    check = "npm run lint"
    batch = false  // Run per workspace
  }

  ["rust-workspaces"] {
    glob = "**/*.rs"
    workspace_indicator = "Cargo.toml"
    check = "cargo clippy"
  }

  ["python-workspaces"] {
    glob = "**/*.py"
    workspace_indicator = "pyproject.toml"
    check = "ruff check {files}"
  }
}

hooks {
  ["pre-commit"] {
    steps {
      ["node-workspaces"] {}
      ["rust-workspaces"] {}
      ["python-workspaces"] {}
    }
  }
}
```

### Incremental Checks for Large Repos

```pkl
amends "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Config.pkl"

// Global settings for performance
jobs = 16
check_first = false

exclude = [
  "node_modules/**",
  "dist/**",
  "build/**",
  ".venv/**",
  "target/**"
]

linters {
  ["fast-format"] {
    glob = "**/*.{js,ts,py,rs}"
    fix = "prettier --write {files}"
    batch = true
  }

  ["incremental-test"] {
    glob = "**/*.test.ts"
    check = "jest --bail --findRelatedTests {files}"
    condition = "git diff --cached --name-only | grep -q '.ts$'"
  }
}

hooks {
  ["pre-commit"] {
    fix = true
    fail_fast = true
    steps {
      ["fast-format"] {}
      ["incremental-test"] {}
    }
  }
}
```

### Security and Quality Checks

```pkl
amends "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Config.pkl"

linters {
  // Code quality
  ["prettier"] {
    glob = "**/*.{js,ts,json,md}"
    check = "prettier --check {files}"
    fix = "prettier --write {files}"
  }

  ["eslint"] {
    glob = "**/*.{js,ts}"
    check = "eslint {files}"
    fix = "eslint --fix {files}"
  }

  // Security
  ["npm-audit"] {
    glob = "package.json"
    check = "npm audit --audit-level=moderate"
  }

  ["detect-secrets"] {
    glob = "**/*"
    exclude = ["package-lock.json", "*.lock"]
    check = "detect-secrets scan {files}"
  }

  // Spell checking
  ["typos"] {
    glob = "**/*.{md,ts,js,py}"
    check = "typos {files}"
    fix = "typos --write-changes {files}"
  }
}

hooks {
  ["pre-commit"] {
    fix = true
    steps {
      ["prettier"] {}
      ["eslint"] {}
      ["typos"] {}
      ["detect-secrets"] {}
    }
  }

  ["pre-push"] {
    steps {
      ["npm-audit"] {}
    }
  }
}
```

### Custom Shell Scripts

```pkl
amends "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Config.pkl"

import "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Builtins.pkl"

linters {
  ["shellcheck"] = (Builtins.linters["shellcheck"]) {
    glob = "**/*.sh"
  }

  ["shfmt"] = (Builtins.linters["shfmt"]) {
    glob = "**/*.sh"
  }

  ["shell-test"] {
    glob = "**/*.sh"
    check = "bash -n {file}"  // Syntax check only
  }
}

hooks {
  ["pre-commit"] {
    fix = true
    steps {
      ["shfmt"] {}
      ["shellcheck"] {}
      ["shell-test"] {}
    }
  }
}
```

## Integration Examples

### With mise-en-place

```pkl
// hk.pkl
amends "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Config.pkl"

import "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Builtins.pkl"

linters = Builtins.linters.toMap()

hooks {
  ["pre-commit"] {
    steps {
      ["prettier"] {}
      ["eslint"] {}
    }
  }
}
```

```toml
# .mise.toml
[tools]
hk = "latest"
pkl = "latest"
node = "20"
prettier = "latest"

[tasks.lint]
run = "hk check --all"

[tasks.fix]
run = "hk fix --all"

[tasks.setup]
run = "hk install"
```

### CI/CD Integration

```yaml
# .github/workflows/lint.yml
name: Lint

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install mise
        uses: jdx/mise-action@v2

      - name: Run hk check
        run: hk check --all --fail-fast
```

### Pre-commit with Auto-fix

```pkl
amends "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Config.pkl"

linters {
  ["format"] {
    glob = "**/*.{js,ts,py,rs,go}"
    fix = "prettier --write {files}"
  }

  ["lint"] {
    glob = "**/*.{js,ts}"
    check = "eslint {files}"
    fix = "eslint --fix {files}"
    stage = "**/*.{js,ts}"  // Auto-stage fixed files
  }
}

hooks {
  ["pre-commit"] {
    fix = true  // Enable auto-fix
    stash = "git"  // Preserve unstaged changes
    steps {
      ["format"] {}
      ["lint"] {}
    }
  }
}
```

## Performance Optimization Examples

### Maximum Parallelism

```pkl
amends "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Config.pkl"

jobs = 0  // Auto-detect CPU count
check_first = false  // Skip check, go straight to fix

linters {
  ["parallel-lint"] {
    glob = "**/*.js"
    check = "eslint {files}"
    batch = true  // Process multiple files per command
    parallel = true  // Run in parallel with other steps
  }
}
```

### Minimal Local Checks, Comprehensive CI

```pkl
amends "package://github.com/jdx/hk/releases/download/v1.20.0/hk@1.20.0#/Config.pkl"

linters {
  ["format-local"] {
    glob = "**/*.ts"
    fix = "prettier --write {files}"
  }

  ["lint-local"] {
    glob = "**/*.ts"
    check = "eslint {files}"
  }

  ["test-ci"] {
    glob = "**/*.ts"
    check = "npm test"
    condition = "env.CI == 'true'"
  }

  ["coverage-ci"] {
    glob = "**/*.ts"
    check = "npm run test:coverage"
    condition = "env.CI == 'true'"
  }
}

hooks {
  ["pre-commit"] {
    fix = true
    steps {
      ["format-local"] {}
      ["lint-local"] {}
    }
  }

  ["check"] {
    steps {
      ["format-local"] {}
      ["lint-local"] {}
      ["test-ci"] {}
      ["coverage-ci"] {}
    }
  }
}
```

These examples demonstrate common hk configurations for various project types and use cases. Adapt them to your specific needs by modifying glob patterns, commands, and hook configurations.
