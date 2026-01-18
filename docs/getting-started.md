# Getting Started

Create your first mock API project in under 5 minutes.

## Installation

```bash
pip install mockapi-server
```

Verify:

```bash
mockapi-server --version
```

## Quick Start

**Create a Pydantic schema file:**

```python
# models.py
from datetime import datetime
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime
```

**Start the server:**

```bash
mockapi-server serve models.py --generate-data --data-count 20
```

The server starts at `http://localhost:8000` with:
- REST API at `/api/v1`
- Interactive docs at `/docs`
- Alternative docs at `/redoc`

## Data Storage

Currently supports in-memory storage only (data lost on restart):

```bash
mockapi-server serve models.py --storage-url memory://
```

**Planned:** JSON file persistence, SQLite, PostgreSQL, Redis backends.

## Your First API Request

Endpoints use the exact model name (e.g., `User` → `/User`, not `/users`):

```bash
# List all users
curl http://localhost:8000/api/v1/User

# Get specific user
curl http://localhost:8000/api/v1/User/1

# Create user
curl -X POST http://localhost:8000/api/v1/User \
  -H "Content-Type: application/json" \
  -d '{"id": 999, "name": "Alice", "email": "alice@example.com", "created_at": "2025-01-10T10:00:00Z"}'
```

## Interactive Docs

Visit `http://localhost:8000/docs` for Swagger UI:

- Browse all endpoints
- See request/response schemas
- Test API calls in browser

Alternative: `http://localhost:8000/redoc`

## Working with Relationships

Foreign keys are automatically detected:

```python
class Post(BaseModel):
    id: int
    title: str
    content: str
    author_id: int  # Detected as FK to User
```

Generated data respects relationships - all `author_id` values reference valid User IDs.

## CLI Options

Control server behavior with command-line options:

```bash
mockapi-server serve models.py \
  --host 0.0.0.0 \
  --port 8000 \
  --reload \
  --generate-data \
  --data-count 50 \
  --storage-url memory://
```

See all options: `mockapi-server serve --help`

## Example Projects

Explore the working example in the [examples/basic/](../examples/basic/) directory:

- Simple two-model API demonstrating User/Post relationship
- Interactive HTML client for testing
- Complete setup and run instructions

**Planned:** Additional examples for blog and e-commerce use cases.

## Next Steps

- [CLI Reference](cli-reference.md) - Command-line options and usage
- [API Reference](api-reference.md) - REST API endpoints and query syntax
- [Architecture](architecture.md) - System design and DDD structure
- [FAQ](faq.md) - Common questions
