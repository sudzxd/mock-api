"""Test fixtures: Pydantic models for testing the parser.

This module provides sample Pydantic models that demonstrate various
schema patterns including foreign keys and relationships.
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
# TEST MODELS
# =============================================================================


class User(BaseModel):
    """Test user model.

    Represents a user entity with basic fields and an optional age.
    Used to test schema parsing and relationship detection.
    """

    id: int
    name: str
    email: str
    age: int | None = None
    created_at: datetime


class Post(BaseModel):
    """Test post model with foreign key to User.

    Demonstrates many-to-one relationship via author_id field.
    Tests semantic FK resolution (author_id → User).
    """

    id: int
    title: str
    content: str
    author_id: int  # Foreign key to User
    published: bool = False


class Comment(BaseModel):
    """Test comment model with multiple foreign keys.

    Demonstrates model with relationships to two different models.
    Tests handling of multiple FKs in a single model.
    """

    id: int
    text: str
    post_id: int  # Foreign key to Post
    user_id: int  # Foreign key to User
