# Basic Example

Simple two-model API demonstrating core mockapi-server functionality.

## Models

- **User** - Basic user profile with email validation
- **Product** - Product catalog with pricing

## Quick Start

```bash
# From this directory
mockapi-server serve models.py --generate-data --data-count 20
```

Server starts at `http://localhost:3000`

## Interactive Web Client

Open `client.html` in your browser to interact with the API visually:

```bash
# Start the server first
mockapi-server serve models.py --generate-data --data-count 20

# Then open client.html in your browser
open client.html  # macOS
xdg-open client.html  # Linux
start client.html  # Windows
```

The web client provides:
- View all users and products
- Filter, sort, and paginate data
- Create, update, and delete entities
- Real-time API interaction

## Available Endpoints

### Users

```bash
# List users (with filtering, sorting, pagination)
GET http://localhost:3000/api/v1/User
GET http://localhost:3000/api/v1/User?age__gte=25&sort=-created_at

# Get single user
GET http://localhost:3000/api/v1/User/1

# Create user
POST http://localhost:3000/api/v1/User
Content-Type: application/json

{
  "id": 999,
  "name": "Alice",
  "email": "alice@example.com",
  "age": 30,
  "created_at": "2025-01-10T10:00:00Z"
}

# Update user (partial)
PUT http://localhost:3000/api/v1/User/1
Content-Type: application/json

{
  "age": 31
}

# Delete user
DELETE http://localhost:3000/api/v1/User/1

# Bulk operations
POST http://localhost:3000/api/v1/User/bulk
PUT http://localhost:3000/api/v1/User/bulk
DELETE http://localhost:3000/api/v1/User/bulk?ids=1,2,3
```

### Products

```bash
# List products
GET http://localhost:3000/api/v1/Product
GET http://localhost:3000/api/v1/Product?in_stock=true&price__lte=100

# All CRUD operations same as Users
```

## Interactive Documentation

- **Swagger UI:** `http://localhost:3000/docs`
- **ReDoc:** `http://localhost:3000/redoc`

## Testing with curl

```bash
# List all users
curl http://localhost:3000/api/v1/User

# Filter users by age
curl "http://localhost:3000/api/v1/User?age__gte=25"

# Sort products by price (descending)
curl "http://localhost:3000/api/v1/Product?sort=-price"

# Paginate results
curl "http://localhost:3000/api/v1/User?page=1&page_size=5"

# Create a new product
curl -X POST http://localhost:3000/api/v1/Product \
  -H "Content-Type: application/json" \
  -d '{
    "id": 100,
    "name": "Laptop",
    "description": "High-performance laptop",
    "price": 1299.99,
    "in_stock": true,
    "created_at": "2025-01-10T10:00:00Z"
  }'
```

## Query Operators

Available for all fields:

- `eq` (default): `?name=John`
- `ne`: `?status__ne=inactive`
- `gt`, `gte`: `?age__gte=18`
- `lt`, `lte`: `?price__lte=100`
- `in`: `?id__in=1,2,3,4,5`
- `nin`: `?status__nin=deleted,archived`
- `contains`: `?name__contains=smith`
- `startswith`: `?email__startswith=admin`
- `endswith`: `?email__endswith=@example.com`

## Data Persistence

Add JSON file storage to persist data across restarts:

```bash
mockapi-server serve models.py --storage-url json://./data.json --generate-data
```

Data will be saved to `data.json` and loaded on next startup.

## Next Steps

- Explore [CLI Reference](../../docs/cli-reference.md) for all options
- Read [API Reference](../../docs/api-reference.md) for detailed endpoint docs
