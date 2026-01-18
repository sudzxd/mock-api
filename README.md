# mockapi-server

[![Test PyPI](https://img.shields.io/badge/Test%20PyPI-v0.1.0a2-blue)](https://test.pypi.org/project/mockapi-server/)
[![Python versions](https://img.shields.io/badge/python-3.11%20|%203.12%20|%203.13-blue)](https://test.pypi.org/project/mockapi-server/)
[![CI](https://github.com/sudzxd/mockapi-server/actions/workflows/ci-develop.yml/badge.svg)](https://github.com/sudzxd/mockapi-server/actions)
[![Coverage](https://img.shields.io/badge/coverage-71%25-yellow)](https://github.com/sudzxd/mockapi-server)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: pyright](https://img.shields.io/badge/type%20checked-pyright-blue.svg)](https://github.com/microsoft/pyright)
[![Documentation](https://img.shields.io/badge/docs-github.io-blue.svg)](https://sudzxd.github.io/mockapi-server)

**Stop writing JSON files. Start with types.**

Generate full-featured REST APIs from schema definitions in seconds. Built with Domain-Driven Design, SOLID principles, and production-ready architecture.

## Quick Start

```bash
# Install
pip install mockapi-server

# Create your models
cat > models.py << EOF
from pydantic import BaseModel
from datetime import datetime

class User(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime
EOF

# Start server with generated data
mockapi-server serve models.py --generate-data --data-count 50
```

Visit `http://localhost:3000/docs` for interactive API documentation.

## Features

- **Zero config** - Point at your schema file and go
- **Type-safe** - Built on Pydantic v2 for automatic validation
- **Smart data** - Realistic fake data using Faker (detects emails, names, etc.)
- **Auto relationships** - Foreign keys auto-detected (`author_id` → User)
- **Bulk operations** - Atomic create/update/delete for multiple entities
- **Rich filtering** - 10+ operators (eq, gt, gte, lt, lte, contains, in, nin, etc.)
- **Sorting & pagination** - Multi-field sorting, page/offset-based pagination
- **Stateful** - In-memory or JSON file persistence
- **OpenAPI** - Auto-generated Swagger UI + ReDoc

## Architecture

Built following **Domain-Driven Design** with clean architecture:

- **Domain Layer:** Pure business logic, zero dependencies
- **Application Layer:** Use cases orchestrate domain + infrastructure
- **Infrastructure Layer:** Concrete implementations (repositories, parsers, generators)
- **Presentation Layer:** FastAPI HTTP layer with dependency injection

**Tech Stack:** Python 3.11+ | Pydantic v2 | FastAPI | Faker | Click CLI

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
    author_id: int  # Auto-detected as FK → User.id
    published_at: datetime | None = None
```

```bash
# Start server
mockapi-server serve models.py --generate-data --data-count 50

# Access API
curl http://localhost:3000/api/v1/users
curl http://localhost:3000/api/v1/users/1
curl http://localhost:3000/api/v1/posts?author_id=5&sort=-created_at&page=1&page_size=10
```

**Auto-generated endpoints:**

```
GET    /api/v1/users              # List with filtering, sorting, pagination
GET    /api/v1/users/{id}         # Get single
POST   /api/v1/users              # Create
PUT    /api/v1/users/{id}         # Update (partial supported)
DELETE /api/v1/users/{id}         # Delete
POST   /api/v1/users/bulk         # Bulk create
PUT    /api/v1/users/bulk         # Bulk update
DELETE /api/v1/users/bulk?ids=1,2 # Bulk delete
```

**Interactive docs:** `http://localhost:3000/docs`

## Query Examples

```bash
# Filtering
GET /api/v1/users?age__gte=18&status=active
GET /api/v1/posts?title__contains=python&published=true
GET /api/v1/users?id__in=1,2,3,4,5

# Sorting
GET /api/v1/posts?sort=-created_at,title

# Pagination
GET /api/v1/users?page=1&page_size=20

# Combined
GET /api/v1/posts?author_id=5&sort=-views&page=1&page_size=10
```

**Available operators:** `eq` (default), `gt`, `gte`, `lt`, `lte`, `contains`, `startswith`, `endswith`, `in`, `nin`

## Storage Options

```bash
# In-memory (default) - data lost on restart
mockapi-server serve models.py --storage-url memory://

# JSON file - persists across restarts
mockapi-server serve models.py --storage-url json://./data.json
```

## Examples

Complete working projects in [`examples/`](examples/):

| Example                               | Description               | Features                            |
| ------------------------------------- | ------------------------- | ----------------------------------- |
| **[Basic](examples/basic/)**          | User + Product API        | Simple models, HTML client          |
| **[Blog](examples/blog/)**            | Multi-model relationships | User/Post/Comment, Docker setup     |
| **[E-commerce](examples/ecommerce/)** | Complex system            | Orders/Products, Postman collection |

Each includes schema definitions, setup instructions, and testing tools.

## Why mockapi-server?

| Tool               | Approach              | Pain Points                         |
| ------------------ | --------------------- | ----------------------------------- |
| **json-server**    | Manual JSON files     | Gets stale, no validation           |
| **Mockoon**        | GUI configuration     | Click-heavy, not version controlled |
| **Prism**          | Requires OpenAPI spec | Extra documentation burden          |
| **mockapi-server** | **Schema = API**      | Types are source of truth           |

## Documentation

**[📚 Complete Documentation](https://sudzxd.github.io/mockapi-server)**

**User Guide:**

- [Getting Started](docs/getting-started.md) - Installation and first API (5 minutes)
- [CLI Reference](docs/cli-reference.md) - Complete command reference
- [API Reference](docs/api-reference.md) - REST endpoint documentation
- [Examples](docs/examples.md) - Common patterns and use cases
- [FAQ](docs/faq.md) - Frequently asked questions
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions

**Developer Guide:**

- [Architecture](docs/architecture.md) - DDD design and layer structure
- [Development Setup](docs/development/setup.md) - Local environment
- [Guidelines](docs/development/guidelines.md) - Code standards, Git workflow, SOLID
- [Testing](docs/development/testing.md) - Test strategy and coverage
- [Releasing](docs/development/releasing.md) - Version management

## Development

```bash
# Clone repo
git clone https://github.com/sudzxd/mockapi-server.git
cd mockapi-server

# Setup environment
make dev

# Run tests
make test

# Run quality checks
make check
```

See [Development Setup](docs/development/setup.md) for details.

## Status

Active development. Production-ready for development and testing environments.

**Coverage:** 71%
**Tests:** 113 passing

## Contributing

Contributions welcome! See [Guidelines](docs/development/guidelines.md) for:

- Git workflow (conventional commits)
- Code standards (Python 3.11+, SOLID principles)
- Testing requirements (90%+ coverage)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Links

- **GitHub:** [github.com/sudzxd/mockapi-server](https://github.com/sudzxd/mockapi-server)
- **Issues:** [github.com/sudzxd/mockapi-server/issues](https://github.com/sudzxd/mockapi-server/issues)
- **PyPI:** [pypi.org/project/mockapi-server](https://pypi.org/project/mockapi-server/)
- **Docs:** [sudzxd.github.io/mockapi-server](https://sudzxd.github.io/mockapi-server)
