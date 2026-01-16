# CLAUDE.md - AI Assistant Guide

**For AI assistants working on the mockapi-server codebase**

## What This Project Does

**mockapi-server** generates full-featured REST APIs from Pydantic models in seconds.

Parse Pydantic models → Generate fake data → Create REST endpoints → Handle CRUD operations

**Tech Stack:** Python 3.11+ | Pydantic v2 | FastAPI | Click CLI | Faker | Pytest

**Repository:** <https://github.com/sudzxd/mockapi-server>

## Where to Find Information

### For Implementation Tasks

- **Architecture & Components:** `docs/architecture.md` - SOLID principles, component diagram, data flow
- **Code Style & Workflow:** `docs/development/guidelines.md` - Git workflow, code conventions, SOLID principles
- **Testing Strategy:** `docs/development/testing.md` - Test patterns, coverage targets
- **Dev Setup:** `docs/development/setup.md` - Environment setup, make commands

### For Troubleshooting

- **Common Issues:** `docs/troubleshooting.md`
- **FAQ:** `docs/faq.md`
- **Examples:** `examples/` directory (basic, blog, ecommerce)

### For Users

- **Getting Started:** `docs/getting-started.md`
- **CLI Reference:** `docs/cli-reference.md`
- **API Reference:** `docs/api-reference.md`

## Project Structure (DDD Architecture)

```
mock_api/
├── cli/                # Click commands (serve, generate, validate)
├── core/               # Facades & orchestration (parser, generator, store, router, server)
├── domain/             # Protocols & interfaces (schema, storage, generation, export, middleware)
├── implementations/    # Concrete implementations (parsing, storage, generation)
├── integrations/       # External integrations
└── utils/              # Utilities (logger, etc)
tests/                  # Unit tests + benchmarks
docs/                   # All documentation
examples/               # Example projects
```

**Architecture Layers:**
- **CLI:** User interface commands
- **Core:** Facades that delegate to implementations (future multi-implementation support)
- **Domain:** Protocol interfaces defining contracts for all extension points
- **Implementations:** Concrete implementations (PydanticParser, FakerGenerator, InMemoryRepository)

## Critical Quick Reference

### Type Hints (Python 3.11+ - NO Legacy Typing)

```python
# ✓ Use modern syntax
def process(items: list[str]) -> dict[str, int]:
    name: str | None = None

# ✗ Never use legacy typing
from typing import List, Dict, Optional  # DON'T IMPORT THESE
```

**Rules:** `list[T]`, `dict[K,V]`, `T | None`, `str | int` (NOT List, Dict, Optional, Union)

**Exception:** Only import from typing: `Any`, `TypeVar`, `Generic`, `Protocol`, `Callable`

### Git Workflow

- **Branch:** `<type>/<initials>/<issue>-<desc>` (e.g., `feat/ss/42-add-config`)
- **Commit:** `<type>: <description>` (e.g., `feat: add TypeScript parser`)
- **Types:** feat, fix, docs, style, refactor, test, chore
- **Target:** Always branch off and PR to `develop`

### Testing

- **Naming:** `test_<component>_<scenario>_<expected>()`
- **Coverage:** Overall 90%+, Parser 95%+, Store 100%
- **Commands:** `make test` (with coverage), `make test-fast`, `make check` (full validation)

### Common Commands

- **Setup:** `make dev` → `make hooks-install` → `make check`
- **Development:** `make test`, `make lint`, `make format`, `make type-check`
- **Full Check:** `make check` (run before every commit/PR)
- **All Commands:** `make help`

## For AI Assistants: Decision Tree

### When Asked to Add a Feature

1. Read `docs/architecture.md` to understand component architecture
2. Read `docs/development/guidelines.md` for code style
3. Check `examples/` for similar patterns
4. Write code following modern Python 3.11+ syntax
5. Add tests (see `docs/development/testing.md`)
6. Run `make check`
7. Follow git workflow: branch → commit → PR to `develop`

### When Asked to Fix a Bug

1. Check `docs/troubleshooting.md` for known issues
2. Read relevant test files in `tests/` to understand expected behavior
3. Fix the issue
4. Add regression test
5. Run `make check`

### When Asked to Update Documentation

1. Check existing docs structure (see "Where to Find Information" above)
2. Follow concise style - no duplication across docs
3. Update only what's necessary
4. Verify links and examples work

### When Reviewing Code

Verify:
- Modern type hints (no `List`, `Dict`, `Optional`)
- Test coverage meets targets
- Follows SOLID principles (see `docs/architecture.md`)
- Google-style docstrings
- Conventional commit messages
- All `make check` passes

## Critical Rules

1. **Always read relevant docs before making changes** (don't guess)
2. **Never use legacy typing** (List, Dict, Optional, Union)
3. **Run `make check` before every commit**
4. **Add tests for all new features** (non-negotiable)
5. **Branch off `develop`**, not `main`
6. **Use conventional commits** (feat:, fix:, etc.)
