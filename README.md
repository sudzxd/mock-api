# mockapi-server

[![Test PyPI](https://img.shields.io/badge/Test%20PyPI-v0.1.0a2-blue)](https://test.pypi.org/project/mockapi-server/)
[![Python versions](https://img.shields.io/badge/python-3.11%20|%203.12%20|%203.13-blue)](https://test.pypi.org/project/mockapi-server/)
[![CI](https://github.com/sudzxd/mockapi-server/actions/workflows/ci-develop.yml/badge.svg)](https://github.com/sudzxd/mockapi-server/actions)
[![Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen)](https://github.com/sudzxd/mockapi-server)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: pyright](https://img.shields.io/badge/type%20checked-pyright-blue.svg)](https://github.com/microsoft/pyright)
[![Documentation](https://img.shields.io/badge/docs-github.io-blue.svg)](https://sudzxd.github.io/mockapi-server)

**Stop writing JSON files. Start with types.**

Generate full-featured REST APIs from your Pydantic models in seconds.

## Quick Start

```bash
# Install
pip install mockapi-server

# Initialize project
mockapi-server init

# Run server
mockapi-server serve --models models.py --generate-data
```

## Features

- **Zero config** - Point at your schema file and go
- **Type-safe** - Built on Pydantic for automatic validation
- **Smart data** - Realistic fake data based on field names
- **Auto relationships** - Detects foreign keys, creates nested routes
- **Bulk operations** - Create, update, delete multiple entities atomically
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
mockapi-server serve --models models.py --generate-data --data-count 50
```

Access your API at `http://localhost:3000/api/v1` with auto-generated endpoints:
- `GET /users`, `GET /users/:id`
- `POST /users`, `PUT /users/:id`, `DELETE /users/:id`
- `POST /users/bulk`, `PUT /users/bulk`, `DELETE /users/bulk?ids=1,2,3`
- Interactive docs at `/docs`

## Examples

Check out the [examples/](examples/) directory for complete working projects:

- **[Basic](examples/basic/)** - Simple User and Product API with HTML client
- **[Blog](examples/blog/)** - Multi-model API with relationships and Docker setup
- **[E-commerce](examples/ecommerce/)** - Complex relationships with Postman collection

## Why mockapi-server?

**json-server:** Manual JSON files that get stale
**Mockoon:** GUI clicking for every endpoint
**Prism:** Requires full OpenAPI spec

**mockapi-server:** Your types ARE your API contract.

## Documentation

**[📚 Full Documentation](https://sudzxd.github.io/mockapi-server)**

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
