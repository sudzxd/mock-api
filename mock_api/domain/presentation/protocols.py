"""Presentation layer protocols - API router generation."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Any, Protocol


# =============================================================================
# PROTOCOLS (PRESENTATION)
# =============================================================================
class IRouterGenerator(Protocol):
    """Generate FastAPI routers for models.

    Creates CRUD endpoints dynamically based on parsed schemas.
    """

    def generate_router(
        self,
        model_name: str,
        *,
        prefix: str = "/api/v1",
        tags: list[str] | None = None,
    ) -> Any:  # FastAPI APIRouter
        """Generate FastAPI router for model.

        Creates endpoints:
        - GET /{model_name} - List entities (with filtering, sorting, pagination)
        - GET /{model_name}/{id} - Get single entity
        - POST /{model_name} - Create entity
        - PUT /{model_name}/{id} - Update entity
        - DELETE /{model_name}/{id} - Delete entity
        - POST /{model_name}/bulk - Bulk create
        - PUT /{model_name}/bulk - Bulk update
        - DELETE /{model_name}/bulk - Bulk delete

        Args:
            model_name: Model to generate routes for
            prefix: URL prefix for routes
            tags: OpenAPI tags for documentation

        Returns:
            FastAPI APIRouter instance

        Raises:
            ModelNotFoundError: If model doesn't exist
        """
        ...

    def generate_all_routers(
        self,
        *,
        prefix: str = "/api/v1",
    ) -> list[Any]:  # list[FastAPI APIRouter]
        """Generate routers for all models.

        Args:
            prefix: URL prefix for routes

        Returns:
            List of FastAPI APIRouter instances
        """
        ...
