# mock-api

**Stop writing JSON files. Start with types.**

Generate full-featured REST APIs from your Pydantic models in seconds.

## Quick Start

```bash
# Install
pip install mock-api

# Initialize project
mock-api init

# Run server
mock-api serve --models models.py --generate-data
```

## Features

- **Zero config** - Point at your schema file and go
- **Type-safe** - Built on Pydantic for automatic validation
- **Smart data** - Realistic fake data based on field names
- **Auto relationships** - Detects foreign keys, creates nested routes
- **Stateful** - CRUD operations persist during session
- **OpenAPI** - Auto-generated interactive docs

## Example

```python
# models.py
from pydantic import BaseModel
from datetime import datetime

class User(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

class Post(BaseModel):
    id: int
    title: str
    content: str
    author_id: int  # Automatically creates user relationship
```

```bash
mock-api serve --models models.py --generate-data --data-count 50
```

Access your API at `http://localhost:3000/api/v1` with auto-generated endpoints:
- `GET /users`, `GET /users/:id`
- `POST /users`, `PUT /users/:id`, `DELETE /users/:id`
- Interactive docs at `/docs`

## Why mock-api?

**json-server:** Manual JSON files that get stale
**Mockoon:** GUI clicking for every endpoint
**Prism:** Requires full OpenAPI spec

**mock-api:** Your types ARE your API contract.

## Documentation

- [Getting Started](docs/getting-started.md) - Installation and first project
- [CLI Reference](docs/cli-reference.md) - All commands and options
- [API Reference](docs/api-reference.md) - Python API and REST endpoints
- [Examples](docs/examples.md) - Real-world use cases
- [FAQ](docs/faq.md) - Common questions
- [Architecture](docs/architecture.md) - System design
- [Troubleshooting](docs/troubleshooting.md) - Solutions to common issues

### Contributing

- [Development Setup](docs/development/setup.md)
- [Guidelines](docs/development/guidelines.md)
- [Testing](docs/development/testing.md)

## Status

Under active development.

## License

MIT
