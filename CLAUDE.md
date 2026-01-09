# CLAUDE.md - AI Assistant Guide

**For AI assistants working on the mock-api codebase**

## Project Overview

**mock-api** generates full-featured REST APIs from Pydantic models in seconds.

**Core Functionality:**

- Parse Pydantic models → Extract schema
- Generate realistic fake data based on field types
- Create FastAPI REST endpoints automatically
- Handle CRUD operations with in-memory storage
- Auto-detect foreign key relationships

**Key Features:**

- Zero configuration required
- Type-safe (Pydantic v2 validation)
- Smart data generation (semantic field matching)
- Auto-relationship detection (e.g., `author_id` → `User`)
- OpenAPI docs at `/docs`
- Stateful in-memory storage

**Tech Stack:**

- Python 3.11+ (modern type hints: `list[str]`, `T | None`)
- Pydantic v2 (schema validation)
- FastAPI (REST API framework)
- Click (CLI)
- Faker (data generation)
- Pytest (testing)

**Status:** Under active development

**Repository:** <https://github.com/sudzxd/mock-api>

## Documentation Structure

**Recently cleaned and streamlined (2,809 lines, 41% reduction)**

### Root Files

- `README.md` - Project overview, quick start, features
- `CONTRIBUTING.md` - Contribution guide, quick setup
- `CHANGELOG.md` - Version history
- `CODE_OF_CONDUCT.md` - Community guidelines

### User Documentation (`docs/`)

- `index.md` - Navigation hub
- `getting-started.md` - Installation, first API in 5 min
- `cli-reference.md` - Complete command reference (328 lines)
- `api-reference.md` - Python API + REST endpoints (522 lines)
- `examples.md` - Real-world patterns (blog, frontend integration)
- `faq.md` - 10 critical questions
- `troubleshooting.md` - Common issues and solutions
- `architecture.md` - SOLID principles, component diagram, data flow

### Development Documentation (`docs/development/`)

- `setup.md` - Dev environment setup, make commands
- `guidelines.md` - Git workflow, code style, SOLID principles (merged from best-practices + style-guide)
- `testing.md` - Testing practices, coverage targets
- `releasing.md` - Release process, versioning

## Project Structure

```
mock-api/
├── mock_api/              # Source code
│   ├── cli/               # CLI commands (Click)
│   │   ├── main.py        # Entry point, command groups
│   │   ├── init.py        # Init command
│   │   ├── serve.py       # Serve command
│   │   ├── generate.py    # Generate command
│   │   └── validate.py    # Validate command
│   ├── core/              # Core business logic
│   │   ├── parser.py      # SchemaParser: Pydantic → ModelSchema
│   │   ├── generator.py   # DataGenerator: Schema → Fake data
│   │   ├── store.py       # DataStore: In-memory CRUD
│   │   ├── router.py      # RouteGenerator: Schema → FastAPI routes
│   │   └── server.py      # Server: Orchestrator
│   ├── integrations/      # External integrations
│   └── utils/             # Utilities, logging
├── tests/                 # Test suite
│   ├── conftest.py        # Shared fixtures
│   ├── fixtures/          # Test data models
│   ├── test_*.py          # Unit tests
│   └── benchmarks/        # Performance tests
├── docs/                  # Documentation (see above)
├── examples/              # Example projects
│   ├── basic/
│   ├── blog/
│   └── ecommerce/
├── pyproject.toml         # Project configuration
├── Makefile               # Development commands
└── mkdocs.yml             # Documentation site config
```

## Development Conventions

### Git Workflow

**Branch Naming:**

```
<type>/<initials>/<issue-number>-<description>
```

Examples: `feat/ss/1-add-config`, `fix/ss/5-typescript-parser`

**Commit Messages (Conventional Commits):**

```
<type>: <description>

[optional body]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example: `feat: add TypeScript model generator`

**Workflow:**

1. Branch off `develop`
2. Make changes
3. Run `make check`
4. Commit with conventional format
5. Create PR to `develop`

**Pre-commit Hooks (automatic):**
- Ruff linting/formatting
- Trailing whitespace removal
- YAML/TOML validation
- Spell checking
- Commit message format validation

### Code Style

**Type Hints (Python 3.11+):**

```python
# Good
def process(items: list[str]) -> dict[str, int]:
    name: str | None = None

# Avoid
from typing import List, Dict, Optional
def process(items: List[str]) -> Dict[str, int]:
    name: Optional[str] = None
```

**Rules:**

- Use `list[T]` not `List[T]`
- Use `dict[K, V]` not `Dict[K, V]`
- Use `T | None` not `Optional[T]`
- Use `str | int` not `Union[str, int]`
- Exception: `Any`, `TypeVar`, `Generic`, `Protocol`, `Callable` from `typing`

**Docstrings (Google-style):**

```python
def generate_value(field: FieldSchema) -> Any:
    """Generate realistic fake data for a field.

    Args:
        field: Field schema containing name and type information.

    Returns:
        Generated value appropriate for the field type.

    Example:
        >>> field = FieldSchema(name="email", type=str)
        >>> value = generate_value(field)
        >>> "@" in value
        True
    """
```

**Formatting:**

- Line length: 88 characters
- Indentation: 4 spaces
- American English spelling
- Ruff for formatting/linting

### Testing

**Test Naming:**

```
test_<component>_<scenario>_<expected>
```

Example: `test_parser_with_valid_models_extracts_all_fields()`

**Coverage Targets:**

- Overall: 90%+
- Parser: 95%+
- Generator: 90%+
- Store: 100%
- Router: 95%+

**Commands:**

```bash
make test          # Tests with coverage
make test-fast     # Fast (no coverage)
make benchmark     # Performance tests
```

### SOLID Principles (Brief)

- **Single Responsibility:** Each class handles one concern (Parser parses, Generator generates, Store stores)
- **Open/Closed:** Extend via interfaces without modifying core
- **Liskov Substitution:** All implementations return same types, swappable
- **Interface Segregation:** Small, focused interfaces
- **Dependency Inversion:** Depend on abstractions, use dependency injection

## Architecture Quick Reference

### Components

```
CLI Layer (Click)
    ↓
Server (Orchestrator)
    ↓
    ├── SchemaParser:    Pydantic → ModelSchema
    ├── DataGenerator:   ModelSchema → Fake data
    ├── DataStore:       In-memory CRUD operations
    └── RouteGenerator:  ModelSchema → FastAPI routes
    ↓
FastAPI Application
```

**SchemaParser:**

- Input: Python file path
- Output: `dict[str, ModelSchema]`
- Extracts Pydantic models, detects FKs (`author_id` → `User`)

**DataGenerator:**

- Input: ModelSchema, count
- Output: `list[dict]`
- Generates realistic data based on field names (email, name, phone)

**DataStore:**

- Input: Model name, data
- Output: Data or None
- In-memory `dict[model_name, list[dict]]`, CRUD operations

**RouteGenerator:**

- Input: ModelSchema, DataStore
- Output: FastAPI router
- Generates GET, POST, PUT, DELETE endpoints

**Server:**

- Orchestrates all components
- Configures FastAPI, CORS, OpenAPI docs

### Data Flow

```
models.py → SchemaParser → ModelSchema[] → DataGenerator → Fake Data[] → DataStore
                                                                            ↓
Client Request → FastAPI Router → Route Handler → DataStore (CRUD) → Response
```

### Extension Points

- Custom generators: Implement custom data generation
- Custom storage: Replace in-memory with database
- Custom parsers: Add TypeScript, OpenAPI support

## Common Tasks

### Setup Dev Environment

```bash
git clone https://github.com/sudzxd/mock-api
cd mock-api
make dev                # Install dependencies
make hooks-install      # Install pre-commit hooks
make check              # Verify setup
```

### Run Tests

```bash
make test               # Tests with coverage
make test-fast          # Fast (no coverage)
make lint               # Run linter
make format             # Format code
make type-check         # Type checking
make check              # All quality checks
make ci                 # CI simulation
```

### Add New Feature

1. Create branch: `git checkout -b feat/ss/123-feature-name`
2. Make changes following guidelines
3. Add tests (coverage required)
4. Run `make check`
5. Commit: `git commit -m "feat: add feature"`
6. Create PR to `develop`

### Create Release (Maintainers)

```bash
# 1. Create release branch
git checkout -b release/v0.1.0

# 2. Update version in pyproject.toml
# 3. Update CHANGELOG.md

# 4. Create PR to main, merge
gh pr create --base main
gh pr merge --merge

# 5. Tag release
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0  # Triggers PyPI release

# 6. Merge back to develop
git checkout develop
git merge main
git push
```

### Common Troubleshooting

**Import errors:** `pip install -e ".[dev]"`

**Port in use:** `mock-api serve --models models.py --port 8000`

**CORS errors:** Enable in `mock-api.yml`:

```yaml
cors_enabled: true
cors_origins: ["*"]
```

**See:** `docs/troubleshooting.md` for full guide

## Key Files Reference

### CLI

- `mock_api/cli/main.py` - Entry point, command groups
- `mock_api/cli/init.py` - Project initialization
- `mock_api/cli/serve.py` - Server command
- `mock_api/cli/generate.py` - Data generation command
- `mock_api/cli/validate.py` - Model validation command

### Core

- `mock_api/core/parser.py` - SchemaParser: Parse Pydantic models
- `mock_api/core/generator.py` - DataGenerator: Generate fake data
- `mock_api/core/store.py` - DataStore: In-memory CRUD
- `mock_api/core/router.py` - RouteGenerator: Create FastAPI routes
- `mock_api/core/server.py` - Server: Orchestrate components

### Tests

- `tests/conftest.py` - Shared pytest fixtures
- `tests/test_parser.py` - Parser tests
- `tests/test_generator.py` - Generator tests
- `tests/test_store.py` - Store tests
- `tests/test_router.py` - Router tests
- `tests/test_server.py` - Server tests
- `tests/benchmarks/` - Performance benchmarks

### Configuration

- `pyproject.toml` - Project metadata, dependencies
- `Makefile` - Development commands
- `mkdocs.yml` - Documentation site configuration
- `.pre-commit-config.yaml` - Pre-commit hooks

## Make Commands Reference

| Command           | Description               |
| ----------------- | ------------------------- |
| `make dev`        | Install all dependencies  |
| `make test`       | Run tests with coverage   |
| `make test-fast`  | Fast tests (no coverage)  |
| `make lint`       | Run linter                |
| `make lint-fix`   | Auto-fix lint issues      |
| `make format`     | Format code               |
| `make type-check` | Type checking             |
| `make check`      | All quality checks        |
| `make quick`      | Fast check (lint + tests) |
| `make pre-commit` | Pre-commit checks         |
| `make ci`         | CI pipeline simulation    |
| `make benchmark`  | Run benchmarks            |
| `make clean`      | Remove build artifacts    |
| `make run`        | Run example server        |
| `make help`       | Show all commands         |

## Quick Links

- **GitHub:** <https://github.com/sudzxd/mock-api>
- **Issues:** <https://github.com/sudzxd/mock-api/issues>
- **PyPI:** <https://pypi.org/project/mock-api/>
- **Docs:** See `docs/` directory
- **Examples:** See `examples/` directory

## For AI Assistants

**When asked to:**

- **Add feature:** Check architecture.md, follow guidelines.md conventions
- **Fix bug:** Check troubleshooting.md first, add test
- **Update docs:** Follow concise style, no duplication
- **Review code:** Verify type hints, coverage, SOLID principles
- **Create PR:** Follow branch naming, conventional commits

**Always:**

1. Read relevant docs before making changes
2. Run `make check` before committing
3. Add tests for new features
4. Update documentation if needed
5. Follow SOLID principles
6. Use modern Python 3.11+ syntax
