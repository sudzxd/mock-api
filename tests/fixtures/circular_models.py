"""Test fixtures for circular dependencies."""

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
    """User with manager relationship (self-referential)."""

    id: int
    name: str
    manager_id: int | None = None  # Self-referential FK


class Department(BaseModel):
    """Department with head relationship."""

    id: int
    name: str
    head_id: int  # FK to User


class Employee(BaseModel):
    """Employee creating a cycle: Employee -> Department -> User -> Employee."""

    id: int
    name: str
    department_id: int  # FK to Department
    user_id: int  # FK to User


class Project(BaseModel):
    """Project with lead."""

    id: int
    name: str
    lead_id: int  # FK to Employee


class Task(BaseModel):
    """Task creating another cycle."""

    id: int
    title: str
    project_id: int  # FK to Project
    assignee_id: int  # FK to Employee
