"""Basic example models demonstrating simple API generation.

This example shows how to create a basic REST API with two simple models.
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


class User(BaseModel):
    """User model with basic profile information."""

    id: int
    name: str
    email: str
    age: int | None = None
    created_at: datetime


class Product(BaseModel):
    """Product model for simple inventory management."""

    id: int
    name: str
    description: str
    price: float
    in_stock: bool = True
    created_at: datetime
