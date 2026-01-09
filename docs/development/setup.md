# Development Setup

Guide for setting up a mock-api development environment.

## Quick Start

```bash
git clone https://github.com/sudzxd/mock-api
cd mock-api
make dev
make hooks-install
make check
```

## Prerequisites

- Python 3.11 or higher
- Git
- Make (pre-installed on macOS/Linux)

## Environment Setup

### Using uv (Recommended)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

uv pip install -e ".[dev]"
```

### Using pip

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
pip install -e ".[dev]"
```

## Pre-commit Hooks

Install hooks to run checks before each commit:

```bash
pre-commit install
```

Hooks run automatically on `git commit`. Manual run:

```bash
pre-commit run --all-files
```

## Verify Setup

```bash
make check  # Run all quality checks
```

All commands should pass.

## Makefile Commands

| Command           | Description               |
| ----------------- | ------------------------- |
| `make dev`        | Install all dependencies  |
| `make test`       | Run tests with coverage   |
| `make lint`       | Run linter                |
| `make lint-fix`   | Fix lint issues           |
| `make format`     | Format code               |
| `make type-check` | Type checking             |
| `make check`      | Run all quality checks    |
| `make quick`      | Fast check (lint + tests) |
| `make pre-commit` | Pre-commit checks         |
| `make ci`         | CI pipeline simulation    |
| `make clean`      | Remove build artifacts    |
| `make run`        | Run example server        |
| `make benchmark`  | Run benchmarks            |
| `make help`       | Show all commands         |

## Project Structure

```
mock-api/
├── mock_api/          # Source code
│   ├── cli/           # CLI commands
│   ├── core/          # Core logic
│   ├── integrations/  # External integrations
│   └── utils/         # Utilities
├── tests/             # Test suite
├── docs/              # Documentation
├── examples/          # Example projects
└── pyproject.toml     # Project configuration
```

## Development Workflow

1. **Create feature branch** off `develop`
2. **Make changes** following the [guidelines](guidelines.md)
3. **Run checks:** `make check`
4. **Commit:** `git commit -m "feat: add feature"`
5. **Push and create PR:** `gh pr create --base develop`

## VS Code Setup

Recommended extensions:

- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Ruff (charliermarsh.ruff)

Settings (`.vscode/settings.json`):

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true
  },
  "python.testing.pytestEnabled": true
}
```

## Common Tasks

### Add New Dependency

```bash
uv pip install <package>
# Update pyproject.toml manually
make dev
```

### Run Local Server

```bash
make run  # Runs basic example
# or
mock-api serve --models examples/blog/models.py --generate-data --reload
```

### Clean Build Artifacts

```bash
make clean       # Remove build artifacts
make clean-all   # Deep clean (including venv)
```

### View Project Info

```bash
make info     # Project information
make version  # Version information
make deps     # Dependency tree
```

## Getting Help

- Check [guidelines](guidelines.md)
- Read [testing guide](testing.md)
- Review existing code
- Open GitHub Issues
