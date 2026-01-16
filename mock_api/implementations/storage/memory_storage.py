"""In-memory repository implementation for CRUD operations.

This module provides a thread-safe in-memory repository for managing mock data
with full CRUD operations and referential integrity awareness.

Optimized with:
- O(1) lookups using hash map indices
- OrderedDict for maintaining insertion order with efficient operations
- Reduced deepcopy overhead
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
import threading
from collections import OrderedDict
from collections.abc import Callable
from copy import deepcopy
from typing import Any

# Project/local
from ...core.constants import PRIMARY_KEY_FIELD, BulkResponseKey
from ...core.exceptions import DuplicateInstanceError, InstanceNotFoundError
from ...core.protocols import (
    IBulkRepository,
    IConcurrencyManager,
    IRepository,
    IStorageManager,
)
from ...core.query.executor import MemoryQueryExecutor
from ...core.services import RepositoryValidator, ResultBuilder
from ...core.types import BulkOperationError, FilterSpec, QueryResult, SortSpec
from ...utils.logger import get_logger

# =============================================================================
# TYPES & CONSTANTS
# =============================================================================
logger = get_logger(__name__)

# =============================================================================
# PRIVATE IMPLEMENTATION DETAILS
# =============================================================================


class _InMemoryConcurrencyManager(IConcurrencyManager):
    """Thread safety manager for InMemoryRepository.

    PRIVATE CLASS - Implementation detail of InMemoryRepository.

    Provides thread-safe operations using a lock. Other backends may use
    different concurrency strategies (e.g., database-level locks, async).
    """

    def __init__(self) -> None:
        """Initialize concurrency manager with a lock."""
        self._lock = threading.Lock()

    def __enter__(self):
        """Acquire lock (context manager protocol).

        Returns:
            Self for use in 'with' statements.
        """
        self._lock.acquire()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Release lock (context manager protocol).

        Args:
            exc_type: Exception type if raised.
            exc_val: Exception value if raised.
            exc_tb: Traceback if exception raised.
        """
        self._lock.release()


class _InMemoryIdGenerator:
    """Internal ID generator for InMemoryRepository.

    PRIVATE CLASS - Implementation detail of InMemoryRepository.

    Maintains per-model ID counters for manual auto-increment.
    SQL backends use database AUTOINCREMENT instead of this.
    """

    def __init__(self) -> None:
        """Initialize ID generator with empty counters."""
        self._counters: dict[str, int] = {}

    def next_id(self, model_name: str) -> int:
        """Generate next ID for a model.

        Args:
            model_name: Name of the model.

        Returns:
            Next available ID (auto-incremented).
        """
        if model_name not in self._counters:
            self._counters[model_name] = 0

        self._counters[model_name] += 1
        return self._counters[model_name]

    def assign_id_if_missing(
        self, model_name: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Assign ID to data if not present.

        Args:
            model_name: Name of the model.
            data: Data dictionary (will be modified).

        Returns:
            Data dictionary with ID assigned.
        """
        if PRIMARY_KEY_FIELD not in data:
            data[PRIMARY_KEY_FIELD] = self.next_id(model_name)
        return data

    def update_counter(self, model_name: str, instance_id: int) -> None:
        """Update counter to track highest seen ID.

        Used when loading existing data to ensure new IDs don't conflict.

        Args:
            model_name: Name of the model.
            instance_id: ID value to track.
        """
        if model_name not in self._counters:
            self._counters[model_name] = 0

        if instance_id > self._counters[model_name]:
            self._counters[model_name] = instance_id

    def get_current(self, model_name: str) -> int:
        """Get current counter value for a model.

        Args:
            model_name: Name of the model.

        Returns:
            Current counter value (0 if model not initialized).
        """
        return self._counters.get(model_name, 0)

    def reset(self, model_name: str | None = None) -> None:
        """Reset ID counter(s).

        Args:
            model_name: Name of model to reset, or None to reset all.
        """
        if model_name is None:
            self._counters.clear()
        elif model_name in self._counters:
            self._counters[model_name] = 0


class _InMemoryStorageManager(IStorageManager):
    """Storage manager for InMemoryRepository.

    PRIVATE CLASS - Implementation detail of InMemoryRepository.

    Handles OrderedDict operations for storing instances. Other backends
    use different storage (SQL tables, JSON files, etc.).
    """

    def __init__(self) -> None:
        """Initialize storage with empty data structure."""
        self._data: dict[str, OrderedDict[int, dict[str, Any]]] = {}

    def ensure_model_exists(self, model_name: str) -> None:
        """Ensure model storage exists.

        Args:
            model_name: Name of the model.
        """
        if model_name not in self._data:
            self._data[model_name] = OrderedDict()

    def get(self, model_name: str, instance_id: int) -> dict[str, Any] | None:
        """Get instance by ID.

        Args:
            model_name: Name of the model.
            instance_id: ID of the instance.

        Returns:
            Instance dict or None if not found.
        """
        if model_name not in self._data:
            return None
        return self._data[model_name].get(instance_id)

    def put(self, model_name: str, instance_id: int, instance: dict[str, Any]) -> None:
        """Store instance.

        Args:
            model_name: Name of the model.
            instance_id: ID of the instance.
            instance: Instance data.
        """
        self.ensure_model_exists(model_name)
        self._data[model_name][instance_id] = instance

    def delete(self, model_name: str, instance_id: int) -> dict[str, Any] | None:
        """Delete instance and return it.

        Args:
            model_name: Name of the model.
            instance_id: ID of the instance.

        Returns:
            Deleted instance or None if not found.
        """
        if model_name not in self._data:
            return None
        return self._data[model_name].pop(instance_id, None)

    def get_all(self, model_name: str) -> list[dict[str, Any]]:
        """Get all instances for a model.

        Args:
            model_name: Name of the model.

        Returns:
            List of all instances.
        """
        if model_name not in self._data:
            return []
        return list(self._data[model_name].values())

    def contains(self, model_name: str, instance_id: int) -> bool:
        """Check if instance exists.

        Args:
            model_name: Name of the model.
            instance_id: ID to check.

        Returns:
            True if instance exists.
        """
        if model_name not in self._data:
            return False
        return instance_id in self._data[model_name]

    def count(self, model_name: str) -> int:
        """Count instances in a model.

        Args:
            model_name: Name of the model.

        Returns:
            Number of instances.
        """
        if model_name not in self._data:
            return 0
        return len(self._data[model_name])

    def clear(self, model_name: str | None = None) -> None:
        """Clear storage.

        Args:
            model_name: If provided, clear only this model. Otherwise clear all.
        """
        if model_name:
            self._data[model_name] = OrderedDict()
        else:
            self._data.clear()

    def get_models(self) -> list[str]:
        """Get list of all model names.

        Returns:
            List of model names.
        """
        return list(self._data.keys())


class _InMemoryBulkHandler(IBulkRepository):
    """Bulk operations handler for InMemoryRepository.

    Handles bulk create/update/delete operations with atomicity, error handling,
    and rollback support. Other backends implement bulk operations differently:
    - SQL: Use database transactions and batch INSERT/UPDATE/DELETE
    - JSON: Use temporary files and atomic rename
    - NoSQL: Use database-specific bulk APIs
    """

    def __init__(
        self,
        storage: IStorageManager,
        id_generator: _InMemoryIdGenerator,
        validator: RepositoryValidator,
        result_builder: ResultBuilder,
    ):
        """Initialize bulk handler.

        Args:
            storage: Storage manager for data operations.
            id_generator: ID generator for assigning IDs (in-memory specific).
            validator: Validator for batch size checks.
            result_builder: Result builder for formatting responses.
        """
        self._storage = storage
        self._id_generator = id_generator
        self._validator = validator
        self._result_builder = result_builder

    def _check_duplicate(self, model_name: str, instance_id: int) -> None:
        """Check for duplicate ID and raise if exists.

        Args:
            model_name: Name of the model.
            instance_id: ID to check.

        Raises:
            DuplicateInstanceError: If instance with ID already exists.
        """
        if self._storage.contains(model_name, instance_id):
            raise DuplicateInstanceError(model_name, instance_id)

    def _check_exists(self, model_name: str, instance_id: int) -> dict[str, Any]:
        """Check if instance exists and return it, raise if not found.

        Args:
            model_name: Name of the model.
            instance_id: ID to check.

        Returns:
            The instance if found.

        Raises:
            InstanceNotFoundError: If instance not found.
        """
        instance = self._storage.get(model_name, instance_id)
        if instance is None:
            raise InstanceNotFoundError(model_name, instance_id)
        return instance

    def bulk_create(
        self,
        model_name: str,
        data_list: list[dict[str, Any]],
        allow_partial: bool = False,
        max_batch_size: int | None = None,
    ) -> dict[str, Any]:
        """Create multiple instances atomically.

        Args:
            model_name: Name of the model to create.
            data_list: List of instance dictionaries to create.
            allow_partial: If True, continue on errors; if False, rollback on
                first error.
            max_batch_size: Maximum batch size allowed (optional validation).

        Returns:
            Dict with 'created' count, 'data' list, and optional 'errors' list.

        Raises:
            BatchSizeExceededError: If batch size exceeds maximum.
        """
        self._validator.validate_batch_size(len(data_list), max_batch_size)
        self._storage.ensure_model_exists(model_name)

        created_items: list[dict[str, Any]] = []
        created_ids: list[int] = []
        errors: list[BulkOperationError] = []

        for idx, data in enumerate(data_list):
            try:
                instance = deepcopy(data)

                # Auto-assign ID
                if PRIMARY_KEY_FIELD not in instance:
                    instance[PRIMARY_KEY_FIELD] = self._id_generator.next_id(model_name)

                instance_id = instance[PRIMARY_KEY_FIELD]

                # Check for duplicate
                self._check_duplicate(model_name, instance_id)

                # Add to storage
                self._storage.put(model_name, instance_id, instance)
                created_items.append(deepcopy(instance))
                created_ids.append(instance_id)

            except Exception as e:
                error = BulkOperationError(index=idx, item=data, error=str(e))
                errors.append(error)

                if not allow_partial:
                    # Rollback all created items
                    for created_id in created_ids:
                        self._storage.delete(model_name, created_id)
                    raise

        logger.info(
            f"Bulk created {len(created_items)}/{len(data_list)} {model_name}(s)"
        )

        return self._result_builder.build_bulk_result(
            BulkResponseKey.CREATED, len(created_items), created_items, errors
        )

    def bulk_update(
        self,
        model_name: str,
        data_list: list[dict[str, Any]],
        allow_partial: bool = False,
        max_batch_size: int | None = None,
    ) -> dict[str, Any]:
        """Update multiple instances atomically.

        Args:
            model_name: Name of the model.
            data_list: List of dicts with 'id' and fields to update.
            allow_partial: If True, continue on errors; if False, rollback on
                first error.
            max_batch_size: Maximum batch size allowed (optional validation).

        Returns:
            Dict with 'updated' count, 'data' list, and optional 'errors' list.

        Raises:
            BatchSizeExceededError: If batch size exceeds maximum.
            InstanceNotFoundError: If instance not found (when not in partial mode).
        """
        self._validator.validate_batch_size(len(data_list), max_batch_size)

        # Early return for empty list
        if not data_list:
            return self._result_builder.build_bulk_result(
                BulkResponseKey.UPDATED, 0, [], None
            )

        # Check if model exists
        if self._storage.count(model_name) == 0:
            if not allow_partial:
                raise InstanceNotFoundError(model_name, -1)
            error_list = [
                BulkOperationError(idx, data, f"Model {model_name} not found")
                for idx, data in enumerate(data_list)
            ]
            return self._result_builder.build_bulk_result(
                BulkResponseKey.UPDATED, 0, [], error_list
            )

        updated_items: list[dict[str, Any]] = []
        original_values: dict[int, dict[str, Any]] = {}
        errors: list[BulkOperationError] = []

        for idx, data in enumerate(data_list):
            try:
                # Validate ID present
                self._validator.validate_id_present(data)

                instance_id = data[PRIMARY_KEY_FIELD]

                # Check exists and get instance
                instance = self._check_exists(model_name, instance_id)

                # Store original for rollback
                original_values[instance_id] = deepcopy(instance)

                # Update fields
                instance.update(data)
                instance[PRIMARY_KEY_FIELD] = instance_id

                self._storage.put(model_name, instance_id, instance)
                updated_items.append(deepcopy(instance))

            except Exception as e:
                error = BulkOperationError(index=idx, item=data, error=str(e))
                errors.append(error)

                if not allow_partial:
                    # Rollback all updates
                    for orig_id, orig_data in original_values.items():
                        self._storage.put(model_name, orig_id, orig_data)
                    raise

        logger.info(
            f"Bulk updated {len(updated_items)}/{len(data_list)} {model_name}(s)"
        )

        return self._result_builder.build_bulk_result(
            BulkResponseKey.UPDATED, len(updated_items), updated_items, errors
        )

    def bulk_delete(
        self,
        model_name: str,
        id_list: list[int],
        allow_partial: bool = False,
        max_batch_size: int | None = None,
    ) -> dict[str, Any]:
        """Delete multiple instances atomically.

        Args:
            model_name: Name of the model.
            id_list: List of instance IDs to delete.
            allow_partial: If True, continue on errors; if False, rollback on
                first error.
            max_batch_size: Maximum batch size allowed (optional validation).

        Returns:
            Dict with 'deleted' count, 'id_list' list, and optional 'errors' list.

        Raises:
            BatchSizeExceededError: If batch size exceeds maximum.
            InstanceNotFoundError: If instance not found (when not in partial mode).
        """
        self._validator.validate_batch_size(len(id_list), max_batch_size)

        # Early return for empty list
        if not id_list:
            return self._result_builder.build_bulk_result(
                BulkResponseKey.DELETED, 0, [], [], data_key=BulkResponseKey.IDS
            )

        # Check if model exists
        if self._storage.count(model_name) == 0:
            if not allow_partial:
                raise InstanceNotFoundError(model_name, -1)

            error_list = [
                BulkOperationError(
                    idx,
                    {PRIMARY_KEY_FIELD: instance_id},
                    f"Model {model_name} not found",
                )
                for idx, instance_id in enumerate(id_list)
            ]
            return self._result_builder.build_bulk_result(
                BulkResponseKey.DELETED,
                0,
                [],
                error_list,
                data_key=BulkResponseKey.IDS,
            )

        deleted_ids: list[int] = []
        deleted_instances: dict[int, dict[str, Any]] = {}
        errors: list[BulkOperationError] = []

        for idx, instance_id in enumerate(id_list):
            try:
                # Check exists and get instance for rollback
                instance = self._check_exists(model_name, instance_id)

                # Store for rollback
                deleted_instances[instance_id] = instance

                # Delete
                self._storage.delete(model_name, instance_id)
                deleted_ids.append(instance_id)

            except Exception as e:
                error = BulkOperationError(
                    index=idx,
                    item={PRIMARY_KEY_FIELD: instance_id},
                    error=str(e),
                )
                errors.append(error)

                if not allow_partial:
                    # Rollback all deletions
                    for del_id, del_instance in deleted_instances.items():
                        self._storage.put(model_name, del_id, del_instance)
                    raise

        logger.info(f"Bulk deleted {len(deleted_ids)}/{len(id_list)} {model_name}(s)")

        return self._result_builder.build_bulk_result(
            BulkResponseKey.DELETED,
            len(deleted_ids),
            deleted_ids,
            errors,
            data_key=BulkResponseKey.IDS,
        )


# =============================================================================
# PUBLIC API
# =============================================================================


class InMemoryRepository(IRepository, IBulkRepository):
    """Thread-safe in-memory repository with optimized CRUD and bulk operations.

    Implements IRepository and IBulkRepository protocols for dependency injection.

    Provides a high-performance repository for managing mock data with:
    - Full CRUD operations (Create, Read, Update, Delete)
    - Bulk operations (bulk_create, bulk_update, bulk_delete)
    - O(1) lookups via hash map indices
    - Thread-safe operations
    - Referential integrity awareness

    Performance Characteristics:
    - Single CRUD: O(1)
    - Bulk operations: O(n) where n is batch size
    """

    def __init__(
        self,
        storage: IStorageManager | None = None,
        concurrency: IConcurrencyManager | None = None,
        id_generator: _InMemoryIdGenerator | None = None,
    ) -> None:
        """Initialize repository with pluggable components.

        Args:
            storage: Storage manager (defaults to _InMemoryStorageManager).
            concurrency: Concurrency manager (defaults to
                _InMemoryConcurrencyManager).
            id_generator: ID generator (defaults to _InMemoryIdGenerator,
                in-memory specific).
        """
        # Core components (with defaults for in-memory implementation)
        self._storage = storage or _InMemoryStorageManager()
        self._concurrency = concurrency or _InMemoryConcurrencyManager()
        self._id_generator = id_generator or _InMemoryIdGenerator()

        # Query executor (internal implementation)
        self._query_executor = MemoryQueryExecutor()

        # Shared services (reusable across all backends)
        self._validator = RepositoryValidator()
        self._result_builder = ResultBuilder()

        # Bulk operations handler
        self._bulk_handler = _InMemoryBulkHandler(
            storage=self._storage,
            id_generator=self._id_generator,
            validator=self._validator,
            result_builder=self._result_builder,
        )

        logger.debug("Initialized empty repository with pluggable components")

    def load(self, data: dict[str, list[dict[str, Any]]]) -> None:
        """Load bulk data into the repository.

        Args:
            data: Dictionary mapping model names to lists of instances.
        """
        with self._concurrency:
            for model_name, instances in data.items():
                # Initialize storage for this model
                self._storage.ensure_model_exists(model_name)
                self._storage.clear(model_name)

                # Load instances with deep copy
                for instance in instances:
                    instance_copy = deepcopy(instance)
                    instance_id = instance_copy.get(PRIMARY_KEY_FIELD)
                    if instance_id is not None:
                        self._storage.put(model_name, instance_id, instance_copy)

                        # Update ID counter
                        self._id_generator.update_counter(model_name, instance_id)

            logger.info(f"Loaded data for {len(data)} model(s)")

    def create(
        self, model_name: str, data: dict[str, Any], auto_id: bool = True
    ) -> dict[str, Any]:
        """Create a new instance in the repository.

        Args:
            model_name: Name of the model to create.
            data: Dictionary of field values.
            auto_id: If True, automatically assign ID if not provided.

        Returns:
            The created instance with ID assigned.

        Raises:
            ValueError: If instance with same ID already exists.
        """
        with self._concurrency:
            # Ensure model exists in storage
            self._storage.ensure_model_exists(model_name)

            # Deep copy to avoid mutation
            instance = deepcopy(data)

            # Auto-assign ID if needed
            if auto_id and PRIMARY_KEY_FIELD not in instance:
                instance[PRIMARY_KEY_FIELD] = self._id_generator.next_id(model_name)

            # Get instance ID
            instance_id = instance.get(PRIMARY_KEY_FIELD)

            # Check for duplicate ID
            if instance_id is not None and self._storage.contains(
                model_name, instance_id
            ):
                raise DuplicateInstanceError(model_name, instance_id)

            # Add to storage
            if instance_id is not None:
                self._storage.put(model_name, instance_id, instance)
                # Update counter to track highest ID
                self._id_generator.update_counter(model_name, instance_id)

            logger.debug(f"Created {model_name} with {PRIMARY_KEY_FIELD}={instance_id}")
            return deepcopy(instance)

    def read(self, model_name: str, instance_id: int) -> dict[str, Any] | None:
        """Read a single instance by ID.

        Args:
            model_name: Name of the model.
            instance_id: ID of the instance to retrieve.

        Returns:
            The instance if found, None otherwise.
        """
        with self._concurrency:
            instance = self._storage.get(model_name, instance_id)
            return deepcopy(instance) if instance else None

    def update(
        self, model_name: str, instance_id: int, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing instance.

        Args:
            model_name: Name of the model.
            instance_id: ID of the instance to update.
            data: Dictionary of fields to update.

        Returns:
            The updated instance.

        Raises:
            ValueError: If instance not found.
        """
        with self._concurrency:
            # Check if instance exists
            instance = self._storage.get(model_name, instance_id)
            if instance is None:
                raise InstanceNotFoundError(model_name, instance_id)

            # Update fields (preserve ID)
            instance.update(data)
            instance[PRIMARY_KEY_FIELD] = instance_id

            # Store updated instance
            self._storage.put(model_name, instance_id, instance)

            logger.debug(f"Updated {model_name} with {PRIMARY_KEY_FIELD}={instance_id}")
            return deepcopy(instance)

    def delete(self, model_name: str, instance_id: int) -> bool:
        """Delete an instance by ID.

        Args:
            model_name: Name of the model.
            instance_id: ID of the instance to delete.

        Returns:
            True if deleted, False if not found.

        Time Complexity: O(1) - OrderedDict deletion
        """
        with self._concurrency:
            deleted_instance = self._storage.delete(model_name, instance_id)

            if deleted_instance:
                logger.debug(
                    f"Deleted {model_name} with {PRIMARY_KEY_FIELD}={instance_id}"
                )
                return True

            return False

    def bulk_create(
        self,
        model_name: str,
        data_list: list[dict[str, Any]],
        allow_partial: bool = False,
        max_batch_size: int | None = None,
    ) -> dict[str, Any]:
        """Create multiple instances atomically.

        Args:
            model_name: Name of the model to create.
            data_list: List of instance dictionaries to create.
            allow_partial: If True, continue on errors; if False, rollback on
                first error.
            max_batch_size: Maximum batch size allowed (optional validation).

        Returns:
            Dict with 'created' count, 'data' list, and optional 'errors' list.

        Raises:
            BatchSizeExceededError: If batch size exceeds maximum.

        Time Complexity: O(n) where n is batch size
        """
        with self._concurrency:
            return self._bulk_handler.bulk_create(
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

        Args:
            model_name: Name of the model.
            data_list: List of dicts with 'id' and fields to update.
            allow_partial: If True, continue on errors; if False, rollback on
                first error.
            max_batch_size: Maximum batch size allowed (optional validation).

        Returns:
            Dict with 'updated' count, 'data' list, and optional 'errors' list.

        Raises:
            BatchSizeExceededError: If batch size exceeds maximum.
            InstanceNotFoundError: If instance not found (when not in partial mode)
        """
        with self._concurrency:
            return self._bulk_handler.bulk_update(
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

        Args:
            model_name: Name of the model.
            id_list: List of instance IDs to delete.
            allow_partial: If True, continue on errors; if False, rollback on
                first error.
            max_batch_size: Maximum batch size allowed (optional validation).

        Returns:
            Dict with 'deleted' count, 'id_list' list, and optional 'errors' list.

        Raises:
            BatchSizeExceededError: If batch size exceeds maximum.
            InstanceNotFoundError: If instance not found (when not in partial mode).
        """
        with self._concurrency:
            return self._bulk_handler.bulk_delete(
                model_name, id_list, allow_partial, max_batch_size
            )

    def clear(self, model_name: str | None = None) -> None:
        """Clear data from repository.

        Args:
            model_name: If provided, clear only this model. Otherwise clear all.
        """
        with self._concurrency:
            self._storage.clear(model_name)
            self._id_generator.reset(model_name)
            if model_name:
                logger.debug(f"Cleared {model_name} data")
            else:
                logger.debug("Cleared all data")

    def get_models(self) -> list[str]:
        """Get list of all model names in the repository.

        Returns:
            List of model names.

        Time Complexity: O(n) where n is number of models
        """
        with self._concurrency:
            return self._storage.get_models()

    def list(
        self,
        model_name: str,
        page: int | None = None,
        page_size: int | None = None,
        offset: int | None = None,
        limit: int | None = None,
        filters: list[FilterSpec] | None = None,
        sort_by: list[SortSpec] | None = None,
        filter_func: Callable[[dict[str, Any]], bool] | None = None,
    ) -> QueryResult:
        """List instances with optional filtering, sorting, and pagination.

        For in-memory implementation, loads all items then delegates to
        query executor for filtering/sorting/pagination.

        Args:
            model_name: Name of the model.
            page: Page number (1-indexed) for page-based pagination.
            page_size: Number of items per page.
            offset: Starting offset (0-indexed) for offset-based pagination.
            limit: Maximum items to return.
            filters: Optional list of filter specifications.
            sort_by: Optional list of sort specifications.
            filter_func: Optional custom filter function (legacy support).

        Returns:
            QueryResult with filtered, sorted, paginated items and metadata.
        """
        with self._concurrency:
            # Get all items for this model
            items = self._storage.get_all(model_name)

        # Apply custom filter function if provided (legacy support)
        if filter_func:
            items = [item for item in items if filter_func(item)]

        # Delegate to query executor for filtering, sorting, pagination
        return self._query_executor.execute_query(
            model_name=model_name,
            items=items,
            filters=filters,
            sort_by=sort_by,
            page=page,
            page_size=page_size,
            offset=offset,
            limit=limit,
        )

    def count(
        self,
        model_name: str,
        filter_func: Callable[[dict[str, Any]], bool] | None = None,
    ) -> int:
        """Count instances, optionally with filtering.

        Args:
            model_name: Name of the model.
            filter_func: Optional function to filter instances.

        Returns:
            Number of instances matching the filter.

        Time Complexity:
        - Without filter: O(1) - length of OrderedDict
        - With filter: O(n) - must check each instance
        """
        with self._concurrency:
            if filter_func is None:
                # O(1) without filter
                return self._storage.count(model_name)

            # O(n) with filter
            items = self._storage.get_all(model_name)
            return sum(1 for item in items if filter_func(item))
