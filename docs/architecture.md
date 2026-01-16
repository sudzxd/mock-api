# Architecture

System design and components of mockapi-server.

## Overview

mockapi-server generates REST APIs from Pydantic models by parsing type definitions, generating realistic data, and creating FastAPI routes automatically.

**Design Philosophy:**

- Type safety first
- Zero configuration
- Separation of concerns (DDD layers)
- Extensibility via protocols

## Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       CLI Layer                             │
│                   (Click Commands)                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                     Core Layer                              │
│            (Facades & Orchestration)                        │
│   SchemaParser │ DataGenerator │ DataStore │ Router        │
└─────────────┬───────────────────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────────────────┐
│                   Domain Layer                              │
│                (Protocols & Interfaces)                     │
│  ISchemaParser │ IDataGenerator │ IStorageStrategy          │
└─────────────┬───────────────────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────────────────┐
│               Implementations Layer                         │
│           (Concrete Implementations)                        │
│  PydanticParser │ FakerGenerator │ InMemoryRepository       │
└─────────────────────────────────────────────────────────────┘
```

### Core Layer (Facades)

**SchemaParser** - Facade for schema parsing
- Delegates to `PydanticSchemaParser` implementation
- Future: TypeScript, OpenAPI parsers (Issue #9)

**DataGenerator** - Facade for data generation
- Delegates to `FakerDataGenerator` implementation
- Future: Custom providers (Issue #21)

**DataStore** - Facade for storage operations
- Delegates to `InMemoryRepository` implementation
- Future: JSON, SQLite, PostgreSQL (Issues #48-51)

**Router** - Route generation with presentation layer
- Uses `RouteHandlerFactory` for handler creation
- Delegates to services for business logic

### Domain Layer (Protocols)

Defines interfaces for all extension points:

- `ISchemaParser` - Schema parsing interface
- `IDataGenerator` - Data generation interface
- `IStorageStrategy` - Storage backend interface
- `IExportStrategy` - API export interface (Issue #47)
- `IMiddleware` - Middleware interface (Issues #13, #12, #6)

### Implementations Layer

Concrete implementations of domain protocols:

- `PydanticSchemaParser` - Parses Pydantic models
- `FakerDataGenerator` - Generates data with Faker
- `InMemoryRepository` - In-memory storage with thread safety

## Data Flow

### Request Lifecycle

```
Client Request
    │
    ▼
FastAPI Router
    │
    ▼
Route Handler (Presentation)
    │
    ▼
Services (Application Logic)
    │
    ▼
DataStore (Core Facade)
    │
    ▼
Repository (Implementation)
    │
    ▼
JSON Response
```

### Startup Flow

```
models.py
    │
    ▼
SchemaParser (Facade)
    │
    ▼
PydanticSchemaParser (Implementation)
    │
    ▼
ModelSchema[]
    │
    ▼
DataGenerator (Facade)
    │
    ▼
FakerDataGenerator (Implementation)
    │
    ▼
DataStore → InMemoryRepository
```

## Design Principles

### SOLID Principles

**Single Responsibility:** Each layer has one concern (Core = facades, Domain = protocols, Implementations = concrete logic)

**Open/Closed:** Extend via new implementations without modifying core (add parsers, storage backends, generators)

**Liskov Substitution:** All implementations can be swapped transparently via protocols

**Interface Segregation:** Small, focused protocols - depend only on what you need

**Dependency Inversion:** Core depends on domain protocols, not concrete implementations

### Architecture Benefits

**Extensibility:** Add new implementations by implementing protocols (no core changes)

**Testability:** Mock implementations via protocols for isolated testing

**Future-Ready:** Scaffolding in place for 15+ planned features (storage backends, exporters, middleware)

## Extension Points

All extension points use protocol-based design:

### Custom Parsers
```python
# Implement ISchemaParser protocol
class TypeScriptParser:
    def parse_file(self, file_path: str) -> dict[str, ModelSchema]:
        # TypeScript parsing logic
        pass
```

### Custom Storage
```python
# Implement IStorageStrategy protocol
class PostgreSQLRepository:
    def create(self, model: str, data: dict) -> dict:
        # PostgreSQL logic
        pass
```

### Custom Generators
```python
# Implement IFieldGenerationStrategy protocol
class DomainGenerator:
    def can_generate(self, field: FieldSchema) -> bool:
        return field.name in CUSTOM_PATTERNS

    def generate(self, field: FieldSchema, context) -> Any:
        # Custom generation logic
        pass
```

## Factories

Use factories to create implementations:

```python
from mock_api.implementations import (
    SchemaParserFactory,
    DataGeneratorFactory,
    StorageStrategyFactory
)

# Create implementations
parser = SchemaParserFactory.create("pydantic")
generator = DataGeneratorFactory.create(schemas)
storage = StorageStrategyFactory.create("memory://")
```

## References

- [CLI Reference](cli-reference.md) - Command-line interface
- [API Reference](api-reference.md) - Python API details
- [Guidelines](development/guidelines.md) - SOLID principles in practice
