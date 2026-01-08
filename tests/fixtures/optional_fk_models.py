"""Test fixtures: Optional foreign keys.

This module tests parser behavior with optional foreign key fields
to ensure they're still detected as foreign keys even when nullable.
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Third-party
from pydantic import BaseModel

# =============================================================================
# TEST MODELS
# =============================================================================


class User(BaseModel):
    """Test user model."""

    id: int
    name: str


class Task(BaseModel):
    """Task model with optional foreign key.

    The assignee_id field is optional (can be None) but should
    still be detected as a foreign key to User.
    """

    id: int
    title: str
    assignee_id: int | None = None  # Optional FK - task may be unassigned
