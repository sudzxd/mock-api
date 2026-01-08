# Project Style Guide

This document outlines the coding style and conventions for the mock-api project. All contributors and tools (including GitHub Copilot) must adhere to these standards.

---

## General Coding Standards

### PEP 8 Compliance

We use Ruff to enforce PEP compliance throughout the codebase and expect all code to adhere to the following standards:

- Follow [PEP 8](https://peps.python.org/pep-0008/) guidelines for Python code.

### Line Width

- Maximum line width: **88 characters**.
- Use consistent line breaks to maintain readability.

### Indentation

- Use **4 spaces** per indentation level.
- Do not use tabs.

### Spelling Convention

- Use **American English** spellings throughout the codebase.
- Examples of preferred spellings:
  - `behavior` not `behaviour`
  - `initialize` not `initialise`
  - `synchronize` not `synchronise`
  - `serialize` not `serialise`

---

## Docstring Style

### General Docstring Guidelines

- All public functions, classes, and modules must have docstrings.
- Use **Google-style** docstrings for documentation.
- Private functions (prefixed with `_`) should have docstrings if their logic is non-trivial.

### Google-Style Docstring Example

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

**Key Points:**
- There's no need to include type hints again in the docstring, as they are already present in the function signature.
- The function signature is authoritative for types.
- Include examples for public API functions to show typical usage.

---

## Type Hints

### Use Primitive Types Where Available

- Use primitive types (`list`, `dict`, `tuple`, `set`) instead of their `typing` module equivalents.
- Prefer `list[str]` over `List[str]` (Python 3.9+)
- Prefer `dict[str, int]` over `Dict[str, int]` (Python 3.9+)
- Prefer `tuple[str, int]` over `Tuple[str, int]` (Python 3.9+)
- Use `T | None` instead of `Optional[T]` (Python 3.10+)
- Use `str | int` instead of `Union[str, int]` (Python 3.10+)

**Good:**

```python
def process_messages(items: list[str]) -> dict[str, int]:
    """Process list of items and return counts."""
    return {item: len(item) for item in items}

def get_config(name: str) -> dict[str, str] | None:
    """Get config by name, returns None if not found."""
    return None
```

**Avoid:**

```python
from typing import Dict, List, Optional

def process_messages(items: List[str]) -> Dict[str, int]:
    """Process list of items and return counts."""
    return {item: len(item) for item in items}

def get_config(name: str) -> Optional[Dict[str, str]]:
    """Get config by name, returns None if not found."""
    return None
```

### Exception: Use `typing` for Complex Types

Continue using `typing` module for complex type constructs:

- `typing.Any` (no primitive equivalent)
- `typing.TypeVar` (for generics)
- `typing.Generic` (for generic classes)
- `typing.Protocol` (for structural subtyping)
- `typing.Callable[[str], bool]` (function types)

### Minimum Python Version: 3.11

Since we target Python 3.11+:
- Use `list[T]`, `dict[K, V]`, `tuple[T, ...]`, `set[T]`
- Use `|` union syntax directly (Python 3.10+ feature, but we require 3.11)

---

## Type Safety and Data Structures

### Use Dataclasses or Pydantic for Structured Data

**Rule: Always use typed dataclasses instead of raw dictionaries for application data.**

Working with raw dictionaries (`dict[str, Any]`) in application logic is not type-safe and should be avoided. Use strongly-typed dataclasses to ensure:

- Type checking catches errors at development time
- IDE autocomplete and refactoring support
- Clear contracts between components
- Self-documenting code

**Good:**

```python
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
```

**Avoid:**

```python
def generate_entity(schema: dict[str, Any]) -> dict:
    """Generate entity without type safety."""
    return {"name": schema["name"], "value": schema["default"]}
```

---

## Test Naming Conventions

- Test function names must be descriptive and use lowercase with underscores.
- Test names should clearly state the scenario and expected outcome.
- Use the following pattern for test names:

  ```
  test_<unit_of_work>_<scenario>_<expected_result>
  ```

  **Examples:**

  - `test_parser_with_pydantic_model_extracts_fields`
  - `test_generator_with_email_field_creates_valid_email`
  - `test_store_create_increments_next_id`

- Avoid generic names like `test_something` or `test_case1`.
- The test name should make it clear what is being tested and what the expected behavior is.

---

## Module Organization

### Domain-Driven Module Structure

All modules should follow a consistent organization that prioritizes the "need-to-know" principle. Sections are ordered from most important (public API) to least important (implementation details).

#### Recommended Section Order

```python
"""Module docstring describing domain responsibility."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone

# Third-party
from pydantic import BaseModel
from faker import Faker

# Project/local
from .base import BaseGenerator

# =============================================================================
# TYPES & CONSTANTS
# =============================================================================
DEFAULT_SEED_COUNT = 10
DEFAULT_LOCALE = "en_US"

# =============================================================================
# PUBLIC API
# =============================================================================
def generate_value(field: FieldSchema) -> Any:
    """Generate realistic fake data for a field."""
    pass

# =============================================================================
# CORE CLASSES
# =============================================================================
class DataGenerator:
    """Generate realistic fake data based on field schemas."""
    pass

# =============================================================================
# PRIVATE HELPERS
# =============================================================================
def _detect_field_type(field_name: str) -> str | None:
    """Detect field type from name patterns."""
    pass
```

#### Rationale

- **Need-to-know**: Readers see the module's interface immediately
- **API-driven**: Public functions define what the module does
- **Top-down reading**: Start with high-level concepts, drill down to implementation
- **Maintainability**: Easy to identify what can be refactored vs what's part of the public contract
- **Consistency**: Same pattern across all domain modules

---

## SOLID Principles in Practice

This library is explicitly designed around SOLID principles:

### Single Responsibility Principle (SRP)
- `SchemaParser` handles **only schema parsing**, not data generation
- `DataGenerator` handles **only fake data generation**, not storage
- `Store` handles **only CRUD operations**, not route generation
- `RouteGenerator` handles **only FastAPI route creation**, not business logic

### Open/Closed Principle (OCP)
- New schema sources (TypeScript, OpenAPI) extend `SchemaParser` without modifying core
- New data generators can be plugged in without changing existing code
- Use abstract base classes to enforce contracts

### Liskov Substitution Principle (LSP)
- All schema parsers return the same `ModelSchema` type
- Different storage backends can be swapped transparently
- Clients depend on interfaces, not implementations

### Interface Segregation Principle (ISP)
- Small, focused interfaces (e.g., `Parser`, `Generator`, `Store`)
- Clients depend only on methods they use
- No "fat interfaces" with unused methods

### Dependency Inversion Principle (DIP)
- High-level modules (CLI, Server) depend on abstractions (interfaces)
- Low-level modules (implementations) depend on the same abstractions
- Use dependency injection for testability

---

## Error Handling

### Fail Fast, Fail Clear

- Validate inputs at function entry points
- Raise descriptive exceptions with actionable error messages
- Use built-in exception types when appropriate (`ValueError`, `TypeError`, `KeyError`)

**Good:**

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

**Avoid:**

```python
def parse_file(file_path: str) -> dict[str, ModelSchema]:
    """Parse Pydantic models from a Python file."""
    # Silently fails or crashes later with obscure error
    return {}
```

---

## Performance Guidelines

### Optimization Principles

1. **Measure First**: Always profile before optimizing
2. **Lazy Evaluation**: Generate data only when needed
3. **Cache Results**: Reuse parsed schemas and generated data
4. **Simple is Fast**: Prefer straightforward code; complexity rarely pays off

### Common Patterns

```python
class Store:
    """Store with caching pattern."""

    def __init__(self, schemas: dict[str, ModelSchema]):
        """Initialize with schemas."""
        self.schemas = schemas
        self._cache: dict[str, list[dict]] = {}

    def get_all(self, model_name: str) -> list[dict]:
        """Get all entities with caching."""
        if model_name not in self._cache:
            self._cache[model_name] = self._load_data(model_name)
        return self._cache[model_name]
```

---

## Git Commit Convention

- Use clear, descriptive commit messages
- Follow the format: `<type>: <description>`
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples:**

- `feat: add TypeScript schema parser`
- `fix: handle None values in data generator`
- `refactor: extract route generation to separate class`
- `docs: add examples for CLI usage`
- `test: add edge case coverage for foreign key detection`

---

## Questions?

If you're unsure about any style conventions, check this guide first. When in doubt:
1. Follow PEP 8
2. Prioritize type safety
3. Keep it simple (YAGNI - You Aren't Gonna Need It)
4. Make it obvious (explicit is better than implicit)
