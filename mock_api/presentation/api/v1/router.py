"""Main API router generator."""

from __future__ import annotations

from enum import StrEnum

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Annotated, Any

# Third-party
from fastapi import APIRouter, Depends, Request, Response, status

# Project/local
from mock_api.domain.value_objects.schema import ModelSchema
from mock_api.presentation.api.v1.endpoints.crud import (
    bulk_create_entities_endpoint,
    bulk_delete_entities_endpoint,
    bulk_update_entities_endpoint,
    create_entity_endpoint,
    delete_entity_endpoint,
    get_entity_endpoint,
    list_entities_endpoint,
    update_entity_endpoint,
)
from mock_api.presentation.dependencies.injection import (
    get_bulk_create_entities_use_case,
    get_bulk_delete_entities_use_case,
    get_bulk_update_entities_use_case,
    get_create_entity_use_case,
    get_delete_entity_use_case,
    get_get_entity_use_case,
    get_list_entities_use_case,
    get_update_entity_use_case,
)

# =============================================================================
# CONSTANTS
# =============================================================================


class HTTPMethod(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


# =============================================================================
# ROUTER FACTORY
# =============================================================================
def create_router(
    schemas: dict[str, ModelSchema],
    *,
    prefix: str = "/api/v1",
) -> APIRouter:
    """Create FastAPI router with CRUD endpoints for all models.

    Generates endpoints for each model:
    - GET /{model_name} - List entities
    - GET /{model_name}/{id} - Get entity
    - POST /{model_name} - Create entity
    - POST /{model_name}/bulk - Bulk create entities
    - PUT /{model_name}/{id} - Update entity
    - PUT /{model_name}/bulk - Bulk update entities
    - DELETE /{model_name}/{id} - Delete entity
    - DELETE /{model_name}/bulk - Bulk delete entities

    Args:
        schemas: Model schemas
        prefix: URL prefix

    Returns:
        FastAPI APIRouter with all endpoints
    """
    # Create main router
    router = APIRouter(prefix=prefix, tags=["CRUD"])

    # Register routes for each model
    for model_name, schema in schemas.items():
        create_model_router(router, model_name, schema)

    return router


def create_model_router(
    router: APIRouter,
    model_name: str,
    _schema: ModelSchema,
) -> None:
    """Add CRUD routes for single model to router.

    Args:
        router: FastAPI APIRouter to add routes to
        model_name: Model name
        _schema: Model schema (reserved for future use)
    """

    # Create wrapper functions that bind model_name
    async def list_wrapper(
        request: Request,
        use_case: Annotated[Any, Depends(get_list_entities_use_case)],
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        return await list_entities_endpoint(
            model_name, request, use_case, page, page_size
        )

    async def get_wrapper(
        entity_id: int,
        use_case: Annotated[Any, Depends(get_get_entity_use_case)],
    ) -> dict[str, Any]:
        return await get_entity_endpoint(model_name, entity_id, use_case)

    async def create_wrapper(
        data: dict[str, Any],
        use_case: Annotated[Any, Depends(get_create_entity_use_case)],
    ) -> dict[str, Any]:
        return await create_entity_endpoint(model_name, data, use_case)

    async def bulk_create_wrapper(
        data_list: list[dict[str, Any]],
        use_case: Annotated[Any, Depends(get_bulk_create_entities_use_case)],
    ) -> list[dict[str, Any]]:
        return await bulk_create_entities_endpoint(model_name, data_list, use_case)

    async def update_wrapper(
        entity_id: int,
        data: dict[str, Any],
        use_case: Annotated[Any, Depends(get_update_entity_use_case)],
    ) -> dict[str, Any]:
        return await update_entity_endpoint(model_name, entity_id, data, use_case)

    async def delete_wrapper(
        entity_id: int,
        use_case: Annotated[Any, Depends(get_delete_entity_use_case)],
    ) -> Response:
        return await delete_entity_endpoint(model_name, entity_id, use_case)

    async def bulk_update_wrapper(
        data_list: list[dict[str, Any]],
        use_case: Annotated[Any, Depends(get_bulk_update_entities_use_case)],
    ) -> list[dict[str, Any]]:
        return await bulk_update_entities_endpoint(model_name, data_list, use_case)

    async def bulk_delete_wrapper(
        entity_ids: list[int],
        use_case: Annotated[Any, Depends(get_bulk_delete_entities_use_case)],
    ) -> dict[str, Any]:
        return await bulk_delete_entities_endpoint(model_name, entity_ids, use_case)

    # List entities - GET /{model_name}
    router.add_api_route(
        f"/{model_name}",
        list_wrapper,
        methods=[HTTPMethod.GET],
        response_model=None,
        summary=f"List {model_name} entities",
        description=(
            f"List {model_name} entities with filtering, sorting, and pagination"
        ),
    )

    # Create entity - POST /{model_name}
    router.add_api_route(
        f"/{model_name}",
        create_wrapper,
        methods=[HTTPMethod.POST],
        response_model=None,
        status_code=status.HTTP_201_CREATED,
        summary=f"Create {model_name}",
        description=f"Create a new {model_name} entity",
    )

    # Bulk create entities - POST /{model_name}/bulk
    router.add_api_route(
        f"/{model_name}/bulk",
        bulk_create_wrapper,
        methods=[HTTPMethod.POST],
        response_model=None,
        status_code=status.HTTP_201_CREATED,
        summary=f"Bulk create {model_name} entities",
        description=f"Create multiple {model_name} entities in a single operation",
    )

    # Bulk update entities - PUT /{model_name}/bulk
    router.add_api_route(
        f"/{model_name}/bulk",
        bulk_update_wrapper,
        methods=[HTTPMethod.PUT],
        response_model=None,
        status_code=status.HTTP_200_OK,
        summary=f"Bulk update {model_name} entities",
        description=(
            f"Update multiple {model_name} entities. Each item must include 'id'."
        ),
    )

    # Bulk delete entities - DELETE /{model_name}/bulk
    router.add_api_route(
        f"/{model_name}/bulk",
        bulk_delete_wrapper,
        methods=[HTTPMethod.DELETE],
        response_model=None,
        status_code=status.HTTP_200_OK,
        summary=f"Bulk delete {model_name} entities",
        description=f"Delete multiple {model_name} entities by IDs.",
    )

    # Get entity - GET /{model_name}/{{id}}
    router.add_api_route(
        f"/{model_name}/{{entity_id}}",
        get_wrapper,
        methods=[HTTPMethod.GET],
        response_model=None,
        summary=f"Get {model_name} by ID",
        description=f"Retrieve a single {model_name} entity by ID",
    )

    # Update entity - PUT /{model_name}/{{id}}
    router.add_api_route(
        f"/{model_name}/{{entity_id}}",
        update_wrapper,
        methods=[HTTPMethod.PUT],
        response_model=None,
        summary=f"Update {model_name}",
        description=(
            f"Update an existing {model_name} entity (supports partial updates)"
        ),
    )

    # Delete entity - DELETE /{model_name}/{{id}}
    router.add_api_route(
        f"/{model_name}/{{entity_id}}",
        delete_wrapper,
        methods=[HTTPMethod.DELETE],
        response_model=None,
        status_code=status.HTTP_204_NO_CONTENT,
        summary=f"Delete {model_name}",
        description=f"Delete a {model_name} entity by ID",
    )
