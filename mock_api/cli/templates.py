"""Project templates for the init command.

This module contains pre-built templates for scaffolding new mock API projects.
Each template includes model definitions, configuration, and documentation.
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from dataclasses import dataclass

# Internal
from mock_api.core.constants import TemplateType

# =============================================================================
# TEMPLATE DATACLASS
# =============================================================================


@dataclass
class ProjectTemplate:
    """Container for project template content.

    Attributes:
        name: Template name (basic, blog, ecommerce, custom).
        description: Short description of the template.
        models_content: Python code for models.py file.
        config_content: YAML content for mock-api.yml file.
        readme_content: Markdown content for README.md file.
    """

    name: str
    description: str
    models_content: str
    config_content: str
    readme_content: str


# =============================================================================
# BASIC TEMPLATE
# =============================================================================

_BASIC_MODELS = '''"""Simple API models."""

from datetime import datetime

from pydantic import BaseModel


class User(BaseModel):
    """User model."""

    id: int
    name: str
    email: str
    created_at: datetime
'''

_BASIC_CONFIG = """# Mock API Configuration
seed_count: {seed_count}
port: {port}
log_level: INFO
cors_enabled: true
cors_origins:
  - "*"
"""

_BASIC_README = """# {project_name}

A simple mock API generated with [mock-api](https://github.com/sudarshan-sagar/mock-api).

## Models

- **User**: Simple user model with id, name, email, and created_at fields

## Quick Start

1. Install mock-api:
   ```bash
   pip install mock-api
   ```

2. Start the server:
   ```bash
   mock-api serve --models models.py --generate-data
   ```

3. Visit http://localhost:{port}/docs to explore the API

## Available Endpoints

- `GET /api/v1/users` - List all users
- `GET /api/v1/users/{{id}}` - Get a specific user
- `POST /api/v1/users` - Create a new user
- `PUT /api/v1/users/{{id}}` - Update a user
- `DELETE /api/v1/users/{{id}}` - Delete a user

## Example Request

```bash
curl http://localhost:{port}/api/v1/users
```

## Configuration

Edit `mock-api.yml` to customize:
- `seed_count`: Number of instances to generate (default: {seed_count})
- `port`: Server port (default: {port})
- `log_level`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `cors_enabled`: Enable/disable CORS
"""

BASIC_TEMPLATE = ProjectTemplate(
    name=TemplateType.BASIC,
    description="Simple API with User model",
    models_content=_BASIC_MODELS,
    config_content=_BASIC_CONFIG,
    readme_content=_BASIC_README,
)

# =============================================================================
# BLOG TEMPLATE
# =============================================================================

_BLOG_MODELS = '''"""Blog API models with relationships."""

from datetime import datetime

from pydantic import BaseModel


class User(BaseModel):
    """Blog user/author."""

    id: int
    name: str
    email: str
    bio: str | None = None
    created_at: datetime


class Post(BaseModel):
    """Blog post."""

    id: int
    title: str
    content: str
    author_id: int  # Foreign key to User
    published: bool = False
    created_at: datetime
    updated_at: datetime


class Comment(BaseModel):
    """Comment on a blog post."""

    id: int
    post_id: int  # Foreign key to Post
    author_id: int  # Foreign key to User
    content: str
    created_at: datetime
'''

_BLOG_CONFIG = """# Mock API Configuration for Blog
seed_count: {seed_count}
port: {port}
log_level: INFO
cors_enabled: true
cors_origins:
  - "*"
"""

_BLOG_README = """# {project_name}

A blog API with users, posts, and comments. Generated with [mock-api](https://github.com/sudarshan-sagar/mock-api).

## Models

- **User**: Blog authors with name, email, bio
- **Post**: Blog posts with title, content, author relationship
- **Comment**: Comments on posts with author relationship

## Relationships

- Posts have an `author_id` foreign key to User
- Comments have `post_id` and `author_id` foreign keys

## Quick Start

1. Install mock-api:
   ```bash
   pip install mock-api
   ```

2. Start the server:
   ```bash
   mock-api serve --models models.py --generate-data
   ```

3. Visit http://localhost:{port}/docs to explore the API

## Available Endpoints

### Users
- `GET /api/v1/users` - List all users
- `GET /api/v1/users/{{id}}` - Get a specific user
- `POST /api/v1/users` - Create a new user
- `PUT /api/v1/users/{{id}}` - Update a user
- `DELETE /api/v1/users/{{id}}` - Delete a user

### Posts
- `GET /api/v1/posts` - List all posts (filter by `author_id`)
- `GET /api/v1/posts/{{id}}` - Get a specific post
- `POST /api/v1/posts` - Create a new post
- `PUT /api/v1/posts/{{id}}` - Update a post
- `DELETE /api/v1/posts/{{id}}` - Delete a post

### Comments
- `GET /api/v1/comments` - List all comments (filter by `post_id` or `author_id`)
- `GET /api/v1/comments/{{id}}` - Get a specific comment
- `POST /api/v1/comments` - Create a new comment
- `PUT /api/v1/comments/{{id}}` - Update a comment
- `DELETE /api/v1/comments/{{id}}` - Delete a comment

## Example Requests

```bash
# Get all posts by a specific author
curl "http://localhost:{port}/api/v1/posts?author_id=1"

# Get all comments on a specific post
curl "http://localhost:{port}/api/v1/comments?post_id=1"
```

## Configuration

Edit `mock-api.yml` to customize server settings.
"""

BLOG_TEMPLATE = ProjectTemplate(
    name=TemplateType.BLOG,
    description="User, Post, Comment models",
    models_content=_BLOG_MODELS,
    config_content=_BLOG_CONFIG,
    readme_content=_BLOG_README,
)

# =============================================================================
# ECOMMERCE TEMPLATE
# =============================================================================

_ECOMMERCE_MODELS = '''"""E-commerce API models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class OrderStatus(str, Enum):
    """Order status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Category(BaseModel):
    """Product category."""

    id: int
    name: str
    description: str


class Product(BaseModel):
    """Product for sale."""

    id: int
    name: str
    description: str
    price: float
    category_id: int  # Foreign key to Category
    stock: int = 0
    created_at: datetime


class Customer(BaseModel):
    """Customer account."""

    id: int
    name: str
    email: str
    address: str | None = None
    created_at: datetime


class Order(BaseModel):
    """Customer order."""

    id: int
    customer_id: int  # Foreign key to Customer
    product_id: int  # Foreign key to Product
    quantity: int
    total_price: float
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime
    updated_at: datetime
'''

_ECOMMERCE_CONFIG = """# Mock API Configuration for E-commerce
seed_count: {seed_count}
port: {port}
log_level: INFO
cors_enabled: true
cors_origins:
  - "*"
"""

_ECOMMERCE_README = """# {project_name}

An e-commerce API with products, categories, customers, and orders. Generated with [mock-api](https://github.com/sudarshan-sagar/mock-api).

## Models

- **Category**: Product categories
- **Product**: Products for sale with price, stock, category relationship
- **Customer**: Customer accounts with contact info
- **Order**: Customer orders with product, quantity, status

## Features

- Enum support (OrderStatus: pending, processing, shipped, delivered, cancelled)
- Foreign key relationships between entities
- Optional fields (address, etc.)

## Quick Start

1. Install mock-api:
   ```bash
   pip install mock-api
   ```

2. Start the server:
   ```bash
   mock-api serve --models models.py --generate-data
   ```

3. Visit http://localhost:{port}/docs to explore the API

## Available Endpoints

### Categories
- `GET /api/v1/categories` - List all categories
- `POST /api/v1/categories` - Create a new category

### Products
- `GET /api/v1/products` - List all products (filter by `category_id`)
- `GET /api/v1/products/{{id}}` - Get a specific product
- `POST /api/v1/products` - Create a new product
- `PUT /api/v1/products/{{id}}` - Update a product
- `DELETE /api/v1/products/{{id}}` - Delete a product

### Customers
- `GET /api/v1/customers` - List all customers
- `GET /api/v1/customers/{{id}}` - Get a specific customer
- `POST /api/v1/customers` - Create a new customer

### Orders
- `GET /api/v1/orders` - List all orders (filter by `customer_id`, `product_id`, or
  `status`)
- `GET /api/v1/orders/{{id}}` - Get a specific order
- `POST /api/v1/orders` - Create a new order
- `PUT /api/v1/orders/{{id}}` - Update order status
- `DELETE /api/v1/orders/{{id}}` - Cancel an order

## Example Requests

```bash
# Get all products in a category
curl "http://localhost:{port}/api/v1/products?category_id=1"

# Get all orders for a customer
curl "http://localhost:{port}/api/v1/orders?customer_id=1"

# Get all pending orders
curl "http://localhost:{port}/api/v1/orders?status=pending"
```

## Configuration

Edit `mock-api.yml` to customize server settings.
"""

ECOMMERCE_TEMPLATE = ProjectTemplate(
    name=TemplateType.ECOMMERCE,
    description="Product, Category, Order models",
    models_content=_ECOMMERCE_MODELS,
    config_content=_ECOMMERCE_CONFIG,
    readme_content=_ECOMMERCE_README,
)

# =============================================================================
# CUSTOM TEMPLATE
# =============================================================================

_CUSTOM_MODELS = '''"""Custom API models.

Define your Pydantic models here. Each model will automatically get:
- GET /api/v1/<model_name>s - List all instances
- GET /api/v1/<model_name>s/{id} - Get specific instance
- POST /api/v1/<model_name>s - Create instance
- PUT /api/v1/<model_name>s/{id} - Update instance
- DELETE /api/v1/<model_name>s/{id} - Delete instance

Tips:
- Add `_id` suffix to field names for automatic foreign key detection
- Use Pydantic field types for validation (EmailStr, HttpUrl, etc.)
- Optional fields use `field: Type | None = None`
- Enums work great with StrEnum or str,Enum
"""

from datetime import datetime

from pydantic import BaseModel


# Define your models below
class Example(BaseModel):
    """Example model - replace with your own."""

    id: int
    name: str
    created_at: datetime
'''

_CUSTOM_CONFIG = """# Mock API Configuration
# Customize these settings for your API

seed_count: {seed_count}  # Number of instances to generate per model
port: {port}  # Server port
log_level: INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
cors_enabled: true
cors_origins:
  - "*"

# Optional settings:
# host: "0.0.0.0"
# auto_reload: false
# strict_mode: false
"""

_CUSTOM_README = """# {project_name}

A custom mock API generated with [mock-api](https://github.com/sudarshan-sagar/mock-api).

## Quick Start

1. Install mock-api:
   ```bash
   pip install mock-api
   ```

2. Define your models in `models.py`

3. Start the server:
   ```bash
   mock-api serve --models models.py --generate-data
   ```

4. Visit http://localhost:{port}/docs to explore the API

## Defining Models

Edit `models.py` to define your Pydantic models. Here's an example:

```python
from pydantic import BaseModel, EmailStr
from datetime import datetime

class User(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime

class Post(BaseModel):
    id: int
    title: str
    content: str
    author_id: int  # Foreign key to User
    created_at: datetime
```

## Features

- Automatic CRUD endpoints for all models
- Foreign key detection (fields ending in `_id`)
- Query filtering by any field
- Pagination support
- OpenAPI documentation at `/docs`
- Data persistence during server runtime

## Configuration

Edit `mock-api.yml` to customize:
- `seed_count`: Number of instances to generate per model
- `port`: Server port
- `log_level`: Logging verbosity
- `cors_enabled`: CORS settings

## Commands

```bash
# Validate your models
mock-api validate --models models.py

# Generate sample data
mock-api generate --models models.py --count 50 --output data.json

# Start server with auto-generated data
mock-api serve --models models.py --generate-data --data-count 20
```

## Example Requests

```bash
# List all instances
curl http://localhost:{port}/api/v1/examples

# Get specific instance
curl http://localhost:{port}/api/v1/examples/1

# Create new instance
curl -X POST http://localhost:{port}/api/v1/examples \\
  -H "Content-Type: application/json" \\
  -d '{{"id": 100, "name": "Test", "created_at": "2025-01-01T00:00:00Z"}}'

# Filter by field
curl "http://localhost:{port}/api/v1/examples?name=Test"
```

## Learn More

- [mock-api Documentation](https://github.com/sudarshan-sagar/mock-api)
- [Pydantic Documentation](https://docs.pydantic.dev/)
"""

CUSTOM_TEMPLATE = ProjectTemplate(
    name=TemplateType.CUSTOM,
    description="Empty template with guidance",
    models_content=_CUSTOM_MODELS,
    config_content=_CUSTOM_CONFIG,
    readme_content=_CUSTOM_README,
)

# =============================================================================
# GITIGNORE CONTENT
# =============================================================================

GITIGNORE_CONTENT = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Mock API
*.log
.mock-api/
"""

# =============================================================================
# TEMPLATE LOOKUP
# =============================================================================

_TEMPLATES = {
    TemplateType.BASIC: BASIC_TEMPLATE,
    TemplateType.BLOG: BLOG_TEMPLATE,
    TemplateType.ECOMMERCE: ECOMMERCE_TEMPLATE,
    TemplateType.CUSTOM: CUSTOM_TEMPLATE,
}


def get_template(template_type: TemplateType) -> ProjectTemplate:
    """Get a project template by type.

    Args:
        template_type: The type of template to retrieve.

    Returns:
        The requested ProjectTemplate.

    Raises:
        KeyError: If template_type is not found.
    """
    return _TEMPLATES[template_type]
