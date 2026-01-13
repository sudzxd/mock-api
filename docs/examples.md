# Examples

Real-world patterns demonstrating mockapi-server capabilities.

## Complete Working Examples

For ready-to-run example projects, see the [examples/](../examples/) directory:

- **[Basic](../examples/basic/)** - Simple User and Product API with interactive HTML client
- **[Blog](../examples/blog/)** - Multi-model relationships (User, Post, Comment) with Docker setup
- **[E-commerce](../examples/ecommerce/)** - Complex e-commerce system with Postman collection

Each example includes complete Pydantic models, setup instructions, and testing tools.

## Code Patterns

Below are code snippets demonstrating common usage patterns:

### Basic User API

Simple single-model API.

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

```bash
mockapi-server serve --models models.py --generate-data --data-count 20
```

Test endpoints:

```bash
curl http://localhost:3000/api/v1/users
curl http://localhost:3000/api/v1/users/1

curl -X POST http://localhost:3000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"id": 999, "name": "Test", "email": "test@example.com", "created_at": "2025-01-10T10:00:00Z"}'
```

### Bulk Operations

Process multiple entities in one request.

```bash
# Bulk create
curl -X POST http://localhost:3000/api/v1/users/bulk \
  -H "Content-Type: application/json" \
  -d '{"data": [
    {"name": "Alice", "email": "alice@example.com", "created_at": "2025-01-10T10:00:00Z"},
    {"name": "Bob", "email": "bob@example.com", "created_at": "2025-01-10T11:00:00Z"}
  ]}'

# Bulk update
curl -X PUT http://localhost:3000/api/v1/users/bulk \
  -H "Content-Type: application/json" \
  -d '{"data": [
    {"id": 1, "name": "Alice Updated", "email": "alice@example.com", "created_at": "2025-01-10T10:00:00Z"},
    {"id": 2, "name": "Bob Updated", "email": "bob@example.com", "created_at": "2025-01-10T11:00:00Z"}
  ]}'

# Bulk delete
curl -X DELETE "http://localhost:3000/api/v1/users/bulk?ids=1,2,3"
```

## Blog with Relationships

Multi-model API with foreign keys.

```python
# models.py
from datetime import datetime
from pydantic import BaseModel

class User(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

class Post(BaseModel):
    id: int
    title: str
    content: str
    author_id: int  # FK to User
    published_at: datetime | None = None

class Comment(BaseModel):
    id: int
    text: str
    post_id: int  # FK to Post
    user_id: int  # FK to User
    created_at: datetime
```

```bash
mockapi-server serve --models models.py --generate-data --data-count 50
```

Query relationships:

```bash
# Get user's posts
curl "http://localhost:3000/api/v1/posts?author_id=1"

# Get post's comments
curl "http://localhost:3000/api/v1/comments?post_id=5"
```

Foreign keys automatically reference valid IDs.

## Pagination

**Page-based:**

```bash
curl "http://localhost:3000/api/v1/users?page=1&page_size=10"
```

**Offset-based:**

```bash
curl "http://localhost:3000/api/v1/users?offset=0&limit=10"
```

Both return `items` array with `pagination` metadata including `has_next` and `has_prev`.

## Filtering and Sorting

**Filter by field value:**

```bash
# Equality
curl "http://localhost:3000/api/v1/users?status=active"

# Comparison operators
curl "http://localhost:3000/api/v1/users?age__gte=18"
curl "http://localhost:3000/api/v1/posts?views__gt=100"

# String matching (case-insensitive)
curl "http://localhost:3000/api/v1/users?name__contains=smith"
curl "http://localhost:3000/api/v1/users?email__endswith=@example.com"

# IN operator
curl "http://localhost:3000/api/v1/posts?id__in=1,2,3,4,5"

# Null values
curl "http://localhost:3000/api/v1/users?bio=null"
```

**Sort results:**

```bash
# Ascending
curl "http://localhost:3000/api/v1/users?sort=name"

# Descending (prefix with -)
curl "http://localhost:3000/api/v1/posts?sort=-created_at"

# Multiple fields
curl "http://localhost:3000/api/v1/users?sort=-created_at,name"
```

**Combine features:**

```bash
# Filter + Sort + Paginate
curl "http://localhost:3000/api/v1/posts?author_id=5&published=true&sort=-views&page=1&page_size=10"
```

Available operators: `eq` (default), `gt`, `gte`, `lt`, `lte`, `contains`, `startswith`, `endswith`, `in`

## Frontend Integration

Using mock API with React/Vue/etc.

```javascript
// api.js
const API_BASE = "http://localhost:3000/api/v1";

export const api = {
  async getUsers() {
    const response = await fetch(`${API_BASE}/users`);
    return response.json();
  },

  async getUser(id) {
    const response = await fetch(`${API_BASE}/users/${id}`);
    return response.json();
  },

  async createUser(data) {
    const response = await fetch(`${API_BASE}/users`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return response.json();
  },

  async updateUser(id, data) {
    const response = await fetch(`${API_BASE}/users/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return response.json();
  },

  async deleteUser(id) {
    await fetch(`${API_BASE}/users/${id}`, { method: "DELETE" });
  },
};
```

React example:

```javascript
// UserList.jsx
import { useEffect, useState } from "react";
import { api } from "./api";

function UserList() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getUsers().then((data) => {
      setUsers(data);
      setLoading(false);
    });
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <ul>
      {users.map((user) => (
        <li key={user.id}>
          {user.name} - {user.email}
        </li>
      ))}
    </ul>
  );
}
```

## Configuration

Use `mockapi-server.yml` for project settings:

```yaml
# mockapi-server.yml
seed_count: 100
port: 3000
log_level: INFO
cors_enabled: true
cors_origins:
  - "http://localhost:3001"
  - "http://localhost:8080"
```

```bash
mockapi-server serve --models models.py --config mockapi-server.yml --generate-data
```
