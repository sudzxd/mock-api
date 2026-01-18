"""Response DTOs."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from dataclasses import dataclass
from typing import Any


# =============================================================================
# RESPONSE DTOS
# =============================================================================
@dataclass(frozen=True)
class EntityResponse:
    """Response containing single entity."""

    model_name: str
    data: dict[str, Any]


@dataclass(frozen=True)
class ListEntitiesResponse:
    """Response containing paginated list of entities."""

    model_name: str
    items: list[dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int


@dataclass(frozen=True)
class BulkCreateEntitiesResponse:
    """Response containing bulk created entities."""

    model_name: str
    items: list[dict[str, Any]]
    count: int


@dataclass(frozen=True)
class BulkUpdateEntitiesResponse:
    """Response containing bulk updated entities."""

    model_name: str
    items: list[dict[str, Any]]
    count: int


@dataclass(frozen=True)
class BulkDeleteEntitiesResponse:
    """Response containing bulk delete count."""

    model_name: str
    count: int
