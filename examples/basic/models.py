"""Basic example models for mockapi-server.

Simple User and Product API demonstrating core functionality.
"""

from datetime import datetime

from pydantic import BaseModel


class User(BaseModel):
    """User model with basic profile information."""

    id: int
    name: str
    email: str
    age: int | None = None
    created_at: datetime


class Product(BaseModel):
    """Product model with pricing and inventory."""

    id: int
    name: str
    description: str
    price: float
    in_stock: bool = True
    created_at: datetime
