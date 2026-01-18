# Examples

Common patterns and usage scenarios for mockapi-server.

## Complete Working Examples

Ready-to-run example projects are available in the [`examples/`](../examples/) directory:

| Example | Description | Features |
|---------|-------------|----------|
| **[Basic](../examples/basic/)** | User and Product API | Simple models, HTML client |
| **[Blog](../examples/blog/)** | Multi-model relationships | User/Post/Comment, Docker setup |
| **[E-commerce](../examples/ecommerce/)** | Complex relationships | Product/Order/Customer, Postman collection |

Each example includes complete schema definitions, setup instructions, and testing tools.

## Schema Patterns

### Basic Model

Minimal required fields:

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int  # Primary key (required)
    name: str
    email: str
```

### Optional Fields

Union type syntax for nullable fields:

```python
from datetime import datetime

class User(BaseModel):
    id: int
    name: str
    email: str
    bio: str | None = None  # Optional, 50% chance of None when generated
    age: int | None = None
    created_at: datetime
```

### Foreign Key Relationships

Pattern: `<model_name>_id` auto-detected as foreign key:

```python
class Post(BaseModel):
    id: int
    title: str
    content: str
    author_id: int  # FK → User.id
    published_at: datetime | None = None

class Comment(BaseModel):
    id: int
    text: str
    post_id: int   # FK → Post.id
    user_id: int   # FK → User.id
    created_at: datetime
```

Generated data ensures all foreign key values reference existing entities.

### Enumerations

Type-safe status fields:

```python
from enum import Enum

class Status(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"

class Task(BaseModel):
    id: int
    title: str
    status: Status  # Randomly selects from enum values
```

## CLI Usage Patterns

### Development Workflow

```bash
# Quick prototype with generated data
mockapi-server serve models.py --generate-data --data-count 50

# Production-like setup with persistence
mockapi-server serve models.py --storage json://./data.json

# Custom port for parallel instances
mockapi-server serve models.py --port 8000 --generate-data
```

### Data Generation

```bash
# Control data volume per model
mockapi-server serve models.py --generate-data --data-count 100

# Reproducible data (same seed = same data)
mockapi-server serve models.py --generate-data --seed 42
```

## API Usage Patterns

### CRUD Operations

**Create:**
```bash
POST /api/v1/users
Content-Type: application/json

{"name": "Alice", "email": "alice@example.com", "created_at": "2025-01-17T10:00:00Z"}
```

**Read:**
```bash
GET /api/v1/users/1
```

**Update (partial):**
```bash
PUT /api/v1/users/1
Content-Type: application/json

{"email": "alice.updated@example.com"}
```

**Delete:**
```bash
DELETE /api/v1/users/1
```

### Bulk Operations

**Bulk Create:**
```bash
POST /api/v1/users/bulk
Content-Type: application/json

{
  "data": [
    {"name": "Alice", "email": "alice@example.com", "created_at": "2025-01-17T10:00:00Z"},
    {"name": "Bob", "email": "bob@example.com", "created_at": "2025-01-17T11:00:00Z"}
  ]
}
```

**Bulk Update:**
```bash
PUT /api/v1/users/bulk
Content-Type: application/json

{
  "data": [
    {"id": 1, "name": "Alice Updated"},
    {"id": 2, "name": "Bob Updated"}
  ]
}
```

**Bulk Delete:**
```bash
DELETE /api/v1/users/bulk?ids=1,2,3,4,5
```

### Query Patterns

#### Filtering

**Field equality:**
```bash
GET /api/v1/users?status=active
```

**Comparison operators:**
```bash
GET /api/v1/users?age__gte=18          # Greater than or equal
GET /api/v1/posts?views__gt=100        # Greater than
GET /api/v1/products?price__lte=50.00  # Less than or equal
```

**String matching (case-insensitive):**
```bash
GET /api/v1/users?name__contains=smith
GET /api/v1/users?email__startswith=admin
GET /api/v1/users?domain__endswith=.org
```

**IN operator:**
```bash
GET /api/v1/posts?id__in=1,2,3,4,5
GET /api/v1/users?status__in=active,pending
```

**NULL checks:**
```bash
GET /api/v1/users?bio=null           # bio IS NULL
GET /api/v1/posts?published_at=null  # Not published
```

**Relationship queries:**
```bash
GET /api/v1/posts?author_id=5        # All posts by user 5
GET /api/v1/comments?post_id=10      # All comments on post 10
```

#### Sorting

**Single field (ascending):**
```bash
GET /api/v1/users?sort=name
```

**Descending (prefix with `-`):**
```bash
GET /api/v1/posts?sort=-created_at
```

**Multiple fields:**
```bash
GET /api/v1/users?sort=-created_at,name  # By creation date desc, then name asc
```

#### Pagination

**Page-based:**
```bash
GET /api/v1/users?page=1&page_size=20
```

**Offset-based:**
```bash
GET /api/v1/users?offset=40&limit=20
```

Response includes pagination metadata:
```json
{
  "items": [...],
  "total": 100,
  "page": 3,
  "page_size": 20,
  "has_next": true,
  "has_prev": true
}
```

#### Combined Queries

Filter, sort, and paginate together:

```bash
GET /api/v1/posts?author_id=5&published=true&sort=-views&page=1&page_size=10
```

## Frontend Integration

### REST API Client Pattern

```javascript
// api.js - Type-safe API client
const API_BASE = "http://localhost:3000/api/v1";

export const api = {
  async getUsers() {
    const res = await fetch(`${API_BASE}/users`);
    return res.json();
  },

  async getUser(id) {
    const res = await fetch(`${API_BASE}/users/${id}`);
    if (!res.ok) throw new Error(`User ${id} not found`);
    return res.json();
  },

  async createUser(data) {
    const res = await fetch(`${API_BASE}/users`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return res.json();
  },

  async updateUser(id, data) {
    const res = await fetch(`${API_BASE}/users/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return res.json();
  },

  async deleteUser(id) {
    await fetch(`${API_BASE}/users/${id}`, { method: "DELETE" });
  },
};
```

### Usage

```javascript
// Fetch and display users
const users = await api.getUsers();
console.log(users.items);  // Array of user objects

// Create new user
const newUser = await api.createUser({
  name: "Alice",
  email: "alice@example.com",
  created_at: new Date().toISOString()
});

// Update user
await api.updateUser(1, { email: "alice.new@example.com" });
```

For complete React/Vue examples, see [`examples/basic/client.html`](../examples/basic/client.html).

## Configuration Patterns

### YAML Configuration

```yaml
# mockapi-server.yml
seed_count: 100
port: 3000
host: 0.0.0.0
log_level: INFO
auto_reload: true
cors_enabled: true
cors_origins:
  - "http://localhost:3001"
  - "http://localhost:8080"
```

### Usage

```bash
mockapi-server serve models.py --config mockapi-server.yml --generate-data
```

### Storage Options

**In-memory (default):**
```bash
mockapi-server serve models.py --storage memory://
```

**JSON persistence:**
```bash
mockapi-server serve models.py --storage json://./data.json
```

**Future:** SQLite, PostgreSQL, Redis support planned.

## Testing Patterns

### Postman Collection

```json
{
  "info": { "name": "User API Tests" },
  "item": [
    {
      "name": "List Users",
      "request": {
        "method": "GET",
        "url": "http://localhost:3000/api/v1/users"
      }
    },
    {
      "name": "Create User",
      "request": {
        "method": "POST",
        "url": "http://localhost:3000/api/v1/users",
        "body": {
          "mode": "raw",
          "raw": "{\"name\": \"Test\", \"email\": \"test@example.com\"}"
        }
      }
    }
  ]
}
```

See [`examples/ecommerce/postman/`](../examples/ecommerce/postman/) for complete collection.

### Docker Integration

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN pip install mockapi-server
COPY models.py .
CMD ["mockapi-server", "serve", "models.py", "--host", "0.0.0.0", "--generate-data"]
```

```yaml
# docker-compose.yml
version: "3.8"
services:
  mockapi:
    build: .
    ports:
      - "3000:3000"
    volumes:
      - ./models.py:/app/models.py
```

See [`examples/blog/docker-compose.yml`](../examples/blog/docker-compose.yml) for complete setup.

## Available Filter Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `eq` (default) | Exact match | `?status=active` |
| `gt` | Greater than | `?age__gt=18` |
| `gte` | Greater than or equal | `?price__gte=10.00` |
| `lt` | Less than | `?count__lt=100` |
| `lte` | Less than or equal | `?age__lte=65` |
| `contains` | Substring match (case-insensitive) | `?name__contains=john` |
| `startswith` | Prefix match (case-insensitive) | `?email__startswith=admin` |
| `endswith` | Suffix match (case-insensitive) | `?domain__endswith=.com` |
| `in` | IN operator (comma-separated) | `?id__in=1,2,3` |
| `nin` | NOT IN operator | `?status__nin=deleted,archived` |

## Next Steps

- [CLI Reference](cli-reference.md) - Complete command documentation
- [API Reference](api-reference.md) - REST endpoint specifications
- [FAQ](faq.md) - Common questions and answers
