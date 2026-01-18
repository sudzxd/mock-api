"""Dependency injection for FastAPI.

Immutable dependency container pattern.
Use cases are created per-request via FastAPI Depends().
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from dataclasses import dataclass
from typing import Any, Protocol

# Project/local
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
from mock_api.domain.repositories.protocols import (
    IBulkRepository,
    IReadRepository,
    IWriteRepository,
)
from mock_api.domain.services.protocols import (
    IFilterService,
    ISortService,
    IValidationService,
)
from mock_api.domain.value_objects.schema import ModelSchema
from mock_api.infrastructure.factories.storage_factory import StorageFactory
from mock_api.infrastructure.services.filter_executor import FilterExecutor
from mock_api.infrastructure.services.filter_service import FilterService
from mock_api.infrastructure.services.sort_executor import SortExecutor
from mock_api.infrastructure.services.sort_service import SortService
from mock_api.infrastructure.services.validation_service import ValidationService


# =============================================================================
# PROTOCOLS
# =============================================================================
class IRepository(
    IReadRepository[dict[str, Any]],
    IWriteRepository[dict[str, Any]],
    IBulkRepository[dict[str, Any]],
    Protocol,
):
    """Combined repository protocol.

    Provides read, write, and bulk operations.
    Used for dependency injection to avoid intersection types.
    """


# =============================================================================
# DEPENDENCY CONTAINER
# =============================================================================
@dataclass(frozen=True)
class DependencyContainer:
    """Immutable dependency container.

    Thread-safe container holding all application dependencies.
    Initialized once at startup and never modified.
    """

    repository: IRepository
    filter_service: IFilterService
    sort_service: ISortService
    validation_service: IValidationService
    schemas: dict[str, ModelSchema]


# =============================================================================
# GLOBAL CONTAINER
# =============================================================================
# Module-level singleton (immutable once initialized)
_container: DependencyContainer | None = None


# =============================================================================
# INITIALIZATION
# =============================================================================
def initialize_dependencies(
    schemas: dict[str, ModelSchema], storage_url: str = "memory://"
) -> None:
    """Initialize dependency container.

    Called once at application startup by CLI.
    Creates immutable container with all dependencies.

    Args:
        schemas: Parsed model schemas
        storage_url: Storage backend URL (default: memory://)

    Raises:
        RuntimeError: If dependencies already initialized
    """
    global _container

    if _container is not None:
        raise RuntimeError(
            "Dependencies already initialized. "
            "Call reset_dependencies() first if re-initialization needed."
        )

    # Create services
    filter_service = FilterService()
    sort_service = SortService()
    validation_service = ValidationService()

    # Create executors
    filter_executor = FilterExecutor()
    sort_executor = SortExecutor()

    # Create repository via factory (pass all dependencies)
    repository = StorageFactory.create(
        storage_url, schemas, validation_service, filter_executor, sort_executor
    )

    # Create immutable container
    _container = DependencyContainer(
        repository=repository,
        filter_service=filter_service,
        sort_service=sort_service,
        validation_service=validation_service,
        schemas=schemas,
    )


def reset_dependencies() -> None:
    """Reset dependencies (for testing).

    Clears the global container, allowing re-initialization.
    Should only be used in test fixtures.
    """
    global _container
    _container = None


def get_container() -> DependencyContainer:
    """Get dependency container.

    Returns:
        Immutable dependency container

    Raises:
        RuntimeError: If dependencies not initialized
    """
    if _container is None:
        raise RuntimeError(
            "Dependencies not initialized. Call initialize_dependencies() first."
        )
    return _container


# =============================================================================
# DEPENDENCY PROVIDERS
# =============================================================================
def get_create_entity_use_case() -> CreateEntityUseCase:
    """FastAPI dependency for CreateEntityUseCase.

    Returns:
        CreateEntityUseCase instance with injected dependencies
    """
    container = get_container()
    return CreateEntityUseCase(container.repository, container.schemas)


def get_get_entity_use_case() -> GetEntityUseCase:
    """FastAPI dependency for GetEntityUseCase.

    Returns:
        GetEntityUseCase instance with injected dependencies
    """
    container = get_container()
    return GetEntityUseCase(container.repository, container.schemas)


def get_update_entity_use_case() -> UpdateEntityUseCase:
    """FastAPI dependency for UpdateEntityUseCase.

    Returns:
        UpdateEntityUseCase instance with injected dependencies
    """
    container = get_container()
    return UpdateEntityUseCase(container.repository, container.schemas)


def get_delete_entity_use_case() -> DeleteEntityUseCase:
    """FastAPI dependency for DeleteEntityUseCase.

    Returns:
        DeleteEntityUseCase instance with injected dependencies
    """
    container = get_container()
    return DeleteEntityUseCase(container.repository, container.schemas)


def get_list_entities_use_case() -> ListEntitiesUseCase:
    """FastAPI dependency for ListEntitiesUseCase.

    Returns:
        ListEntitiesUseCase instance with injected dependencies
    """
    container = get_container()
    return ListEntitiesUseCase(
        container.repository,
        container.filter_service,
        container.sort_service,
        container.schemas,
    )


def get_bulk_create_entities_use_case() -> BulkCreateEntitiesUseCase:
    """FastAPI dependency for BulkCreateEntitiesUseCase.

    Returns:
        BulkCreateEntitiesUseCase instance with injected dependencies
    """
    container = get_container()
    return BulkCreateEntitiesUseCase(container.repository, container.schemas)


def get_bulk_update_entities_use_case() -> BulkUpdateEntitiesUseCase:
    """FastAPI dependency for BulkUpdateEntitiesUseCase.

    Returns:
        BulkUpdateEntitiesUseCase instance with injected dependencies
    """
    container = get_container()
    return BulkUpdateEntitiesUseCase(container.repository, container.schemas)


def get_bulk_delete_entities_use_case() -> BulkDeleteEntitiesUseCase:
    """FastAPI dependency for BulkDeleteEntitiesUseCase.

    Returns:
        BulkDeleteEntitiesUseCase instance with injected dependencies
    """
    container = get_container()
    return BulkDeleteEntitiesUseCase(container.repository, container.schemas)
