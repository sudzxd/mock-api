"""Blog example models demonstrating relationships and foreign keys.

This example shows how mockapi-server handles related models with
foreign key relationships between User, Post, and Comment.
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
    """Blog user with profile information."""

    id: int
    username: str
    email: str
    bio: str | None = None
    created_at: datetime


class Post(BaseModel):
    """Blog post authored by a user."""

    id: int
    title: str
    content: str
    author_id: int  # Foreign key to User
    published_at: datetime | None = None
    created_at: datetime


class Comment(BaseModel):
    """Comment on a blog post by a user."""

    id: int
    text: str
    post_id: int  # Foreign key to Post
    user_id: int  # Foreign key to User
    created_at: datetime
