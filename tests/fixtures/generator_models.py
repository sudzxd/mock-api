"""Test fixtures for generator testing.

Comprehensive models covering all field patterns and edge cases.
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
# ENUMS
# =============================================================================


class Priority(int, Enum):
    """Priority levels."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Status(str, Enum):
    """Status values."""

    ACTIVE = "active"
    INACTIVE = "inactive"


# =============================================================================
# TEST MODELS - Field Patterns
# =============================================================================


class Contact(BaseModel):
    """Model with contact field patterns."""

    id: int
    email: str
    phone: str
    name: str
    username: str
    first_name: str
    last_name: str


class Location(BaseModel):
    """Model with address field patterns."""

    id: int
    address: str
    street: str
    city: str
    state: str
    country: str
    zip: str


class Article(BaseModel):
    """Model with content field patterns."""

    id: int
    title: str
    content: str
    description: str
    url: str
    created_at: datetime
    updated_at: datetime


# =============================================================================
# TEST MODELS - Relationships
# =============================================================================


class Author(BaseModel):
    """Author model for FK testing."""

    id: int
    name: str


class Book(BaseModel):
    """Book with FK to Author."""

    id: int
    title: str
    author_id: int


class Review(BaseModel):
    """Review with FK to Book."""

    id: int
    text: str
    book_id: int


# =============================================================================
# TEST MODELS - Edge Cases
# =============================================================================


class Product(BaseModel):
    """Model with enums and optional fields."""

    id: int
    name: str
    priority: Priority
    status: Status | None = None
    description: str | None = None


class Node(BaseModel):
    """Self-referential model."""

    id: int
    name: str
    parent_id: int | None = None
