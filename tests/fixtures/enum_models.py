"""Test fixtures: Enum field handling.

This module tests parser behavior with Enum fields to ensure
they are properly detected and their values are extracted.
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from enum import Enum

# Third-party
from pydantic import BaseModel

# =============================================================================
# ENUMS
# =============================================================================


class Status(str, Enum):
    """User status enum."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class Priority(int, Enum):
    """Task priority enum."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


# =============================================================================
# TEST MODELS
# =============================================================================


class User(BaseModel):
    """User model with enum status field."""

    id: int
    name: str
    status: Status
    email: str


class Task(BaseModel):
    """Task model with enum priority field and optional enum status."""

    id: int
    title: str
    priority: Priority
    status: Status | None = None
    user_id: int  # Foreign key to User
