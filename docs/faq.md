# FAQ

Frequently asked questions about mockapi-server.

## General

### What is mockapi-server?

mockapi-server generates fully functional REST APIs from Pydantic models. It creates realistic test data, handles CRUD operations, and automatically detects relationships - all without writing API code.

### When should I use mockapi-server?

Use mockapi-server when:
- Frontend needs to develop before backend is ready
- Testing requires realistic API responses
- Prototyping requires quick API mockups
- Learning REST API concepts

### How is this different from json-server?

| Feature | mockapi-server | json-server |
|---------|----------|-------------|
| **Input** | Pydantic models (types) | JSON files (data) |
| **Data Generation** | Automatic with realistic data | Manual |
| **Relationships** | Auto-detected | Manual configuration |
| **Validation** | Pydantic automatic | None |

### Is this production-ready?

mockapi-server is designed for development and testing. For production, implement a real API using FastAPI, Django, or similar frameworks with the same Pydantic models.

## Technical

### How does foreign key detection work?

Pattern: `<model_name>_id` where `<model_name>` matches an existing model (case-insensitive).

```python
class Post(BaseModel):
    author_id: int  # Detected as FK to "User" model
    user_id: int    # Detected as FK to "User" model
```

### Can I use enums?

Yes:

```python
from enum import Enum

class Status(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"

class Task(BaseModel):
    id: int
    status: Status
```

Generated data randomly selects from enum values.

### How do I handle optional fields?

Use union type syntax:

```python
class User(BaseModel):
    id: int
    name: str
    bio: str | None = None  # Optional field
```

Generated data randomly sets optional fields to `None` or generates values.

### Does it persist data between restarts?

No, data is stored in memory only. When the server stops, all data is lost. Use `--generate-data` to re-populate on each start.

## Troubleshooting

### Server won't start

**Problem:** `FileNotFoundError: models.py not found`

**Solution:** Ensure the path is correct:

```bash
mockapi-server serve --models ./path/to/models.py
```

### Port already in use

**Solution:** Use a different port:

```bash
mockapi-server serve --models models.py --port 8000
```

Or kill the process:

```bash
lsof -i :3000
kill -9 <PID>
```

### CORS errors in browser

**Solution:** Enable CORS in config:

```yaml
# mockapi-server.yml
cors_enabled: true
cors_origins:
  - "*"  # Dev only
```

For more troubleshooting, see [Troubleshooting Guide](troubleshooting.md).
