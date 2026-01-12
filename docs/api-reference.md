# API Reference

Complete reference for both the Python API and REST endpoints.

## Python API

### Server

Main entry point for creating a mock API server.

```python
from mock_api.core.server import Server

server = Server(
    models_file="models.py",
    prefix="/api/v1",
    generate_data=True,
    data_count=50
)

app = server.create_app()
```

#### Parameters

- **models_file** (`str`, required): Path to Python file with Pydantic models
- **prefix** (`str`, default: `"/api/v1"`): API route prefix
- **generate_data** (`bool`, default: `False`): Pre-populate with generated data
- **data_count** (`int`, default: `10`): Instances per model when generating
- **config** (`Config | None`, default: `None`): Configuration instance

#### Properties

- **app** (`FastAPI`): Get FastAPI app, creating if necessary
- **schemas** (`dict[str, ModelSchema]`): Parsed model schemas
- **store** (`DataStore`): Data storage instance

#### Methods

##### create_app()

Create and configure FastAPI application.

**Returns:** `FastAPI` - Configured FastAPI application

**Example:**

```python
server = Server("models.py")
app = server.create_app()
```

##### populate_data()

Pre-populate store with generated data.

**Example:**

```python
server = Server("models.py")
app = server.create_app()
server.populate_data()  # Fill with generated data
```

---

### SchemaParser

Parse Pydantic models from Python files.

```python
from mock_api.core.parser import SchemaParser

parser = SchemaParser()
schemas = parser.parse_file("models.py")
```

#### Methods

##### parse_file(file_path: str)

Parse Pydantic models from a Python file.

**Parameters:**

- **file_path** (`str`): Path to Python file

**Returns:** `dict[str, ModelSchema]` - Parsed schemas by model name

**Raises:**

- `FileNotFoundError`: If file doesn't exist
- `ValueError`: If file is invalid

**Example:**

```python
parser = SchemaParser()
schemas = parser.parse_file("models.py")

for name, schema in schemas.items():
    print(f"Model: {name}")
    print(f"Fields: {len(schema.fields)}")
    print(f"Relationships: {len(schema.relationships)}")
```

---

### DataGenerator

Generate realistic fake data from schemas.

```python
from mock_api.core.generator import DataGenerator
from mock_api.core.parser import SchemaParser

parser = SchemaParser()
schemas = parser.parse_file("models.py")

generator = DataGenerator(schemas)
users = generator.generate("User", count=50)
```

#### Parameters

- **schemas** (`dict[str, ModelSchema]`, required): Model schemas
- **config** (`Config | None`, default: `None`): Configuration instance

#### Methods

##### generate(model_name: str, count: int)

Generate fake data instances for a model.

**Parameters:**

- **model_name** (`str`): Name of model to generate
- **count** (`int`): Number of instances to generate

**Returns:** `list[dict]` - Generated data instances

**Example:**

```python
# Generate 100 users
users = generator.generate("User", count=100)

# Access generated data
print(users[0])
# {'id': 1, 'name': 'Alice Johnson', 'email': 'alice.johnson@example.com'}
```

---

### DataStore

In-memory CRUD data store.

```python
from mock_api.core.store import DataStore

store = DataStore()
```

#### Methods

##### create(model_name: str, data: dict)

Create a new instance.

**Parameters:**

- **model_name** (`str`): Model name
- **data** (`dict`): Instance data

**Returns:** `dict` - Created instance

**Example:**

```python
user = store.create("User", {
    "id": 1,
    "name": "Alice",
    "email": "alice@example.com"
})
```

##### get(model_name: str, id: int)

Get instance by ID.

**Parameters:**

- **model_name** (`str`): Model name
- **id** (`int`): Instance ID

**Returns:** `dict | None` - Instance or None if not found

**Example:**

```python
user = store.get("User", 1)
if user:
    print(user["name"])
```

##### get_all(model_name: str, filters: dict | None)

Get all instances, optionally filtered.

**Parameters:**

- **model_name** (`str`): Model name
- **filters** (`dict | None`): Filter criteria

**Returns:** `list[dict]` - Matching instances

**Example:**

```python
# Get all users
users = store.get_all("User")

# Get filtered users
active_users = store.get_all("User", {"active": True})
```

##### update(model_name: str, id: int, data: dict)

Update an existing instance.

**Parameters:**

- **model_name** (`str`): Model name
- **id** (`int`): Instance ID
- **data** (`dict`): Updated data

**Returns:** `dict | None` - Updated instance or None if not found

**Example:**

```python
updated = store.update("User", 1, {
    "name": "Alice Updated"
})
```

##### delete(model_name: str, id: int)

Delete an instance.

**Parameters:**

- **model_name** (`str`): Model name
- **id** (`int`): Instance ID

**Returns:** `bool` - True if deleted, False if not found

**Example:**

```python
deleted = store.delete("User", 1)
```

##### count(model_name: str)

Count instances of a model.

**Parameters:**

- **model_name** (`str`): Model name

**Returns:** `int` - Number of instances

**Example:**

```python
user_count = store.count("User")
print(f"Total users: {user_count}")
```

---

## REST API Endpoints

All endpoints follow standard REST conventions.

### Base URL

Default: `http://localhost:3000/api/v1`

Configurable via `--prefix` option.

### Standard Endpoints

For each model (e.g., `User`), the following endpoints are generated:

#### List All

```http
GET /api/v1/users
```

**Response:**

```json
[
  {
    "id": 1,
    "name": "Alice Johnson",
    "email": "alice@example.com",
    "created_at": "2025-01-10T10:00:00Z"
  },
  {
    "id": 2,
    "name": "Bob Smith",
    "email": "bob@example.com",
    "created_at": "2025-01-09T15:30:00Z"
  }
]
```

#### Get One

```http
GET /api/v1/users/{id}
```

**Response:**

```json
{
  "id": 1,
  "name": "Alice Johnson",
  "email": "alice@example.com",
  "created_at": "2025-01-10T10:00:00Z"
}
```

**Error (404):**

```json
{
  "detail": "User with id 999 not found"
}
```

#### Create

```http
POST /api/v1/users
Content-Type: application/json

{
  "id": 100,
  "name": "New User",
  "email": "new@example.com",
  "created_at": "2025-01-10T12:00:00Z"
}
```

**Response (201):**

```json
{
  "id": 100,
  "name": "New User",
  "email": "new@example.com",
  "created_at": "2025-01-10T12:00:00Z"
}
```

**Error (422 - Validation):**

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "email"],
      "msg": "Field required"
    }
  ]
}
```

#### Update

```http
PUT /api/v1/users/{id}
Content-Type: application/json

{
  "id": 1,
  "name": "Updated Name",
  "email": "updated@example.com",
  "created_at": "2025-01-10T12:00:00Z"
}
```

**Response:**

```json
{
  "id": 1,
  "name": "Updated Name",
  "email": "updated@example.com",
  "created_at": "2025-01-10T12:00:00Z"
}
```

#### Delete

```http
DELETE /api/v1/users/{id}
```

**Response (204 No Content)**

---

## Query Parameters

### Filtering

Filter results by field values:

```http
GET /api/v1/posts?author_id=5
GET /api/v1/users?active=true
```

Multiple filters are AND'ed:

```http
GET /api/v1/posts?author_id=5&published=true
```

### Pagination

**Page-based (default):**

```http
GET /api/v1/users?page=1&page_size=20
```

**Offset-based:**

```http
GET /api/v1/users?offset=0&limit=10
```

Both return:

```json
{
  "items": [...],
  "pagination": {
    "total_items": 100,
    "has_next": true,
    "has_prev": false
  }
}
```

Cannot mix strategies in one request. Configure defaults in `mockapi-server.yml`.

---

## Model Schema Types

### ModelSchema

```python
@dataclass
class ModelSchema:
    name: str                          # Model name
    model_class: type[BaseModel]       # Pydantic model class
    fields: list[FieldSchema]          # Field definitions
    relationships: list[Relationship]  # Detected relationships
```

### FieldSchema

```python
@dataclass
class FieldSchema:
    name: str              # Field name
    type: type             # Python type
    is_optional: bool      # Whether field is optional
    default: Any           # Default value
    is_foreign_key: bool   # Whether field is FK
    related_model: str | None  # Related model name if FK
```

### Relationship

```python
@dataclass
class Relationship:
    field_name: str           # Relationship field name
    related_model: str        # Target model name
    relationship_type: str    # "one_to_many" or "many_to_one"
    foreign_key_field: str    # FK field name
```

---

## Type Mappings

### Pydantic to Python

| Pydantic Type | Python Type | Generated Data                |
| ------------- | ----------- | ----------------------------- |
| `int`         | `int`       | Random integer                |
| `str`         | `str`       | Random text or semantic match |
| `bool`        | `bool`      | Random boolean                |
| `float`       | `float`     | Random float                  |
| `datetime`    | `datetime`  | Random datetime               |
| `date`        | `date`      | Random date                   |
| `UUID`        | `UUID`      | Random UUID                   |

### Field Name Semantics

Generator detects field names and generates appropriate data:

| Field Name Pattern   | Generated Data Type |
| -------------------- | ------------------- |
| `*email*`            | Valid email address |
| `*phone*`            | Phone number        |
| `*url*`, `*website*` | URL                 |
| `*name`              | Person name         |
| `first_name`         | First name          |
| `last_name`          | Last name           |
| `*address*`          | Street address      |
| `*city*`             | City name           |
| `*country*`          | Country name        |
| `*company*`          | Company name        |

---

## Interactive Documentation

Visit `/docs` or `/redoc` endpoints for:

- Full API schema
- Request/response examples
- Interactive testing
- Model definitions

**Example:** `http://localhost:3000/docs`
