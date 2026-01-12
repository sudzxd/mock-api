"""E-commerce example models demonstrating complex relationships.

This example shows a realistic e-commerce system with customers,
products, orders, and order items with multiple foreign key relationships.
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from datetime import datetime

# Third-party
from pydantic import BaseModel

# =============================================================================
# MODELS
# =============================================================================


class Customer(BaseModel):
    """Customer with profile and contact information."""

    id: int
    name: str
    email: str
    phone: str | None = None
    address: str | None = None
    created_at: datetime


class Product(BaseModel):
    """Product catalog item."""

    id: int
    name: str
    description: str
    price: float
    category: str
    stock_quantity: int
    created_at: datetime


class Order(BaseModel):
    """Customer order with status tracking."""

    id: int
    customer_id: int  # Foreign key to Customer
    status: str  # pending, processing, shipped, delivered, cancelled
    total_amount: float
    created_at: datetime
    updated_at: datetime


class OrderItem(BaseModel):
    """Line item in an order."""

    id: int
    order_id: int  # Foreign key to Order
    product_id: int  # Foreign key to Product
    quantity: int
    unit_price: float
    subtotal: float
