"""Protocols for storage backend strategies.

This module defines the interfaces that all storage backends must implement,
enabling support for multiple persistence (in-memory, JSON, SQLite, PostgreSQL).
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Any, Protocol

# Project/local
from ...core.types import QueryResult

# =============================================================================
# PUBLIC API
# =============================================================================


class IStorageStrategy(Protocol):
    """Protocol for storage backend implementations.

    Current implementations:
        - InMemoryStorageStrategy: In-memory storage with OrderedDict

    Future implementations:
        - JSONStorageStrategy: File-based JSON persistence (Issue #48)
        - SQLiteStorageStrategy: SQLite database storage (Issue #51)
        - PostgreSQLStorageStrategy: PostgreSQL database storage (Issue #50)

    Design notes:
        - Each implementation handles its own query optimization
        - Filtering/sorting strategies vary by backend (SQL uses WHERE/ORDER BY,
          in-memory filters Python lists)
        - Transaction handling is backend-specific

    Example:
        >>> storage = InMemoryStorageStrategy()
        >>> instance = storage.create("User", {"name": "Alice"})
        >>> instance["id"]
        1
    """

    def create(
        self, model: str, data: dict[str, Any], auto_id: bool = True
    ) -> dict[str, Any]:
        """Create a new instance.

        Args:
            model: Model name
            data: Instance data
            auto_id: Whether to auto-generate ID

        Returns:
            Created instance with ID

        Raises:
            DuplicateInstanceError: If instance with ID already exists
        """
        ...

    def read(self, model: str, instance_id: int) -> dict[str, Any] | None:
        """Read an instance by ID.

        Args:
            model: Model name
            instance_id: Instance ID

        Returns:
            Instance data or None if not found
        """
        ...

    def update(
        self, model: str, instance_id: int, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing instance.

        Args:
            model: Model name
            instance_id: Instance ID
            data: Updated data

        Returns:
            Updated instance

        Raises:
            InstanceNotFoundError: If instance doesn't exist
        """
        ...

    def delete(self, model: str, instance_id: int) -> dict[str, Any] | None:
        """Delete an instance by ID.

        Args:
            model: Model name
            instance_id: Instance ID

        Returns:
            Deleted instance data or None if not found
        """
        ...

    def list(
        self,
        model: str,
        page: int | None = None,
        page_size: int | None = None,
        offset: int | None = None,
        limit: int | None = None,
        filters: list[Any] | None = None,
        sort_by: list[Any] | None = None,
    ) -> QueryResult:
        """List instances with filtering, sorting, and pagination.

        Args:
            model: Model name
            page: Page number (1-indexed) for page-based pagination
            page_size: Items per page
            offset: Starting offset for offset-based pagination
            limit: Maximum items for offset-based pagination
            filters: List of filter specifications
            sort_by: List of sort specifications

        Returns:
            QueryResult with items and pagination metadata

        Note:
            Each backend optimizes this differently:
            - InMemory: Load all, filter/sort in Python
            - SQL: Generate WHERE/ORDER BY clauses
            - NoSQL: Use database query operators
        """
        ...

    def count(self, model: str) -> int:
        """Count total instances for a model.

        Args:
            model: Model name

        Returns:
            Total count
        """
        ...

    def clear(self, model: str | None = None) -> None:
        """Clear all data for a model or all models.

        Args:
            model: Model name, or None to clear all models
        """
        ...


class IBulkStorageStrategy(Protocol):
    """Protocol for bulk storage operations.

    Bulk operations provide atomicity and performance optimizations.
    Implementation varies by backend:
    - InMemory: Manual rollback on failure
    - SQL: Database transactions
    - JSON: Atomic file write

    Example:
        >>> storage = InMemoryStorageStrategy()
        >>> result = storage.bulk_create("User", [
        ...     {"name": "Alice"},
        ...     {"name": "Bob"},
        ... ])
        >>> result["created"]
        2
    """

    def bulk_create(
        self,
        model: str,
        data_list: list[dict[str, Any]],
        allow_partial: bool = False,
        max_batch_size: int | None = None,
    ) -> dict[str, Any]:
        """Create multiple instances in a single operation.

        Args:
            model: Model name
            data_list: List of instance data
            allow_partial: If True, continue on error; if False, rollback all
            max_batch_size: Maximum batch size (enforced by config)

        Returns:
            Result dict with created count, data, and errors

        Raises:
            BatchSizeExceededError: If batch exceeds max_batch_size
        """
        ...

    def bulk_update(
        self,
        model: str,
        data_list: list[dict[str, Any]],
        allow_partial: bool = False,
        max_batch_size: int | None = None,
    ) -> dict[str, Any]:
        """Update multiple instances in a single operation.

        Args:
            model: Model name
            data_list: List of instance data (must include 'id' field)
            allow_partial: If True, continue on error; if False, rollback all
            max_batch_size: Maximum batch size

        Returns:
            Result dict with updated count, data, and errors

        Raises:
            BatchSizeExceededError: If batch exceeds max_batch_size
        """
        ...

    def bulk_delete(
        self,
        model: str,
        ids: list[int],
        allow_partial: bool = False,
        max_batch_size: int | None = None,
    ) -> dict[str, Any]:
        """Delete multiple instances in a single operation.

        Args:
            model: Model name
            ids: List of instance IDs to delete
            allow_partial: If True, continue on error; if False, rollback all
            max_batch_size: Maximum batch size

        Returns:
            Result dict with deleted count and errors

        Raises:
            BatchSizeExceededError: If batch exceeds max_batch_size
        """
        ...
