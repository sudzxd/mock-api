# E-commerce Example

Complex multi-model API demonstrating an e-commerce system with customers, products, orders, and order items.

## Models

- **Customer**: Customer profiles with contact information
- **Product**: Product catalog with pricing and inventory
- **Order**: Customer orders with status tracking
- **OrderItem**: Line items linking orders to products

## Setup

```bash
mockapi-server serve --models models.py --generate-data --data-count 100
```

## Access

- API: http://localhost:3000/api/v1
- Docs: http://localhost:3000/docs
- Postman: Import `postman_collection.json` for ready-to-use API requests

## Query Examples

```bash
# Get all orders for customer 5
curl "http://localhost:3000/api/v1/orders?customer_id=5"

# Get all items in order 10
curl "http://localhost:3000/api/v1/orderitems?order_id=10"

# Get all order items for a specific product
curl "http://localhost:3000/api/v1/orderitems?product_id=3"

# Get products in a specific category
curl "http://localhost:3000/api/v1/products?category=electronics"
```

## Postman Collection

Import `postman_collection.json` into Postman to get:

- Pre-configured API requests for all endpoints
- Example request bodies for POST/PUT operations
- Tests for validating responses
- Environment variables for easy switching

See [examples documentation](../../docs/examples.md) for detailed usage patterns.
