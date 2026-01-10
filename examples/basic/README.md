# Basic Example

Simple two-model API demonstrating User and Product models.

## Setup

```bash
# From this directory
mockapi-server serve --models models.py --generate-data --data-count 20
```

## Access

- API: http://localhost:3000/api/v1
- Docs: http://localhost:3000/docs
- Client: Open `client.html` in your browser

## Available Endpoints

- GET/POST/PUT/DELETE `/users`
- GET/POST/PUT/DELETE `/products`

See [examples documentation](../../docs/examples.md) for detailed usage patterns.
