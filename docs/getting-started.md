# Getting Started

Create your first mock API project in 5 minutes.

## Installation

```bash
pip install mock-api
```

Verify:

```bash
mock-api --version
```

## Quick Start

### Option 1: Initialize with Template

```bash
mock-api init

# Or non-interactive
mock-api init --template blog --project-name my-blog --seed-count 50
```

Available templates: **basic**, **blog**, **ecommerce**, **custom**

### Option 2: Manual Setup

Create your models:

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

Start the server:

```bash
mock-api serve --models models.py --generate-data --data-count 20
```

## Your First API Request

```bash
# List all users
curl http://localhost:3000/api/v1/users

# Get specific user
curl http://localhost:3000/api/v1/users/1

# Create user
curl -X POST http://localhost:3000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"id": 999, "name": "Alice", "email": "alice@example.com", "created_at": "2025-01-10T10:00:00Z"}'
```

## Interactive Docs

Visit `http://localhost:3000/docs` for Swagger UI:

- Browse all endpoints
- See request/response schemas
- Test API calls in browser

Alternative: `http://localhost:3000/redoc`

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

## Configuration

Create `mock-api.yml`:

```yaml
seed_count: 50
port: 3000
host: 0.0.0.0
log_level: INFO
auto_reload: true
cors_enabled: true
cors_origins: ["*"]
```

Use it:

```bash
mock-api serve --models models.py --config mock-api.yml
```

## Next Steps

- [CLI Reference](cli-reference.md) - All commands and options
- [API Reference](api-reference.md) - Python and REST APIs
- [Examples](examples.md) - Real-world use cases
- [FAQ](faq.md) - Common questions
