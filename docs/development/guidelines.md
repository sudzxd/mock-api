# Development Guidelines

Development conventions and guidelines for mock-api contributors.

## Git Workflow

### Branch Naming

Create all branches off `develop`:

```
<type>/<initials>/<issue-number>-<description>
```

**Components:**

- **type**: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
- **initials**: Your initials (e.g., `ss`)
- **issue-number**: GitHub issue number
- **description**: Short kebab-case description

**Examples:**

```bash
feat/ss/1-add-config
fix/ss/5-typescript-parser
docs/ss/4-getting-started
```

### Commit Messages

Follow conventional commits:

```
<type>: <description>

[optional body]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples:**

```
feat: add TypeScript model generator
fix: handle nested optional fields correctly
docs: update CLI reference for new options
```

**Guidelines:**

- Keep subject line under 72 characters
- Use imperative mood ("add" not "added")
- Don't end subject with period
- Explain what and why, not how

### Development Flow

```bash
# 1. Start from develop
git checkout develop
git pull origin develop

# 2. Create feature branch
git checkout -b feat/ss/1-add-config

# 3. Run quality checks
make check

# 4. Commit and push
git add .
git commit -m "feat: add configuration system"
git push origin feat/ss/1-add-config

# 5. Create PR to develop
gh pr create --base develop
```

### Pre-commit Hooks

Hooks run automatically on commit (see [setup.md](setup.md) for installation).

**What they do:**
- Ruff linting and formatting
- Trailing whitespace removal
- YAML/TOML validation
- Spell checking
- Commit message format validation (conventional commits)

Manual run:

```bash
make pre-commit  # Run all hooks
```

## Code Style

### Type Hints

Use modern Python 3.11+ syntax:

```python
# Good
def process(items: list[str]) -> dict[str, int]:
    result: dict[str, int] = {}
    name: str | None = None
    return result

# Avoid
from typing import Dict, List, Optional

def process(items: List[str]) -> Dict[str, int]:
    result: Dict[str, int] = {}
    name: Optional[str] = None
    return result
```

**Use primitive types:**

- `list[str]` not `List[str]`
- `dict[K, V]` not `Dict[K, V]`
- `T | None` not `Optional[T]`
- `str | int` not `Union[str, int]`

**Exception:** Use `typing` for complex types (`Any`, `TypeVar`, `Generic`, `Protocol`, `Callable`)

### Docstrings

Use Google-style docstrings:

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
    pass
```

**Guidelines:**

- All public functions, classes, and modules must have docstrings
- Don't repeat type information (already in signature)
- Include examples for public API functions

### Module Organization

```python
"""Module docstring describing domain responsibility."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
import json
from datetime import datetime

# Third-party
from pydantic import BaseModel

# Project/local
from .base import BaseClass

# =============================================================================
# TYPES & CONSTANTS
# =============================================================================
DEFAULT_COUNT = 10

# =============================================================================
# PUBLIC API
# =============================================================================
def public_function():
    """Public function."""
    pass

# =============================================================================
# CORE CLASSES
# =============================================================================
class MyClass:
    """Main class."""
    pass

# =============================================================================
# PRIVATE HELPERS
# =============================================================================
def _private_helper():
    """Private helper."""
    pass
```

### Formatting

- Line length: 88 characters
- Use 4 spaces for indentation
- American English spelling
- Ruff for formatting and linting

```bash
make format       # Auto-format
make lint         # Check linting
make lint-fix     # Auto-fix issues
```

## Type Safety

### Use Dataclasses for Structured Data

Always use typed dataclasses instead of raw dictionaries:

```python
# Good
from dataclasses import dataclass

@dataclass
class FieldSchema:
    """Schema for a model field."""
    name: str
    type: type
    is_optional: bool
    default: Any = None

def generate_entity(schema: FieldSchema) -> dict:
    """Generate entity with type-safe configuration."""
    return {"name": schema.name, "value": schema.default}

# Avoid
def generate_entity(schema: dict[str, Any]) -> dict:
    """Generate entity without type safety."""
    return {"name": schema["name"], "value": schema["default"]}
```

## Testing Practices

### Test Naming

```
test_<component>_<scenario>_<expected>
```

**Examples:**

```python
def test_parser_with_valid_models_extracts_all_fields():
    """Parser should extract all fields from valid Pydantic models."""
    pass

def test_generator_with_email_field_creates_valid_email():
    """Generator should create valid email for fields named 'email'."""
    pass
```

### Test Structure

```python
def test_feature():
    """Test description."""
    # Arrange - Set up test data
    parser = SchemaParser()

    # Act - Perform the action
    result = parser.parse_file("test.py")

    # Assert - Verify the outcome
    assert result is not None
    assert len(result) > 0
```

### Coverage Targets

- Overall: 90%+
- Critical components (Parser, Store): 95%+
- New features: 100%

```bash
make test         # Run tests with coverage
make test-cov     # View HTML report
```

## SOLID Principles

**Single Responsibility:** Each class handles one concern (SchemaParser parses, DataGenerator generates, Store stores)

**Open/Closed:** Extend via interfaces (new parsers, generators, storage backends) without modifying core

**Liskov Substitution:** All implementations return same types, can be swapped transparently

**Interface Segregation:** Small, focused interfaces - clients depend only on what they use

**Dependency Inversion:** High-level modules depend on abstractions, use dependency injection

## Error Handling

Fail fast with clear messages:

```python
def parse_file(file_path: str) -> dict[str, ModelSchema]:
    """Parse Pydantic models from a Python file."""
    if not Path(file_path).exists():
        raise FileNotFoundError(
            f"Schema file not found: {file_path}"
        )
    if not file_path.endswith('.py'):
        raise ValueError(
            f"Schema file must be a Python file (.py), got: {file_path}"
        )
    return {}
```

## Performance

### Principles

1. **Measure First**: Always profile before optimizing
2. **Lazy Evaluation**: Generate data only when needed
3. **Cache Results**: Reuse parsed schemas and generated data
4. **Simple is Fast**: Prefer straightforward code

### Benchmarking

```bash
make benchmark           # Run benchmarks
make benchmark-compare   # Compare with baseline
```

### Performance Targets

- Parser: < 10ms for 10 models
- Generator: < 100ms for 100 entities
- Store: 1000 ops/sec
- Server startup: < 1s

## Security

```bash
make security  # Run security audit
```
