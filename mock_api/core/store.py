"""Data store facade delegating to repository implementation.

This module provides the DataStore facade that delegates all operations to
a Repository implementation (default: InMemoryRepository).

The facade maintains backward compatibility while enabling a layered architecture
that supports future storage backends via dependency injection.

Architecture:
- DataStore (Facade) → IRepository protocol → Concrete repository
- Repository handles both CRUD and querying
- Query optimization is backend-specific (in-memory vs SQL)

TODO: Future storage backends (issues #48-51):
- JSONRepository for file-based storage (issue #48)
- SQLiteRepository for SQL storage (issue #49)
- PostgreSQLRepository for production use (issue #50)
- RedisRepository for caching (issue #51)

TODO: Future architectural improvements (Phase 3+):
- Add service layer between presentation and data access
- Extract business logic into domain services
- Add Unit of Work pattern for transaction management
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from collections.abc import Callable
from typing import Any

# Project/local
from ..implementations.storage import InMemoryRepository
from ..utils.logger import get_logger
from .protocols import IDataStore
from .types import FilterSpec, QueryResult, SortSpec

# =============================================================================
# TYPES & CONSTANTS
# =============================================================================
logger = get_logger(__name__)

# Type alias for filter functions
FilterFunc = Callable[[dict[str, Any]], bool]

# =============================================================================
# PUBLIC API
# =============================================================================


class DataStore(IDataStore):
    """Facade delegating to repository implementation.

    Implements IDataStore protocol for backward compatibility and dependency injection.

    This facade delegates all operations to a repository implementation.
    The repository handles both CRUD and querying, with query optimization
    being backend-specific:
    - In-memory: Load data, then filter/sort in Python
    - SQL: Generate WHERE/ORDER BY clauses for database-level optimization

    The layered architecture enables future improvements:
    - Swap storage backends (JSON, SQLite, PostgreSQL, Redis)
    - Add caching layer
    - Implement Unit of Work for transactions
    - Extract business logic to service layer

    Example:
        >>> store = DataStore()
        >>> store.create("User", {"id": 1, "name": "Alice"})
        {'id': 1, 'name': 'Alice'}
        >>> result = store.list("User", page=1, page_size=10)
        >>> len(result.items)
        1
    """

    def __init__(self, repository: InMemoryRepository | None = None) -> None:
        """Initialize data store with repository implementation.

        Args:
            repository: Repository implementation (default: InMemoryRepository).

        Note:
            Dependency injection allows swapping implementations for:
            - Testing with mock repositories
            - Using different storage backends (JSON, SQLite, PostgreSQL)
            - Custom query optimization strategies
        """
        self._repository = repository or InMemoryRepository()
        logger.debug(f"Initialized DataStore with {type(self._repository).__name__}")

    # =========================================================================
    # CRUD OPERATIONS (delegate to repository)
    # =========================================================================

    def load(self, data: dict[str, list[dict[str, Any]]]) -> None:
        """Load bulk data into the store.

        Delegates to repository for storage.

        Args:
            data: Dictionary mapping model names to lists of instances.
        """
        self._repository.load(data)

    def create(
        self, model_name: str, data: dict[str, Any], auto_id: bool = True
    ) -> dict[str, Any]:
        """Create a new instance.

        Delegates to repository for storage.

        Args:
            model_name: Name of the model.
            data: Dictionary of field values.
            auto_id: If True, automatically assign ID if not provided.

        Returns:
            The created instance with ID assigned.
        """
        return self._repository.create(model_name, data, auto_id)

    def read(self, model_name: str, instance_id: int) -> dict[str, Any] | None:
        """Read a single instance by ID.

        Delegates to repository for retrieval.

        Args:
            model_name: Name of the model.
            instance_id: ID of the instance.

        Returns:
            The instance or None if not found.
        """
        return self._repository.read(model_name, instance_id)

    def update(
        self, model_name: str, instance_id: int, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing instance.

        Delegates to repository for storage.

        Args:
            model_name: Name of the model.
            instance_id: ID of the instance to update.
            data: Dictionary of field values to update.

        Returns:
            The updated instance.
        """
        return self._repository.update(model_name, instance_id, data)

    def delete(self, model_name: str, instance_id: int) -> bool:
        """Delete an instance by ID.

        Delegates to repository for deletion.

        Args:
            model_name: Name of the model.
            instance_id: ID of the instance to delete.

        Returns:
            True if deleted, False if not found.
        """
        return self._repository.delete(model_name, instance_id)

    # =========================================================================
    # BULK OPERATIONS (delegate to repository)
    # =========================================================================

    def bulk_create(
        self,
        model_name: str,
        data_list: list[dict[str, Any]],
        allow_partial: bool = False,
        max_batch_size: int | None = None,
    ) -> dict[str, Any]:
        """Create multiple instances atomically.

        Delegates to repository for bulk storage.

        Args:
            model_name: Name of the model.
            data_list: List of instances to create.
            allow_partial: If True, continue on errors; if False, rollback.
            max_batch_size: Maximum batch size allowed.

        Returns:
            Dict with 'created' count and optional 'errors'.
        """
        return self._repository.bulk_create(
            model_name, data_list, allow_partial, max_batch_size
        )

    def bulk_update(
        self,
        model_name: str,
        data_list: list[dict[str, Any]],
        allow_partial: bool = False,
        max_batch_size: int | None = None,
    ) -> dict[str, Any]:
        """Update multiple instances atomically.

        Delegates to repository for bulk updates.

        Args:
            model_name: Name of the model.
            data_list: List of instances to update (must include 'id').
            allow_partial: If True, continue on errors; if False, rollback.
            max_batch_size: Maximum batch size allowed.

        Returns:
            Dict with 'updated' count and optional 'errors'.
        """
        return self._repository.bulk_update(
            model_name, data_list, allow_partial, max_batch_size
        )

    def bulk_delete(
        self,
        model_name: str,
        id_list: list[int],
        allow_partial: bool = False,
        max_batch_size: int | None = None,
    ) -> dict[str, Any]:
        """Delete multiple instances atomically.

        Delegates to repository for bulk deletion.

        Args:
            model_name: Name of the model.
            id_list: List of instance IDs to delete.
            allow_partial: If True, continue on errors; if False, rollback.
            max_batch_size: Maximum batch size allowed.

        Returns:
            Dict with 'deleted' count and optional 'errors'.
        """
        return self._repository.bulk_delete(
            model_name, id_list, allow_partial, max_batch_size
        )

    # =========================================================================
    # QUERY OPERATIONS (delegate to query executor)
    # =========================================================================

    def list(
        self,
        model_name: str,
        page: int | None = None,
        page_size: int | None = None,
        offset: int | None = None,
        limit: int | None = None,
        filters: list[FilterSpec] | None = None,
        sort_by: list[SortSpec] | None = None,
        filter_func: FilterFunc | None = None,
    ) -> QueryResult:
        """List instances with filtering, sorting, and pagination.

        Delegates to repository for query execution.

        Args:
            model_name: Name of the model.
            page: Page number (1-indexed).
            page_size: Items per page.
            offset: Number of items to skip.
            limit: Maximum number of items to return.
            filters: Optional list of filter specifications.
            sort_by: Optional list of sort specifications.
            filter_func: Optional custom filter function (legacy support).

        Returns:
            QueryResult with filtered, sorted, paginated items and metadata.

        Note:
            Repository implementation determines query optimization strategy:
            - In-memory: Load all, then filter/sort in Python
            - SQL: Generate WHERE/ORDER BY clauses for database optimization
        """
        return self._repository.list(
            model_name=model_name,
            page=page,
            page_size=page_size,
            offset=offset,
            limit=limit,
            filters=filters,
            sort_by=sort_by,
            filter_func=filter_func,
        )

    # =========================================================================
    # UTILITY OPERATIONS (delegate to repository)
    # =========================================================================

    def count(self, model_name: str, filter_func: FilterFunc | None = None) -> int:
        """Count instances, optionally with filtering.

        Delegates to repository for counting.

        Args:
            model_name: Name of the model.
            filter_func: Optional function to filter instances.

        Returns:
            Number of instances matching the filter.
        """
        return self._repository.count(model_name, filter_func)

    def clear(self, model_name: str | None = None) -> None:
        """Clear data from store.

        Delegates to repository for data clearing.

        Args:
            model_name: Name of model to clear, or None to clear all.
        """
        self._repository.clear(model_name)

    def get_models(self) -> list[str]:
        """Get list of all model names in store.

        Delegates to repository.

        Returns:
            List of model names.
        """
        return self._repository.get_models()
