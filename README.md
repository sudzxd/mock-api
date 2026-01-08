# mock-api

**Stop writing JSON files. Start with types.**

Generate full-featured REST APIs from your Pydantic models or TypeScript types in seconds.

## Quick Start

```bash
# Install
pip install mock-api

# Run
mock-api run models.py --seed 50

# Get a full REST API
# GET    /users
# GET    /users/:id
# POST   /users
# PUT    /users/:id
# DELETE /users/:id
```

## Features

- 🚀 **Zero config** - Point at your schema file and go
- 🎯 **Type-safe** - Built on Pydantic for automatic validation
- 🤖 **Smart data** - Realistic fake data based on field names
- 🔗 **Auto relationships** - Detects foreign keys, creates nested routes
- 💾 **Stateful** - CRUD operations persist during session
- 🔄 **Proxy mode** - Mix mock and real endpoints
- 🐍 **Python native** - First-class Pydantic support
- 📘 **TypeScript support** - Parse TS types too

## Why mock-api?

**json-server**: Manual JSON files that get stale
**Mockoon**: GUI clicking for every endpoint
**Prism**: Requires full OpenAPI spec

**mock-api**: Your types ARE your API contract.

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
mock-api run models.py --seed 20
# Server running on http://localhost:3000
# Seeded 20 users, 60 posts
```

```bash
curl http://localhost:3000/users/1
# {
#   "id": 1,
#   "name": "Sarah Chen",
#   "email": "sarah.chen@company.com",
#   "created_at": "2025-01-05T10:30:00Z"
# }

curl http://localhost:3000/posts?author_id=1
# Returns all posts by user 1
```

## Status

🚧 **Under active development** - Not yet ready for production use.

Star this repo to follow progress!

## License

MIT
