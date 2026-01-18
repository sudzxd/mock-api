"""Repository protocols - segregated data access interfaces.

Following Interface Segregation Principle (SOLID):
- IReadRepository: Read-only operations
- IWriteRepository: Write operations (create, update, delete)
- IBulkRepository: Bulk operations

All repositories are generic and thread-safe.
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Any, Generic, Protocol, TypeVar

# Project/local
from ..value_objects.query import FilterSpec, QueryResult, SortSpec

# =============================================================================
# CONSTANTS
# =============================================================================
# Covariant type variable for read/write repositories (output only)
# Repositories only return T, never accept it as input (they accept raw dicts)
T_co = TypeVar("T_co", covariant=True)

# Invariant type variable for bulk operations (used in both input and output)
T = TypeVar("T")


# =============================================================================
# PROTOCOLS (REPOSITORIES)
# =============================================================================
class IReadRepository(Protocol, Generic[T_co]):
    """Read-only repository protocol.

    Thread-safe read operations with filtering, sorting, and pagination.
    Implementations must support concurrent reads.
    """

    def get(
        self,
        model_name: str,
        entity_id: int,
    ) -> T_co:
        """Get single entity by ID.

        Args:
            model_name: Model/collection name
            entity_id: Entity primary key

        Returns:
            Entity data

        Raises:
            ModelNotFoundError: If model_name doesn't exist
            EntityNotFoundError: If entity doesn't exist
        """
        ...

    def list(
        self,
        model_name: str,
        *,
        page: int = 1,
        page_size: int = 20,
        filters: list[FilterSpec] | None = None,
        sorts: list[SortSpec] | None = None,
    ) -> QueryResult[T_co]:
        """List entities with filtering, sorting, and pagination.

        Args:
            model_name: Model/collection name
            page: Page number (1-indexed)
            page_size: Items per page
            filters: List of filter specifications
            sorts: List of sort specifications

        Returns:
            QueryResult with paginated items and metadata

        Raises:
            ModelNotFoundError: If model_name doesn't exist
            ValidationError: If filters/sorts are invalid
        """
        ...

    def count(
        self,
        model_name: str,
        *,
        filters: list[FilterSpec] | None = None,
    ) -> int:
        """Count entities matching filters.

        Args:
            model_name: Model/collection name
            filters: List of filter specifications

        Returns:
            Count of matching entities

        Raises:
            ModelNotFoundError: If model_name doesn't exist
            ValidationError: If filters are invalid
        """
        ...

    def exists(
        self,
        model_name: str,
        entity_id: int,
    ) -> bool:
        """Check if entity exists.

        Args:
            model_name: Model/collection name
            entity_id: Entity primary key

        Returns:
            True if entity exists

        Raises:
            ModelNotFoundError: If model_name doesn't exist
        """
        ...


class IWriteRepository(Protocol, Generic[T_co]):
    """Write-only repository protocol.

    Thread-safe write operations with validation.
    Implementations must validate data before writing.
    """

    def create(
        self,
        model_name: str,
        data: dict[str, Any],
    ) -> T_co:
        """Create new entity.

        Args:
            model_name: Model/collection name
            data: Entity data (without ID)

        Returns:
            Created entity with assigned ID

        Raises:
            ModelNotFoundError: If model_name doesn't exist
            ValidationError: If data is invalid
            DuplicateKeyError: If unique constraint violated
        """
        ...

    def update(
        self,
        model_name: str,
        entity_id: int,
        data: dict[str, Any],
    ) -> T_co:
        """Update existing entity.

        Args:
            model_name: Model/collection name
            entity_id: Entity primary key
            data: Updated fields (partial update supported)

        Returns:
            Updated entity

        Raises:
            ModelNotFoundError: If model_name doesn't exist
            EntityNotFoundError: If entity doesn't exist
            ValidationError: If data is invalid
        """
        ...

    def delete(
        self,
        model_name: str,
        entity_id: int,
    ) -> bool:
        """Delete entity by ID.

        Args:
            model_name: Model/collection name
            entity_id: Entity primary key

        Returns:
            True if deleted, False if not found

        Raises:
            ModelNotFoundError: If model_name doesn't exist
        """
        ...


class IBulkRepository(Protocol, Generic[T]):
    """Bulk operations repository protocol.

    Thread-safe bulk operations with transaction semantics.
    Implementations should support all-or-nothing or partial success modes.

    Note: Uses invariant T (not covariant) because bulk operations
    may need to process the returned items.
    """

    def bulk_create(
        self,
        model_name: str,
        data_list: list[dict[str, Any]],
        *,
        allow_partial: bool = False,
    ) -> list[T]:
        """Bulk create entities.

        Args:
            model_name: Model/collection name
            data_list: List of entity data dicts
            allow_partial: If False, all-or-nothing. If True, continue on errors.

        Returns:
            List of created entities

        Raises:
            ModelNotFoundError: If model_name doesn't exist
            ValidationError: If any data is invalid (and not allow_partial)
            BulkOperationError: If operation fails (contains partial results)
        """
        ...

    def bulk_update(
        self,
        model_name: str,
        data_list: list[dict[str, Any]],
        *,
        allow_partial: bool = False,
    ) -> list[T]:
        """Bulk update entities.

        Each dict must contain 'id' field plus fields to update.

        Args:
            model_name: Model/collection name
            data_list: List of update dicts (must include 'id')
            allow_partial: If False, all-or-nothing. If True, continue on errors.

        Returns:
            List of updated entities

        Raises:
            ModelNotFoundError: If model_name doesn't exist
            ValidationError: If any data is invalid (and not allow_partial)
            BulkOperationError: If operation fails (contains partial results)
        """
        ...

    def bulk_delete(
        self,
        model_name: str,
        entity_ids: list[int],
        *,
        allow_partial: bool = False,
    ) -> int:
        """Bulk delete entities.

        Args:
            model_name: Model/collection name
            entity_ids: List of entity IDs to delete
            allow_partial: If False, all-or-nothing. If True, continue on errors.

        Returns:
            Count of deleted entities

        Raises:
            ModelNotFoundError: If model_name doesn't exist
            BulkOperationError: If operation fails (contains partial count)
        """
        ...
