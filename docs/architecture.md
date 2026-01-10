# Architecture

System design and components of mockapi-server.

## Overview

mockapi-server generates REST APIs from Pydantic models by parsing type definitions, generating realistic data, and creating FastAPI routes automatically.

**Design Philosophy:**

- Type safety first
- Zero configuration
- Separation of concerns
- Extensibility via interfaces

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                          CLI Layer                          │
│                     (Click Commands)                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                        Server                               │
│                    (Orchestrator)                           │
└──┬───────────┬──────────┬─────────────┬────────────────────-┘
   │           │          │             │
   │           │          │             │
┌──▼──-┐  ┌────▼──────┐ ┌───▼────┐ ┌────▼──────┐
│Schema│  │ Data      │ │ Data   │ │Route      │
│Parser│  │ Generator │ │ Store  │ │Generator  │
└──┬───┘  └────┬───-──┘ └───┬────┘ └────┬──────┘
   │           │          │           │
   │           │          │           │
   └───────────┴──────────┴───────────┘
               │
        ┌──────▼──────┐
        │  FastAPI    │
        │Application  │
        └─────────────┘
```

### SchemaParser

**Responsibility:** Parse Pydantic models → ModelSchema

**Input:** Python file path
**Output:** `dict[str, ModelSchema]`

**Functionality:**

- Imports Python module
- Extracts Pydantic BaseModel classes
- Parses field types and annotations
- Detects foreign key relationships (e.g., `author_id` → `User`)
- Returns typed dataclass representations

### DataGenerator

**Responsibility:** ModelSchema → Fake data

**Input:** ModelSchema, count
**Output:** `list[dict]`

**Functionality:**

- Generates realistic fake data based on field names (email, name, phone)
- Respects foreign key constraints
- Handles optional fields
- Uses Faker library for semantic data

### DataStore

**Responsibility:** In-memory CRUD operations

**Input:** Model name, data
**Output:** Data or None

**Functionality:**

- Stores data in `dict[model_name, list[dict]]`
- Implements create, read, update, delete operations
- Filters by query parameters
- Thread-safe for single process

### RouteGenerator

**Responsibility:** ModelSchema → FastAPI routes

**Input:** ModelSchema, DataStore
**Output:** FastAPI router

**Functionality:**

- Generates standard REST endpoints (GET, POST, PUT, DELETE)
- Creates Pydantic response models
- Adds OpenAPI documentation
- Implements query parameter filtering

### Server

**Responsibility:** Orchestrates all components

**Functionality:**

- Instantiates parser, generator, store, route generator
- Configures FastAPI application
- Adds CORS middleware
- Serves OpenAPI docs at `/docs`
- Returns configured app for uvicorn

## Data Flow

### Request Lifecycle

```
Client Request
    │
    ▼
FastAPI Router
    │
    ▼
Route Handler
    │
    ▼
DataStore (CRUD)
    │
    ▼
Pydantic Validation
    │
    ▼
JSON Response
```

### Data Generation Flow

```
models.py
    │
    ▼
SchemaParser
    │
    ▼
ModelSchema[]
    │
    ▼
DataGenerator
    │
    ▼
Fake Data[]
    │
    ▼
DataStore
```

## Design Principles

### SOLID Principles

**Single Responsibility:** Each component handles one concern (parsing, generating, storing, routing)

**Open/Closed:** New parsers, generators, or storage backends can be added without modifying core

**Liskov Substitution:** All parsers return ModelSchema, all stores implement same CRUD interface

**Interface Segregation:** Small, focused interfaces - components depend only on what they use

**Dependency Inversion:** High-level Server depends on abstractions (interfaces), not implementations

### Other Principles

**Separation of Concerns:** Clear boundaries between parsing, generation, storage, and routing

**Dependency Injection:** Components receive dependencies via constructor (testability)

**Type Safety:** Strong typing throughout with Python 3.11+ type hints and Pydantic

## Extension Points

### Custom Generators

Implement custom data generation logic:

```python
class CustomGenerator:
    def generate(self, model_name: str, count: int) -> list[dict]:
        # Custom logic
        pass
```

### Custom Storage Backends

Replace in-memory store with database:

```python
class DatabaseStore:
    def create(self, model_name: str, data: dict) -> dict:
        # Database logic
        pass
```

### Custom Parsers

Add TypeScript or OpenAPI support:

```python
class TypeScriptParser:
    def parse_file(self, file_path: str) -> dict[str, ModelSchema]:
        # TypeScript parsing logic
        pass
```

## References

- [CLI Reference](cli-reference.md) - Command-line interface
- [API Reference](api-reference.md) - Python API details
- [Guidelines](development/guidelines.md) - SOLID principles in practice
