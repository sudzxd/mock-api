# CLI Reference

Complete command-line interface reference for mockapi-server.

## Supported Schema Formats

| Format | Extensions | Status | Description |
|--------|-----------|--------|-------------|
| **Pydantic** | `.py` | ✅ Implemented | Python Pydantic BaseModel classes |
| **OpenAPI** | `.yaml`, `.json` | 📋 Planned | OpenAPI 3.x specifications |
| **GraphQL** | `.graphql`, `.gql` | 📋 Planned | GraphQL schema definitions |

Currently, only Pydantic models are supported. All formats will convert to a unified internal representation (`ModelSchema`).

## Global Options

```bash
mockapi-server --version  # Show version and exit
mockapi-server --help     # Show help message
```

## Commands

### serve

Start development server from schema file.

**Usage:**
```bash
mockapi-server serve SCHEMA_FILE [OPTIONS]
```

**Arguments:**

| Argument      | Type | Description |
|---------------|------|-------------|
| `SCHEMA_FILE` | PATH | Path to schema file (required) |

**Options:**

| Option               | Type | Default      | Description |
|----------------------|------|--------------|-------------|
| `--host`             | TEXT | `0.0.0.0`    | Host to bind server |
| `--port`             | INT  | `8000`       | Port to bind server |
| `--reload`           | FLAG | False        | Enable auto-reload on file changes |
| `--generate-data`    | FLAG | False        | Pre-populate with fake data on startup |
| `--no-generate-data` | FLAG | -            | Explicitly disable data generation |
| `--data-count`       | INT  | `10`         | Number of entities to generate per model |
| `--storage-url`      | TEXT | `memory://`  | Storage backend URL |

**Storage Backends:**

| URL Format | Status | Description | Persistence |
|------------|--------|-------------|-------------|
| `memory://` | ✅ Implemented | In-memory storage (default) | Lost on restart |
| `json://path/file.json` | 📋 Planned | JSON file storage | Persists across restarts |
| `sqlite:///path/file.db` | 📋 Planned | SQLite database | Persists across restarts |

**Examples:**

```bash
# Basic usage
mockapi-server serve models.py

# With fake data generation
mockapi-server serve models.py --generate-data --data-count 50

# Custom host and port
mockapi-server serve models.py --host localhost --port 8000

# Development mode with auto-reload
mockapi-server serve models.py --reload

# All options
mockapi-server serve models.py \
  --host 0.0.0.0 \
  --port 8000 \
  --reload \
  --generate-data \
  --data-count 100 \
  --storage-url memory://
```

**Server URLs:**

Once started, access:
- **API Base:** `http://{host}:{port}/api/v1`
- **Swagger UI:** `http://{host}:{port}/docs`
- **ReDoc:** `http://{host}:{port}/redoc`

**Typical Workflow:**

```bash
# 1. Start with generated data for testing
mockapi-server serve models.py --generate-data --data-count 20

# 2. Visit Swagger UI to explore API
open http://localhost:8000/docs

# 3. Test endpoints (note: model names are used as-is, e.g., User not users)
curl http://localhost:8000/api/v1/User
curl http://localhost:8000/api/v1/User/1
```

---

## REST API Structure

### Endpoint Pattern

For each model in your schema, the following endpoints are auto-generated.

**Model Name Convention:** Endpoint paths use the exact model name (e.g., `User` → `/User`, `BlogPost` → `/BlogPost`). No lowercasing or pluralization is applied.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/{ModelName}` | List all entities (with filtering, sorting, pagination) |
| `GET` | `/api/v1/{ModelName}/{id}` | Get single entity by ID |
| `POST` | `/api/v1/{ModelName}` | Create new entity |
| `PUT` | `/api/v1/{ModelName}/{id}` | Update entity (partial update supported) |
| `DELETE` | `/api/v1/{ModelName}/{id}` | Delete entity by ID |
| `POST` | `/api/v1/{ModelName}/bulk` | Bulk create multiple entities |
| `PUT` | `/api/v1/{ModelName}/bulk` | Bulk update multiple entities |
| `DELETE` | `/api/v1/{ModelName}/bulk` | Bulk delete entities by IDs |

### Query Parameters

**Filtering:**

Supported operators: `eq` (default), `ne`, `gt`, `gte`, `lt`, `lte`, `in`, `nin`, `contains`

```bash
# Exact match (default operator)
GET /api/v1/User?status=active

# Comparison operators
GET /api/v1/User?age__gte=18          # >=
GET /api/v1/User?age__gt=18           # >
GET /api/v1/User?age__lte=65          # <=
GET /api/v1/User?age__lt=65           # <
GET /api/v1/User?age__ne=25           # !=

# String matching (case-insensitive substring)
GET /api/v1/User?name__contains=john

# IN operator (comma-separated values)
GET /api/v1/User?id__in=1,2,3,4,5
GET /api/v1/User?status__in=active,pending

# NOT IN operator
GET /api/v1/User?status__nin=deleted,archived
```

**Sorting:**
```bash
# Ascending (default)
GET /api/v1/User?sort=name

# Descending (prefix with -)
GET /api/v1/Post?sort=-created_at

# Multiple fields
GET /api/v1/User?sort=-created_at,name
```

**Pagination:**

Only page-based pagination is currently supported:

```bash
# Page-based pagination (default: page=1, page_size=20)
GET /api/v1/User?page=1&page_size=20
GET /api/v1/User?page=2&page_size=50
```

**Combined:**
```bash
GET /api/v1/Post?author_id=5&published=true&sort=-views&page=1&page_size=10
```

### Response Format

**List Response:**
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

**Single Entity:**
```json
{
  "id": 1,
  "name": "Alice",
  "email": "alice@example.com",
  "created_at": "2025-01-17T10:00:00Z"
}
```

**Bulk Operations:**
```json
{
  "items": [...],
  "count": 10
}
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Error (file not found, parse error, validation failed, etc.) |

---

## Environment Variables

Currently not supported. All configuration via CLI options or config files.

---

## Tips & Best Practices

**Development:**
- Use `--reload` for automatic server restart on file changes
- Use `--generate-data` to start with realistic test data
- Use `http://localhost:8000/docs` for interactive API testing

**Data Generation:**
- Start with `--data-count 10` for quick prototyping
- Use `--data-count 100+` for realistic load testing
- Foreign keys automatically reference IDs (currently random 1-100)

**Performance:**
- In-memory storage (`memory://`) is fast but data is lost on restart
- Bulk operations (`/bulk` endpoints) are significantly faster than individual creates

**Schema Design:**
- Use foreign key pattern: `author_id: int` auto-detects relationship to `Author` model
- Optional fields: `bio: str | None = None` (50% chance of None when generated)
- Model names are used exactly as defined (e.g., `User` → `/User`, not `/users`)

---

## Planned Commands

The following commands are **not yet implemented**:

### mockapi-server init

Initialize new project with template scaffolding.

### mockapi-server generate

Generate mock data files without starting server.

### mockapi-server validate

Validate schema file and show detected models.

Track progress: [GitHub Issues](https://github.com/sudzxd/mockapi-server/issues)

---

## Getting Help

```bash
# Show all commands
mockapi-server --help

# Show command-specific help
mockapi-server serve --help
```

For issues or questions:
- [GitHub Issues](https://github.com/sudzxd/mockapi-server/issues)
- [Documentation](https://github.com/sudzxd/mockapi-server/docs)
