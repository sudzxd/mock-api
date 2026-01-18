"""CRUD endpoint handlers.

Note: Exception handling is centralized in middleware/exception_handlers.py.
Endpoints delegate to use cases and let exceptions propagate naturally.
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Annotated, Any

# Third-party
from fastapi import Depends, Request, Response, status

# Project/local
from mock_api.application.dto.requests import (
    BulkCreateEntitiesRequest,
    BulkDeleteEntitiesRequest,
    BulkUpdateEntitiesRequest,
    CreateEntityRequest,
    DeleteEntityRequest,
    GetEntityRequest,
    ListEntitiesRequest,
    UpdateEntityRequest,
)
from mock_api.application.use_cases import (
    BulkCreateEntitiesUseCase,
    BulkDeleteEntitiesUseCase,
    BulkUpdateEntitiesUseCase,
    CreateEntityUseCase,
    DeleteEntityUseCase,
    GetEntityUseCase,
    ListEntitiesUseCase,
    UpdateEntityUseCase,
)
from mock_api.core.exceptions import EntityNotFoundError
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
# CRUD ENDPOINTS
# =============================================================================
async def create_entity_endpoint(
    model_name: str,
    data: dict[str, Any],
    use_case: Annotated[CreateEntityUseCase, Depends(get_create_entity_use_case)],
) -> dict[str, Any]:
    """Create new entity.

    Args:
        model_name: Model name from path
        data: Entity data from request body
        use_case: Injected CreateEntityUseCase

    Returns:
        EntityResponse with created entity (201)

    Raises:
        ModelNotFoundError: If model doesn't exist (handled by middleware → 404)
        ValidationError: If data invalid (handled by middleware → 422)
    """
    # Create request DTO
    request = CreateEntityRequest(model_name=model_name, data=data)

    # Execute use case (exceptions handled by middleware)
    response = use_case.execute(request)

    # Return response (FastAPI will set 201 status in router)
    return response.data


async def bulk_create_entities_endpoint(
    model_name: str,
    data_list: list[dict[str, Any]],
    use_case: Annotated[
        BulkCreateEntitiesUseCase, Depends(get_bulk_create_entities_use_case)
    ],
) -> list[dict[str, Any]]:
    """Bulk create multiple entities.

    Args:
        model_name: Model name from path
        data_list: List of entity data from request body
        use_case: Injected BulkCreateEntitiesUseCase

    Returns:
        List of created entities (201)

    Raises:
        ModelNotFoundError: If model doesn't exist (handled by middleware → 404)
        ValidationError: If data is invalid (handled by middleware → 422)
        BulkOperationError: If bulk operation fails (handled by middleware → 400)
    """
    # Create request DTO
    request = BulkCreateEntitiesRequest(model_name=model_name, data_list=data_list)

    # Execute use case (exceptions handled by middleware)
    response = use_case.execute(request)

    # Return response (FastAPI will set 201 status in router)
    return response.items


async def get_entity_endpoint(
    model_name: str,
    entity_id: int,
    use_case: Annotated[GetEntityUseCase, Depends(get_get_entity_use_case)],
) -> dict[str, Any]:
    """Get single entity by ID.

    Args:
        model_name: Model name from path
        entity_id: Entity ID from path
        use_case: Injected GetEntityUseCase

    Returns:
        EntityResponse

    Raises:
        ModelNotFoundError: If model doesn't exist (handled by middleware → 404)
        EntityNotFoundError: If entity doesn't exist (handled by middleware → 404)
    """
    # Create request DTO
    request = GetEntityRequest(model_name=model_name, entity_id=entity_id)

    # Execute use case (exceptions handled by middleware)
    response = use_case.execute(request)

    # Return response
    return response.data


async def update_entity_endpoint(
    model_name: str,
    entity_id: int,
    data: dict[str, Any],
    use_case: Annotated[UpdateEntityUseCase, Depends(get_update_entity_use_case)],
) -> dict[str, Any]:
    """Update existing entity.

    Args:
        model_name: Model name from path
        entity_id: Entity ID from path
        data: Updated fields from request body
        use_case: Injected UpdateEntityUseCase

    Returns:
        EntityResponse with updated entity

    Raises:
        ModelNotFoundError: If model doesn't exist (handled by middleware → 404)
        EntityNotFoundError: If entity doesn't exist (handled by middleware → 404)
        ValidationError: If data invalid (handled by middleware → 422)
    """
    # Create request DTO
    request = UpdateEntityRequest(model_name=model_name, entity_id=entity_id, data=data)

    # Execute use case (exceptions handled by middleware)
    response = use_case.execute(request)

    # Return responses
    return response.data


async def delete_entity_endpoint(
    model_name: str,
    entity_id: int,
    use_case: Annotated[DeleteEntityUseCase, Depends(get_delete_entity_use_case)],
) -> Response:
    """Delete entity.

    Args:
        model_name: Model name from path
        entity_id: Entity ID from path
        use_case: Injected DeleteEntityUseCase

    Returns:
        204 No Content on success

    Raises:
        ModelNotFoundError: If model doesn't exist (handled by middleware → 404)
        EntityNotFoundError: If entity doesn't exist (handled by middleware → 404)
    """
    # Create request DTO
    request = DeleteEntityRequest(model_name=model_name, entity_id=entity_id)

    # Execute use case (exceptions handled by middleware)
    deleted = use_case.execute(request)

    # Raise EntityNotFoundError if not deleted (caught by middleware → 404)
    if not deleted:
        raise EntityNotFoundError(
            model_name=model_name,
            entity_id=entity_id,
        )

    # Return 204 No Content
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def list_entities_endpoint(
    model_name: str,
    request: Request,
    use_case: Annotated[ListEntitiesUseCase, Depends(get_list_entities_use_case)],
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """List entities with filtering, sorting, pagination.

    Query parameters:
    - page: Page number (default 1)
    - page_size: Items per page (default 20)
    - sort: Sort specification (e.g., 'name,-age')
    - Any field filters (e.g., name=John, age__gte=18)

    Args:
        model_name: Model name from path
        request: FastAPI Request to access query params
        use_case: Injected ListEntitiesUseCase
        page: Page number
        page_size: Items per page

    Returns:
        ListEntitiesResponse with paginated results

    Raises:
        ModelNotFoundError: If model doesn't exist (handled by middleware → 404)
        ValidationError: If filters/sorts invalid (handled by middleware → 422)
    """
    # Get all query parameters
    query_params = dict(request.query_params)

    # Create request DTO
    list_request = ListEntitiesRequest(
        model_name=model_name,
        page=page,
        page_size=page_size,
        query_params=query_params if query_params else None,
    )

    # Execute use case (exceptions handled by middleware)
    response = use_case.execute(list_request)

    # Return response
    return {
        "items": response.items,
        "total": response.total,
        "page": response.page,
        "page_size": response.page_size,
        "total_pages": response.total_pages,
    }


async def bulk_update_entities_endpoint(
    model_name: str,
    data_list: list[dict[str, Any]],
    use_case: Annotated[
        BulkUpdateEntitiesUseCase, Depends(get_bulk_update_entities_use_case)
    ],
) -> list[dict[str, Any]]:
    """Bulk update multiple entities.

    Each item must include 'id' field.

    Args:
        model_name: Model name from path
        data_list: List of entity data (with 'id') from request body
        use_case: Injected BulkUpdateEntitiesUseCase

    Returns:
        List of updated entities (200)

    Raises:
        ModelNotFoundError: If model doesn't exist (handled by middleware → 404)
        EntityNotFoundError: If entity doesn't exist (handled by middleware → 404)
        ValidationError: If data is invalid (handled by middleware → 422)
        BulkOperationError: If bulk operation fails (handled by middleware → 400)
    """
    # Create request DTO
    request = BulkUpdateEntitiesRequest(model_name=model_name, data_list=data_list)

    # Execute use case (exceptions handled by middleware)
    response = use_case.execute(request)

    # Return response
    return response.items


async def bulk_delete_entities_endpoint(
    model_name: str,
    entity_ids: list[int],
    use_case: Annotated[
        BulkDeleteEntitiesUseCase, Depends(get_bulk_delete_entities_use_case)
    ],
) -> dict[str, Any]:
    """Bulk delete multiple entities by IDs.

    Args:
        model_name: Model name from path
        entity_ids: List of entity IDs from request body
        use_case: Injected BulkDeleteEntitiesUseCase

    Returns:
        Dict with model_name and count (200)

    Raises:
        ModelNotFoundError: If model doesn't exist (handled by middleware → 404)
        EntityNotFoundError: If entity doesn't exist (handled by middleware → 404)
        BulkOperationError: If bulk operation fails (handled by middleware → 400)
    """
    # Create request DTO
    request = BulkDeleteEntitiesRequest(model_name=model_name, entity_ids=entity_ids)

    # Execute use case (exceptions handled by middleware)
    response = use_case.execute(request)

    # Return response
    return {"model_name": response.model_name, "count": response.count}
