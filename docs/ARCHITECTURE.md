# Mock API - Architecture & Implementation Plan

**Version:** 1.0
**Date:** 2026-01-05
**Status:** In Development

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Project Layout](#2-project-layout)
3. [Architecture Principles](#3-architecture-principles)
4. [Component Architecture](#4-component-architecture)
5. [Data Flow](#5-data-flow)
6. [Implementation Phases](#6-implementation-phases)
7. [Technology Stack](#7-technology-stack)
8. [Quality Standards](#8-quality-standards)
9. [Deployment Strategy](#9-deployment-strategy)
10. [Future Roadmap](#10-future-roadmap)

---

## 1. System Overview

### 1.1 Vision

**Mock API** is a developer tool that generates production-like REST APIs from type definitions, enabling frontend teams to develop independently of backend implementation.

**Core Value Proposition:**

- **Zero Configuration:** Point at schema file → instant API
- **Type-Safe:** Pydantic/TypeScript schemas ensure contract validation
- **Realistic Data:** Smart fake data generation based on field semantics
- **Full CRUD:** Stateful in-memory database with relationships

### 1.2 Target Users

**Primary:**

- Frontend developers waiting on backend APIs
- Full-stack developers prototyping features
- QA engineers testing edge cases

**Secondary:**

- Technical PMs creating product demos
- Bootcamp students learning API development
- Open-source contributors

### 1.3 Use Cases

```
┌─────────────────────────────────────────────────────────────┐
│ Use Case 1: Independent Frontend Development                │
├─────────────────────────────────────────────────────────────┤
│ 1. Backend team defines Pydantic models                     │
│ 2. Frontend team runs: mock-api run models.py               │
│ 3. Frontend develops against mock API                        │
│ 4. Backend implements real API matching Pydantic contract   │
│ 5. Frontend switches to real API (no code changes)          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Use Case 2: QA Testing Edge Cases                           │
├─────────────────────────────────────────────────────────────┤
│ 1. QA runs mock API with --scenario error_cases             │
│ 2. API returns 500 errors, timeouts, malformed data         │
│ 3. QA validates frontend handles errors gracefully          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Use Case 3: Rapid Prototyping                               │
├─────────────────────────────────────────────────────────────┤
│ 1. PM defines data models (10 minutes)                      │
│ 2. Run mock-api → instant API (30 seconds)                  │
│ 3. Demo working prototype to stakeholders (same day)        │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Project Layout

### 2.1 Complete Directory Structure

```
mock-api/
├── .github/                          # GitHub configuration
│   ├── workflows/
│   │   ├── ci.yml                    # CI/CD pipeline
│   │   ├── release.yml               # Release automation
│   │   └── docs.yml                  # Documentation deployment
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── PULL_REQUEST_TEMPLATE.md
│
├── .vscode/                          # VSCode configuration
│   ├── settings.json                 # ✅ Editor settings (Ruff, Pyright)
│   ├── extensions.json               # ✅ Recommended extensions
│   ├── launch.json                   # Debugger configuration
│   └── tasks.json                    # Build tasks
│
├── docs/                             # Documentation
│   ├── index.md                      # Documentation home
│   ├── ARCHITECTURE.md               # ✅ System architecture
│   ├── GAP_ANALYSIS.md               # ✅ Parser gap analysis
│   ├── BUILD_LOG.md                  # ✅ Development log
│   ├── development/
│   │   ├── style-guide.md            # ✅ Coding standards
│   │   ├── contributing.md           # Contribution guide
│   │   ├── testing.md                # Testing strategy
│   │   └── adr/                      # Architecture Decision Records
│   │       ├── 001-use-pydantic.md
│   │       ├── 002-fastapi-choice.md
│   │       └── 003-in-memory-first.md
│   ├── user-guide/
│   │   ├── getting-started.md
│   │   ├── cli-reference.md
│   │   ├── advanced-usage.md
│   │   └── troubleshooting.md
│   ├── api/
│   │   ├── parser.md                 # Parser API docs
│   │   ├── generator.md              # Generator API docs
│   │   ├── store.md                  # Store API docs
│   │   └── router.md                 # Router API docs
│   └── examples/
│       ├── basic-usage.md
│       ├── relationships.md
│       ├── custom-scenarios.md
│       └── typescript-integration.md
│
├── examples/                         # Example projects
│   ├── basic/
│   │   ├── models.py                 # Simple Pydantic models
│   │   ├── README.md
│   │   └── client.html               # Example frontend
│   ├── blog/
│   │   ├── models.py                 # Blog with User, Post, Comment
│   │   ├── README.md
│   │   └── docker-compose.yml
│   ├── ecommerce/
│   │   ├── models.py                 # Product, Order, Cart
│   │   ├── README.md
│   │   └── frontend/
│   ├── typescript/
│   │   ├── types.ts                  # TypeScript definitions
│   │   └── README.md
│   └── advanced/
│       ├── models.py                 # Complex relationships
│       ├── scenarios.py              # Custom scenarios
│       └── README.md
│
├── mock_api/                         # Main package
│   ├── __init__.py                   # Package initialization
│   ├── __version__.py                # Version info
│   │
│   ├── cli/                          # Command-line interface
│   │   ├── __init__.py
│   │   ├── main.py                   # 🚧 Click commands
│   │   ├── commands/
│   │   │   ├── __init__.py
│   │   │   ├── run.py                # mock-api run
│   │   │   ├── init.py               # mock-api init
│   │   │   ├── validate.py           # mock-api validate
│   │   │   └── version.py            # mock-api version
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── console.py            # Rich console helpers
│   │       └── prompts.py            # Interactive prompts
│   │
│   ├── core/                         # Core business logic
│   │   ├── __init__.py
│   │   ├── logger.py                 # ✅ Centralized logging
│   │   ├── parser.py                 # ✅ Schema parser
│   │   ├── generator.py              # 🚧 Data generator
│   │   ├── store.py                  # 🚧 In-memory CRUD
│   │   ├── router.py                 # 🚧 Route generator
│   │   ├── server.py                 # 🚧 FastAPI server
│   │   ├── config.py                 # 🚧 Configuration management
│   │   └── exceptions.py             # 🚧 Custom exceptions
│   │
│   ├── integrations/                 # External integrations
│   │   ├── __init__.py
│   │   ├── pydantic.py               # Pydantic-specific logic
│   │   ├── typescript.py             # 📅 TypeScript parser
│   │   ├── openapi.py                # 📅 OpenAPI parser
│   │   └── graphql.py                # 📅 GraphQL schema parser
│   │
│   ├── scenarios/                    # Testing scenarios
│   │   ├── __init__.py
│   │   ├── base.py                   # 📅 Base scenario class
│   │   ├── errors.py                 # 📅 Error scenarios
│   │   ├── performance.py            # 📅 Slow/timeout scenarios
│   │   └── custom.py                 # 📅 Custom scenario loader
│   │
│   ├── middleware/                   # FastAPI middleware
│   │   ├── __init__.py
│   │   ├── cors.py                   # 📅 CORS configuration
│   │   ├── logging.py                # 📅 Request logging
│   │   ├── auth.py                   # 📅 Authentication
│   │   └── rate_limit.py             # 📅 Rate limiting
│   │
│   └── utils/                        # Utility functions
│       ├── __init__.py
│       ├── validation.py             # 📅 Input validation helpers
│       ├── serialization.py          # 📅 JSON serialization
│       └── text.py                   # 📅 String utilities
│
├── tests/                            # Test suite
│   ├── __init__.py
│   ├── conftest.py                   # Pytest configuration & fixtures
│   │
│   ├── fixtures/                     # Test fixtures
│   │   ├── __init__.py
│   │   ├── test_models.py            # ✅ Sample Pydantic models
│   │   ├── complex_models.py         # 🚧 Complex relationships
│   │   ├── typescript_types.ts       # 📅 TypeScript fixtures
│   │   └── openapi_specs.yaml        # 📅 OpenAPI fixtures
│   │
│   ├── unit/                         # Unit tests
│   │   ├── __init__.py
│   │   ├── test_parser.py            # ✅ Parser tests (12 tests)
│   │   ├── test_logger.py            # 🚧 Logger tests
│   │   ├── test_generator.py         # 🚧 Generator tests
│   │   ├── test_store.py             # 🚧 Store tests
│   │   ├── test_router.py            # 🚧 Router tests
│   │   └── test_server.py            # 🚧 Server tests
│   │
│   ├── integration/                  # Integration tests
│   │   ├── __init__.py
│   │   ├── test_end_to_end.py        # 🚧 Full workflow tests
│   │   ├── test_cli.py               # 🚧 CLI integration
│   │   ├── test_api.py               # 🚧 API endpoint tests
│   │   └── test_relationships.py     # 🚧 Relationship navigation
│   │
│   ├── performance/                  # Performance tests
│   │   ├── __init__.py
│   │   ├── test_parser_perf.py       # 📅 Parser benchmarks
│   │   ├── test_generator_perf.py    # 📅 Generator benchmarks
│   │   └── test_api_perf.py          # 📅 API throughput
│   │
│   └── security/                     # Security tests
│       ├── __init__.py
│       ├── test_injection.py         # 📅 Injection attacks
│       └── test_path_traversal.py    # 📅 Path validation
│
├── scripts/                          # Development scripts
│   ├── setup_dev.sh                  # Development environment setup
│   ├── run_tests.sh                  # Test runner with coverage
│   ├── benchmark.py                  # Performance benchmarking
│   ├── release.py                    # Release automation
│   └── check_quality.sh              # Pre-commit quality checks
│
├── .gitignore                        # ✅ Git ignore patterns
├── .pre-commit-config.yaml           # ✅ Pre-commit hooks
├── .python-version                   # ✅ Python version (3.11)
├── .editorconfig                     # Editor configuration
├── .dockerignore                     # Docker ignore patterns
│
├── pyproject.toml                    # ✅ Project configuration
├── requirements.txt                  # Production dependencies (generated)
├── requirements-dev.txt              # Development dependencies (generated)
├── uv.lock                           # Dependency lock file
│
├── Dockerfile                        # 📅 Docker container definition
├── docker-compose.yml                # 📅 Multi-container setup
├── railway.toml                      # 📅 Railway deployment config
├── vercel.json                       # 📅 Vercel deployment config
│
├── README.md                         # ✅ Project overview
├── LICENSE                           # MIT License
├── CHANGELOG.md                      # Version history
├── CONTRIBUTING.md                   # Contribution guidelines
├── CODE_OF_CONDUCT.md                # Code of conduct
│
└── mkdocs.yml                        # 📅 Documentation site config

Legend:
  ✅ Complete
  🚧 In Progress / Phase 1
  📅 Planned / Future Phases
```

### 2.2 File Descriptions

#### Root Configuration Files

**pyproject.toml**

```toml
# Central configuration for:
# - Project metadata (name, version, description)
# - Dependencies (core + dev)
# - Tool configurations (ruff, pyright, pytest, coverage)
# - Build system (hatchling)
# - Entry points (mock-api CLI command)
```

**uv.lock**

```
# Dependency lock file generated by uv
# Ensures reproducible installs
# Pinned versions of all dependencies
```

**.pre-commit-config.yaml**

```yaml
# Pre-commit hooks:
# - Ruff (format + lint)
# - Trailing whitespace
# - YAML/TOML validation
# - Codespell
# - Pyright (manual stage)
```

**.python-version**

```
# Specifies Python 3.11 requirement
# Used by pyenv, asdf, etc.
```

#### Core Module Files

**mock_api/**init**.py**

```python
"""Mock API - Generate REST APIs from type definitions.

Public API:
    - SchemaParser: Parse Pydantic/TypeScript schemas
    - DataGenerator: Generate realistic fake data
    - MockAPIServer: Run mock API server
"""
from mock_api.core.parser import SchemaParser
from mock_api.core.generator import DataGenerator
from mock_api.core.server import MockAPIServer

__version__ = "0.1.0"
__all__ = ["SchemaParser", "DataGenerator", "MockAPIServer"]
```

**mock_api/core/parser.py** ✅

```python
# Lines: ~365
# Purpose: Parse Pydantic models into internal schema format
# Key classes: FieldSchema, ModelSchema, Relationship, SchemaParser
# Dependencies: Pydantic, importlib, inspect
# Test coverage: 83%
```

**mock_api/core/generator.py** 🚧 NEXT

```python
# Lines: ~300 (estimated)
# Purpose: Generate realistic fake data from schemas
# Key classes: DataGenerator, FieldMapper
# Dependencies: Faker, random, datetime
# Test coverage target: 90%
```

**mock_api/core/store.py** 🚧

```python
# Lines: ~250 (estimated)
# Purpose: In-memory CRUD operations with relationships
# Key classes: Store
# Dependencies: None (pure Python)
# Test coverage target: 100%
```

**mock_api/core/router.py** 🚧

```python
# Lines: ~400 (estimated)
# Purpose: Generate FastAPI routes from schemas
# Key classes: RouteGenerator
# Dependencies: FastAPI, Pydantic
# Test coverage target: 95%
```

**mock_api/core/server.py** 🚧

```python
# Lines: ~200 (estimated)
# Purpose: Orchestrate all components into FastAPI app
# Key classes: MockAPIServer
# Dependencies: FastAPI, Uvicorn
# Test coverage target: 90%
```

#### CLI Files

**mock_api/cli/main.py** 🚧

```python
# Main CLI entry point
# Commands:
#   - run: Start mock API server
#   - init: Interactive project setup
#   - validate: Validate schema file
#   - version: Show version info
```

**mock_api/cli/commands/run.py** 🚧

```python
@click.command()
@click.argument("schema_file", type=click.Path(exists=True))
@click.option("--port", default=3000, help="Port to run on")
@click.option("--seed", default=10, help="Entities per model")
@click.option("--watch", is_flag=True, help="Auto-reload on changes")
def run(schema_file, port, seed, watch):
    """Start mock API server from schema file."""
    pass
```

#### Test Files

**tests/conftest.py**

```python
# Shared pytest fixtures:
# - parser: SchemaParser instance
# - test_models_file: Path to test models
# - tmp_models: Create temp model files
# - client: FastAPI test client
# - db: In-memory store with test data
```

**tests/unit/test_parser.py** ✅

```python
# 12 tests covering:
# - File loading (valid, invalid, missing)
# - Model extraction
# - Field type detection
# - Foreign key detection
# - Relationship creation
# Target: 29 tests (17 more needed)
```

#### Documentation Files

**docs/index.md**

```markdown
# Mock API Documentation

## Quick Start

## User Guide

## API Reference

## Examples

## Contributing
```

**docs/development/adr/001-use-pydantic.md**

```markdown
# ADR 001: Use Pydantic for Schema Validation

## Status: Accepted

## Context

Need type-safe schema validation...

## Decision

Use Pydantic v2 for all schema validation

## Consequences

- Runtime type checking
- Excellent error messages

* Pydantic dependency
```

#### Example Projects

**examples/blog/models.py**

```python
"""Blog application models."""
from pydantic import BaseModel
from datetime import datetime

class User(BaseModel):
    id: int
    username: str
    email: str
    bio: str | None = None

class Post(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    published_at: datetime | None = None

class Comment(BaseModel):
    id: int
    text: str
    post_id: int
    user_id: int
```

**examples/blog/README.md**

````markdown
# Blog Example

## Run

```bash
mock-api run models.py --seed 20
```
````

## Test

```bash
curl http://localhost:3000/users
curl http://localhost:3000/posts
curl http://localhost:3000/users/1/posts
```

### 2.3 Configuration Files

#### .vscode/settings.json

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit"
    }
  },
  "python.testing.pytestEnabled": true
}
```

#### .vscode/launch.json

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Run Mock API",
      "type": "debugpy",
      "request": "launch",
      "module": "mock_api.cli.main",
      "args": ["run", "examples/blog/models.py"],
      "console": "integratedTerminal"
    },
    {
      "name": "Pytest: Current File",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": ["${file}", "-v"],
      "console": "integratedTerminal"
    }
  ]
}
```

### 2.4 File Size Estimates

| Component    | Files | Lines  | Status            |
| ------------ | ----- | ------ | ----------------- |
| **Core**     | 7     | ~2,000 | 25% complete      |
| **CLI**      | 6     | ~500   | 0% complete       |
| **Tests**    | 15+   | ~2,500 | 20% complete      |
| **Docs**     | 20+   | ~3,000 | 30% complete      |
| **Examples** | 5     | ~500   | 20% complete      |
| **Config**   | 10    | ~500   | 80% complete      |
| **Total**    | ~63   | ~9,000 | **~25% complete** |

### 2.5 Development Workflow

```bash
# Clone repo
git clone https://github.com/sudzxd/mock-api
cd mock-api

# Setup environment
uv venv
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/ -v --cov

# Type check
pyright mock_api/

# Format & lint
ruff format .
ruff check .

# Run locally
mock-api run examples/blog/models.py

# Build docs
mkdocs serve
```

---

## 3. Architecture Principles

### 3.1 Design Philosophy

**1. Convention Over Configuration**

- Auto-detect foreign keys (`author_id` → User)
- Smart data generation (email field → valid emails)
- Sensible defaults everywhere

**2. Type Safety First**

- Pyright strict mode: 0 errors
- Runtime validation with Pydantic
- Clear type contracts between components

**3. Developer Experience**

- Beautiful CLI output (Rich library)
- Helpful error messages with suggestions
- Fast feedback loops (<1s startup)

**4. SOLID Principles**

- Single Responsibility: Each class has one job
- Open/Closed: Extend without modifying
- Liskov Substitution: Drop-in replacements
- Interface Segregation: Small, focused interfaces
- Dependency Inversion: Depend on abstractions

**5. Production-Ready Code**

- 100% test coverage target
- Comprehensive logging
- Performance benchmarks
- Security-first mindset

### 2.2 Architectural Patterns

**Layered Architecture:**

```
┌─────────────────────────────────────────────┐
│            CLI Layer (User Interface)       │ ← Click commands, Rich output
├─────────────────────────────────────────────┤
│         Application Layer (Orchestration)   │ ← Server, configuration
├─────────────────────────────────────────────┤
│           Domain Layer (Business Logic)     │ ← Generator, Store, Router
├─────────────────────────────────────────────┤
│        Infrastructure Layer (Adapters)      │ ← Parser, FastAPI, Faker
└─────────────────────────────────────────────┘
```

**Key Patterns:**

- **Factory Pattern:** SchemaParser, DataGenerator
- **Repository Pattern:** Store (CRUD abstraction)
- **Strategy Pattern:** Multiple FK resolution strategies
- **Builder Pattern:** Route generation
- **Singleton Pattern:** Logger configuration

---

## 3. Component Architecture

### 3.1 Component Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                        mock-api                              │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │    CLI     │  │   Server   │  │  Scenarios │           │
│  │  (Click)   │→ │ (FastAPI)  │← │  (Testing) │           │
│  └────────────┘  └────────────┘  └────────────┘           │
│         │              │                                     │
│         ▼              ▼                                     │
│  ┌──────────────────────────────────────────────┐          │
│  │           Core Engine                         │          │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │          │
│  │  │  Parser  │→ │Generator │→ │  Store   │  │          │
│  │  └──────────┘  └──────────┘  └──────────┘  │          │
│  │                      │             │         │          │
│  │                      ▼             ▼         │          │
│  │                 ┌──────────┐  ┌──────────┐  │          │
│  │                 │  Router  │  │  Logger  │  │          │
│  │                 └──────────┘  └──────────┘  │          │
│  └──────────────────────────────────────────────┘          │
│                                                              │
│  ┌──────────────────────────────────────────────┐          │
│  │        Integrations (Future)                  │          │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │          │
│  │  │TypeScript│  │ OpenAPI  │  │ GraphQL  │  │          │
│  │  │  Parser  │  │  Parser  │  │ Parser   │  │          │
│  │  └──────────┘  └──────────┘  └──────────┘  │          │
│  └──────────────────────────────────────────────┘          │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Component Responsibilities

#### **CLI Layer**

**`mock_api/cli/main.py`**

```python
Responsibilities:
- Parse command-line arguments
- Display help text and examples
- Handle user errors gracefully
- Pretty-print output with Rich
- Invoke core components

Commands:
- mock-api run <schema> [--port 3000] [--seed 10]
- mock-api init [--interactive]
- mock-api validate <schema>
- mock-api version
```

#### **Core Layer**

**`mock_api/core/parser.py`** ✅ **COMPLETE**

```python
Responsibilities:
- Parse Pydantic models from Python files
- Extract field types and metadata
- Detect foreign key relationships
- Create inverse relationships
- Validate schema consistency

Input:  Path to .py file
Output: dict[str, ModelSchema]
```

**`mock_api/core/generator.py`** 🚧 **NEXT**

```python
Responsibilities:
- Generate realistic fake data
- Respect field name semantics (email → valid emails)
- Handle relationships (valid foreign keys)
- Support custom data patterns
- Locale-aware generation

Input:  ModelSchema + count
Output: list[dict] of generated entities
```

**`mock_api/core/store.py`** 🚧 **PHASE 1**

```python
Responsibilities:
- In-memory CRUD operations
- Query filtering (?author_id=5)
- Relationship navigation
- Auto-increment IDs
- Thread-safe operations

Input:  CRUD operations
Output: Entity dictionaries
```

**`mock_api/core/router.py`** 🚧 **PHASE 1**

```python
Responsibilities:
- Generate FastAPI routes from schemas
- Standard REST endpoints (GET, POST, PUT, DELETE)
- Nested routes (/users/1/posts)
- Request validation with Pydantic
- Response serialization

Input:  dict[str, ModelSchema] + Store
Output: FastAPI router
```

**`mock_api/core/server.py`** 🚧 **PHASE 1**

```python
Responsibilities:
- Orchestrate all components
- Configure FastAPI app
- Handle startup/shutdown
- CORS middleware
- Error handling

Input:  Configuration
Output: Running FastAPI server
```

**`mock_api/core/logger.py`** ✅ **COMPLETE**

```python
Responsibilities:
- Centralized logging configuration
- Rich console output
- Configurable log levels
- Beautiful tracebacks

Input:  Log messages
Output: Formatted console output
```

#### **Integrations Layer** (Future)

**`mock_api/integrations/typescript.py`** 📅 **PHASE 2**

```python
Responsibilities:
- Parse TypeScript type definitions
- Convert to ModelSchema
- Handle TS-specific types

Input:  .ts file
Output: dict[str, ModelSchema]
```

**`mock_api/integrations/openapi.py`** 📅 **PHASE 3**

```python
Responsibilities:
- Parse OpenAPI 3.x specs
- Extract schemas and relationships
- Generate routes from paths

Input:  openapi.yaml
Output: dict[str, ModelSchema]
```

---

## 4. Data Flow

### 4.1 Request Flow

```
USER
  │
  │ $ mock-api run models.py --seed 20
  ▼
┌────────────────────┐
│  CLI (main.py)     │
│  - Parse args      │
│  - Validate inputs │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│  Parser            │ ① Parse schema file
│  - Import module   │
│  - Extract models  │
│  - Detect FKs      │
└────────┬───────────┘
         │
         │ dict[str, ModelSchema]
         ▼
┌────────────────────┐
│  Generator         │ ② Generate seed data
│  - Create entities │
│  - Realistic data  │
│  - Valid FKs       │
└────────┬───────────┘
         │
         │ dict[str, list[dict]]
         ▼
┌────────────────────┐
│  Store             │ ③ Initialize storage
│  - Load seed data  │
│  - Set up indexes  │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│  Router            │ ④ Generate routes
│  - Create endpoints│
│  - Add validation  │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│  Server            │ ⑤ Start FastAPI
│  - Configure app   │
│  - Add middleware  │
│  - Run uvicorn     │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│  HTTP Server       │
│  localhost:3000    │
│  Ready for requests│
└────────────────────┘
         │
         ▼
    FRONTEND APP
```

### 4.2 Runtime Request Flow

```
FRONTEND
  │
  │ GET /users/5
  ▼
┌────────────────────────┐
│  FastAPI               │
│  - Route matching      │
│  - Auth middleware     │
│  - CORS headers        │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│  Route Handler         │
│  - Extract path params │
│  - Parse query string  │
│  - Validate request    │
└────────┬───────────────┘
         │
         │ get_by_id('User', 5)
         ▼
┌────────────────────────┐
│  Store                 │
│  - Lookup entity       │
│  - Apply filters       │
│  - Return data         │
└────────┬───────────────┘
         │
         │ {"id": 5, "name": "Alice"}
         ▼
┌────────────────────────┐
│  Response Builder      │
│  - Serialize with      │
│    Pydantic            │
│  - Add headers         │
└────────┬───────────────┘
         │
         │ JSON response
         ▼
    FRONTEND APP
```

---

## 5. Implementation Phases

### Phase 0: Foundation ✅ **COMPLETE**

**Duration:** 2 weeks
**Status:** ✅ Done

**Deliverables:**

- ✅ Project structure
- ✅ Development tooling (pyproject.toml, pre-commit)
- ✅ Style guide
- ✅ Parser module (83% coverage)
- ✅ Centralized logging
- ✅ Architecture documentation

**Metrics:**

- Lines of Code: ~450
- Test Coverage: 84%
- Pyright Errors: 0

---

### Phase 1: MVP - Basic Mock API ⏳ **IN PROGRESS**

**Duration:** 2 weeks
**Goal:** Ship minimal viable product

#### Week 1: Core Components

**Day 1-2: Data Generator** 🎯 **NEXT**

```python
Features:
- Generate realistic fake data from schemas
- Field name → Faker mapping (email → valid emails)
- Relationship-aware (valid foreign keys)
- Configurable seed count

Tests:
- Field type generation (str, int, datetime)
- Semantic field detection (email, phone, url)
- Foreign key generation (valid IDs only)
- Reproducible seeds

Acceptance Criteria:
- ✅ Generates 100 entities in <100ms
- ✅ 95% test coverage
- ✅ Pyright strict: 0 errors
- ✅ Realistic data for common field names
```

**Day 3-4: In-Memory Store**

```python
Features:
- CRUD operations (create, read, update, delete)
- Query filtering (?status=active)
- Relationship navigation
- Auto-increment IDs
- Thread-safe

Tests:
- All CRUD operations
- Concurrent access
- Filter combinations
- Edge cases (empty, invalid IDs)

Acceptance Criteria:
- ✅ 1000 ops/sec throughput
- ✅ Thread-safe (pytest-xdist)
- ✅ 100% test coverage
```

**Day 5-7: Route Generator**

```python
Features:
- Standard REST endpoints:
  - GET /users
  - GET /users/:id
  - POST /users
  - PUT /users/:id
  - DELETE /users/:id
- Nested routes (/users/:id/posts)
- Request validation (Pydantic)
- Response formatting

Tests:
- Route generation for all models
- Nested route creation
- Validation (invalid data → 422)
- Error handling (404, 500)

Acceptance Criteria:
- ✅ Generates routes for 100 models in <1s
- ✅ All HTTP methods supported
- ✅ OpenAPI docs auto-generated
```

#### Week 2: Integration & CLI

**Day 8-10: Server Orchestration**

```python
Features:
- FastAPI app setup
- Component wiring
- Startup logging
- Error handling
- CORS middleware

Tests:
- Server startup/shutdown
- Health endpoint
- Error responses
- Middleware integration

Acceptance Criteria:
- ✅ Starts in <2s
- ✅ Graceful shutdown
- ✅ Helpful startup logs
```

**Day 11-12: CLI Interface**

```python
Features:
- mock-api run <schema> [options]
- Beautiful Rich output
- Progress indicators
- Error suggestions

Tests:
- All commands work
- Help text accurate
- Error messages clear

Acceptance Criteria:
- ✅ Intuitive UX
- ✅ Helpful error messages
- ✅ Examples in --help
```

**Day 13-14: End-to-End Testing & Polish**

```python
Activities:
- Integration tests
- Performance benchmarks
- Documentation
- Bug fixes

Deliverables:
- README with examples
- Tutorial video
- Benchmark results
- Release notes

Acceptance Criteria:
- ✅ All tests pass
- ✅ <1s cold start
- ✅ Example projects work
```

**Phase 1 Success Metrics:**

- ✅ Can run: `mock-api run models.py`
- ✅ Returns realistic data via REST API
- ✅ Full CRUD operations work
- ✅ 90%+ test coverage
- ✅ Documentation complete

---

### Phase 2: Advanced Features

**Duration:** 3 weeks

**Features:**

1. **TypeScript Support** (Week 1)

   - Parse .ts type definitions
   - Convert to ModelSchema
   - Integration tests

2. **Scenarios System** (Week 2)

   - Error scenarios (500 errors, timeouts)
   - Slow response mode
   - Custom data scenarios
   - CLI: `--scenario errors`

3. **Watch Mode** (Week 2)

   - Auto-reload on schema changes
   - Hot module replacement
   - WebSocket notifications

4. **Proxy Mode** (Week 3)
   - Mix mock + real endpoints
   - Fallback to real API
   - Record/replay mode

**Success Metrics:**

- ✅ TypeScript examples work
- ✅ All scenario types functional
- ✅ Watch mode <1s reload

---

### Phase 3: Production Features

**Duration:** 4 weeks

**Features:**

1. **OpenAPI Export** (Week 1)

   - Generate openapi.yaml from schemas
   - Swagger UI integration
   - Schema validation

2. **Persistence Layer** (Week 2)

   - SQLite backend option
   - PostgreSQL backend option
   - Data export/import

3. **GraphQL Support** (Week 3)

   - GraphQL schema generation
   - Query/mutation resolvers
   - Subscription support

4. **Authentication** (Week 4)
   - JWT token generation
   - OAuth2 simulation
   - RBAC scenarios

**Success Metrics:**

- ✅ OpenAPI spec validates
- ✅ Data persists across restarts
- ✅ GraphQL queries work

---

### Phase 4: Enterprise Features

**Duration:** 6 weeks

**Features:**

1. **Multi-tenant Support**
2. **Rate Limiting**
3. **API Versioning**
4. **Metrics & Monitoring**
5. **Docker Support**
6. **Cloud Deployment (Vercel, Railway)**

---

## 6. Technology Stack

### Core Dependencies

| Category       | Technology | Version   | Purpose                   |
| -------------- | ---------- | --------- | ------------------------- |
| **Framework**  | FastAPI    | >=0.115.0 | REST API server           |
| **Server**     | Uvicorn    | >=0.30.0  | ASGI server               |
| **Validation** | Pydantic   | >=2.0.0   | Type validation           |
| **Data**       | Faker      | >=30.0.0  | Fake data generation      |
| **CLI**        | Click      | >=8.1.0   | Command-line interface    |
| **Output**     | Rich       | >=13.0.0  | Beautiful terminal output |

### Development Dependencies

| Category       | Technology     | Purpose                 |
| -------------- | -------------- | ----------------------- |
| **Testing**    | Pytest         | Unit testing            |
| **Coverage**   | pytest-cov     | Code coverage           |
| **Async**      | pytest-asyncio | Async test support      |
| **HTTP**       | httpx          | HTTP client for tests   |
| **Linting**    | Ruff           | Fast linter & formatter |
| **Type Check** | Pyright        | Static type checking    |
| **Security**   | Bandit         | Security linting        |
| **Audit**      | pip-audit      | Dependency scanning     |
| **Hooks**      | pre-commit     | Git hooks               |

### Future Dependencies

| Phase   | Technology | Purpose            |
| ------- | ---------- | ------------------ |
| Phase 2 | ts-python  | TypeScript parsing |
| Phase 3 | Strawberry | GraphQL support    |
| Phase 3 | SQLAlchemy | Database ORM       |
| Phase 4 | Prometheus | Metrics            |

---

## 7. Quality Standards

### Code Quality Gates

**Every commit must pass:**

```bash
# 1. Format code
ruff format .

# 2. Lint code
ruff check .

# 3. Type check
pyright .

# 4. Run tests
pytest --cov --cov-fail-under=90

# 5. Security scan
bandit -r mock_api/

# 6. Dependency audit
pip-audit
```

### Metrics Targets

| Metric          | Target      | Current | Status      |
| --------------- | ----------- | ------- | ----------- |
| Test Coverage   | >90%        | 84%     | ⚠️ Increase |
| Pyright Errors  | 0           | 0       | ✅ Pass     |
| Ruff Violations | 0           | 0       | ✅ Pass     |
| Security Issues | 0           | 0       | ✅ Pass     |
| Performance     | <1s startup | ❓      | 🔄 Measure  |
| Documentation   | 100% public | 100%    | ✅ Pass     |

### Performance Benchmarks

```python
# Target benchmarks (pytest-benchmark)
def test_parse_schema_performance(benchmark):
    result = benchmark(parser.parse_file, "models.py")
    assert result  # <10ms for 10 models

def test_generate_data_performance(benchmark):
    result = benchmark(generator.generate, schema, 100)
    assert len(result) == 100  # <50ms for 100 entities

def test_crud_operations_performance(benchmark):
    result = benchmark(store.get_all, "User")
    assert result  # <1ms for 1000 entities

def test_server_startup_performance(benchmark):
    result = benchmark(server.start)
    # <1s cold start
```

---

## 8. Deployment Strategy

### Local Development

```bash
# Install
pip install mock-api

# Or install from source
git clone https://github.com/sudzxd/mock-api
cd mock-api
pip install -e ".[dev]"

# Run
mock-api run models.py
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["mock-api", "run", "models.py", "--host", "0.0.0.0"]
```

### Cloud Deployment

**Railway.app:**

```yaml
# railway.toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "mock-api run models.py --host 0.0.0.0 --port $PORT"
```

**Vercel:**

```json
{
  "builds": [{ "src": "api/index.py", "use": "@vercel/python" }]
}
```

---

## 9. Future Roadmap

### 2026 Q1 (Current)

- ✅ Phase 0: Foundation
- 🚧 Phase 1: MVP

### 2026 Q2

- Phase 2: Advanced Features
- Phase 3: Production Features

### 2026 Q3-Q4

- Phase 4: Enterprise Features
- Performance optimization
- Scale testing

### Beyond

- Plugin system
- Custom data generators
- Cloud-native version
- SaaS offering (mock-api.io)

---

## Appendices

### A. API Design Patterns

**REST Endpoints:**

```
GET    /users           # List all
GET    /users/:id       # Get one
POST   /users           # Create
PUT    /users/:id       # Update
PATCH  /users/:id       # Partial update
DELETE /users/:id       # Delete

GET    /users/:id/posts # Nested resources
```

**Query Parameters:**

```
GET /users?age=25              # Filter
GET /users?sort=created_at     # Sort
GET /users?page=2&limit=10     # Pagination
GET /users?include=posts       # Include relations
```

### B. Error Response Format

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "User with id 999 not found",
    "suggestion": "Valid user IDs: 1-100",
    "timestamp": "2026-01-05T10:30:00Z"
  }
}
```

### C. Configuration File Format

```yaml
# mock-api.yml
seed: 100
locale: en_US
relationships:
  user:
    posts: 3-10 # Each user has 3-10 posts
port: 3000
log_level: INFO
```

---

**Document Version:** 1.0
**Last Updated:** 2026-01-05
**Next Review:** After Phase 1 completion
