"""Test fixtures: Pydantic model inheritance.

This module tests parser behavior with model inheritance,
ensuring that inherited fields are properly captured.
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


class TimestampedModel(BaseModel):
    """Base model with timestamp fields.

    This model demonstrates inheritance - subclasses should
    inherit created_at and updated_at fields.
    """

    created_at: datetime
    updated_at: datetime | None = None


class Article(TimestampedModel):
    """Article model inheriting from TimestampedModel.

    Should have id, title, content plus inherited created_at/updated_at.
    """

    id: int
    title: str
    content: str
    author_id: int  # Foreign key to User
