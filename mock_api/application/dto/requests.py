"""Request DTOs."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from dataclasses import dataclass
from typing import Any


# =============================================================================
# REQUEST DTOS
# =============================================================================
@dataclass(frozen=True)
class CreateEntityRequest:
    """Request to create entity."""

    model_name: str
    data: dict[str, Any]


@dataclass(frozen=True)
class UpdateEntityRequest:
    """Request to update entity."""

    model_name: str
    entity_id: int
    data: dict[str, Any]


@dataclass(frozen=True)
class GetEntityRequest:
    """Request to get single entity by ID."""

    model_name: str
    entity_id: int


@dataclass(frozen=True)
class DeleteEntityRequest:
    """Request to delete entity by ID."""

    model_name: str
    entity_id: int


@dataclass(frozen=True)
class ListEntitiesRequest:
    """Request to list entities with filters/sorts/pagination."""

    model_name: str
    page: int = 1
    page_size: int = 20
    query_params: dict[str, Any] | None = None


@dataclass(frozen=True)
class BulkCreateEntitiesRequest:
    """Request to bulk create multiple entities."""

    model_name: str
    data_list: list[dict[str, Any]]


@dataclass(frozen=True)
class BulkUpdateEntitiesRequest:
    """Request to bulk update multiple entities.

    Each item in data_list must contain 'id' field plus fields to update.
    """

    model_name: str
    data_list: list[dict[str, Any]]


@dataclass(frozen=True)
class BulkDeleteEntitiesRequest:
    """Request to bulk delete multiple entities by IDs."""

    model_name: str
    entity_ids: list[int]
