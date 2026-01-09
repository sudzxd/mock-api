"""Pydantic models for benchmark testing.

This module contains models specifically designed for performance benchmarking:
- Contact: Simple 4-field model for baseline benchmarks
- ComplexModel: 9-field model with enums and optional fields
- Author/Book/Review: Models with foreign key relationships for FK resolution benchmarks
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from datetime import datetime
from enum import Enum

# Third-party
from pydantic import BaseModel

# =============================================================================
# SIMPLE MODEL
# =============================================================================


class Contact(BaseModel):
    """Simple 4-field model for baseline benchmarks."""

    id: int
    name: str
    email: str
    phone: str


# =============================================================================
# COMPLEX MODEL
# =============================================================================


class Status(str, Enum):
    """Status enumeration for ComplexModel."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    ARCHIVED = "archived"


class Priority(str, Enum):
    """Priority enumeration for ComplexModel."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplexModel(BaseModel):
    """Complex 9-field model with enums and optional fields."""

    id: int
    title: str
    description: str
    status: Status
    priority: Priority
    score: float
    tags: str | None = None
    metadata: str | None = None
    created_at: datetime


# =============================================================================
# FOREIGN KEY MODELS
# =============================================================================


class Author(BaseModel):
    """Author model for relationship benchmarks."""

    id: int
    name: str
    email: str
    bio: str | None = None
    created_at: datetime


class Book(BaseModel):
    """Book model with foreign key to Author."""

    id: int
    title: str
    description: str
    author_id: int  # Foreign key to Author
    isbn: str
    pages: int
    published_at: datetime
    created_at: datetime


class Review(BaseModel):
    """Review model with foreign keys to both Book and Author."""

    id: int
    book_id: int  # Foreign key to Book
    author_id: int  # Foreign key to Author (reviewer)
    rating: int
    comment: str
    created_at: datetime


# =============================================================================
# LARGE FIELD COUNT MODELS
# =============================================================================


class LargeModel(BaseModel):
    """Model with 20 fields for field extraction benchmarks."""

    id: int
    field_01: str
    field_02: str
    field_03: str
    field_04: int
    field_05: int
    field_06: float
    field_07: float
    field_08: bool
    field_09: bool
    field_10: datetime
    field_11: datetime
    field_12: str | None = None
    field_13: str | None = None
    field_14: int | None = None
    field_15: int | None = None
    field_16: float | None = None
    field_17: float | None = None
    field_18: bool | None = None
    field_19: str | None = None
    field_20: str | None = None


# =============================================================================
# CIRCULAR DEPENDENCY MODELS
# =============================================================================


class Category(BaseModel):
    """Category with self-referential foreign key."""

    id: int
    name: str
    parent_id: int | None = None  # Self-referential FK
    description: str


class Product(BaseModel):
    """Product with FK to Category."""

    id: int
    name: str
    category_id: int  # FK to Category
    price: float
    stock: int
