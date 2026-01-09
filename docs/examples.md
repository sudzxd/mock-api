# Examples

Real-world patterns demonstrating mock-api capabilities.

## Basic User API

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
mock-api serve --models models.py --generate-data --data-count 20
```

Test endpoints:

```bash
curl http://localhost:3000/api/v1/users
curl http://localhost:3000/api/v1/users/1

curl -X POST http://localhost:3000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"id": 999, "name": "Test", "email": "test@example.com", "created_at": "2025-01-10T10:00:00Z"}'
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
mock-api serve --models models.py --generate-data --data-count 50
```

Query relationships:

```bash
# Get user's posts
curl "http://localhost:3000/api/v1/posts?author_id=1"

# Get post's comments
curl "http://localhost:3000/api/v1/comments?post_id=5"
```

Foreign keys automatically reference valid IDs.

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

Use `mock-api.yml` for project settings:

```yaml
# mock-api.yml
seed_count: 100
port: 3000
log_level: INFO
cors_enabled: true
cors_origins:
  - "http://localhost:3001"
  - "http://localhost:8080"
```

```bash
mock-api serve --models models.py --config mock-api.yml --generate-data
```
