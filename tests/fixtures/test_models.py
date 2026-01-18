"""Test Pydantic models for parser testing."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from datetime import datetime

# Third-party
from pydantic import BaseModel


# =============================================================================
# TEST MODELS
# =============================================================================
class User(BaseModel):
    """Test User model."""

    id: int
    name: str
    email: str
    age: int | None = None
    created_at: datetime


class Post(BaseModel):
    """Test Post model with foreign key."""

    id: int
    title: str
    content: str
    user_id: int  # FK to User
    created_at: datetime


class Product(BaseModel):
    """Test Product model with defaults."""

    id: int
    name: str
    description: str | None = None
    price: float
    in_stock: bool = True
    created_at: datetime
