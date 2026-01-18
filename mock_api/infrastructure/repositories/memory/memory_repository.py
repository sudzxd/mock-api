"""In-memory repository implementation.

Thread-safe implementation using RLock for concurrent access.
All data stored in dictionaries in memory (no persistence).
"""

from __future__ import annotations

import math

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from threading import RLock
from typing import Any

# Project/local
from mock_api.core.exceptions import EntityNotFoundError, ModelNotFoundError
from mock_api.domain.repositories.protocols import (
    IBulkRepository,
    IReadRepository,
    IWriteRepository,
)
from mock_api.domain.services.protocols import (
    IFilterExecutor,
    ISortExecutor,
    IValidationService,
)
from mock_api.domain.value_objects.query import FilterSpec, QueryResult, SortSpec
from mock_api.domain.value_objects.schema import ModelSchema


# =============================================================================
# CORE CLASSES
# =============================================================================
class MemoryRepository(
    IReadRepository[dict[str, Any]],
    IWriteRepository[dict[str, Any]],
    IBulkRepository[dict[str, Any]],
):
    """Thread-safe in-memory repository.

    Features:
    - Thread-safe via RLock (reentrant lock)
    - Auto-incrementing integer IDs
    - Validation via Pydantic (dynamically created models)
    - In-memory filtering and sorting
    - Transaction simulation for bulk operations

    Storage structure:
        {
            "User": {
                1: {"id": 1, "name": "Alice", ...},
                2: {"id": 2, "name": "Bob", ...},
            },
            "Post": {
                1: {"id": 1, "title": "Hello", ...},
            }
        }
    """

    def __init__(
        self,
        schemas: dict[str, ModelSchema],
        validation_service: IValidationService,
        filter_executor: IFilterExecutor,
        sort_executor: ISortExecutor,
    ) -> None:
        """Initialize in-memory repository.

        Args:
            schemas: Model schemas for validation
            validation_service: Service for data validation
            filter_executor: Service for executing filter specifications
            sort_executor: Service for executing sort specifications
        """
        self._schemas = schemas
        self._validation_service = validation_service
        self._filter_executor = filter_executor
        self._sort_executor = sort_executor
        self._lock = RLock()

        # Storage: {model_name: {entity_id: entity_dict}}
        self._storage: dict[str, dict[int, dict[str, Any]]] = {
            model_name: {} for model_name in schemas
        }

        # Auto-increment counters: {model_name: next_id}
        self._next_ids: dict[str, int] = dict.fromkeys(schemas, 1)

    # ========== IReadRepository Implementation ==========

    def get(
        self,
        model_name: str,
        entity_id: int,
    ) -> dict[str, Any]:
        """Get single entity by ID.

        Thread-safe read with lock.

        Args:
            model_name: Model name
            entity_id: Entity ID

        Returns:
            Entity dict

        Raises:
            ModelNotFoundError: If model doesn't exist
            EntityNotFoundError: If entity doesn't exist
        """
        self._validate_model_exists(model_name)

        with self._lock:
            entity = self._storage[model_name].get(entity_id)
            if entity is None:
                raise EntityNotFoundError(
                    model_name=model_name,
                    entity_id=entity_id,
                )
            return entity.copy()

    def list(
        self,
        model_name: str,
        *,
        page: int = 1,
        page_size: int = 20,
        filters: list[FilterSpec] | None = None,
        sorts: list[SortSpec] | None = None,
    ) -> QueryResult[dict[str, Any]]:
        """List entities with filtering, sorting, and pagination.

        Implementation:
        1. Acquire read lock
        2. Get all entities for model
        3. Apply filters
        4. Apply sorts
        5. Apply pagination
        6. Return QueryResult

        Args:
            model_name: Model name
            page: Page number (1-indexed)
            page_size: Items per page
            filters: Filter specifications
            sorts: Sort specifications

        Returns:
            QueryResult with paginated items

        Raises:
            ModelNotFoundError: If model doesn't exist
        """
        self._validate_model_exists(model_name)

        with self._lock:
            # Get all entities
            entities = list(self._storage[model_name].values())

            # Delegate filtering to filter executor
            entities = self._filter_executor.apply(entities, filters)

            # Count total after filtering
            total = len(entities)

            # Delegate sorting to sort executor
            entities = self._sort_executor.apply(entities, sorts)

            # Apply pagination (repository concern - data access pattern)
            paginated_items, total_pages = self._paginate(entities, page, page_size)

            return QueryResult(
                items=tuple(paginated_items),
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            )

    def count(
        self,
        model_name: str,
        *,
        filters: list[FilterSpec] | None = None,
    ) -> int:
        """Count entities matching filters.

        Args:
            model_name: Model name
            filters: Filter specifications

        Returns:
            Count of matching entities

        Raises:
            ModelNotFoundError: If model doesn't exist
        """
        self._validate_model_exists(model_name)

        with self._lock:
            entities = list(self._storage[model_name].values())
            entities = self._filter_executor.apply(entities, filters)
            return len(entities)

    def exists(
        self,
        model_name: str,
        entity_id: int,
    ) -> bool:
        """Check if entity exists.

        Args:
            model_name: Model name
            entity_id: Entity ID

        Returns:
            True if entity exists

        Raises:
            ModelNotFoundError: If model doesn't exist
        """
        self._validate_model_exists(model_name)

        with self._lock:
            return entity_id in self._storage[model_name]

    # ========== IWriteRepository Implementation ==========

    def create(
        self,
        model_name: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Create new entity.

        Implementation:
        1. Validate model exists
        2. Validate data against schema (Pydantic)
        3. Acquire write lock
        4. Assign next ID
        5. Store entity
        6. Release lock
        7. Return created entity

        Args:
            model_name: Model name
            data: Entity data (without ID)

        Returns:
            Created entity with assigned ID

        Raises:
            ModelNotFoundError: If model doesn't exist
            ValidationError: If data is invalid
        """
        self._validate_model_exists(model_name)

        with self._lock:
            return self._create_entity(model_name, data)

    def update(
        self,
        model_name: str,
        entity_id: int,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Update existing entity.

        Supports partial updates (only provided fields updated).

        Args:
            model_name: Model name
            entity_id: Entity ID
            data: Updated fields

        Returns:
            Updated entity

        Raises:
            ModelNotFoundError: If model doesn't exist
            EntityNotFoundError: If entity doesn't exist
            ValidationError: If data is invalid
        """
        self._validate_model_exists(model_name)

        with self._lock:
            return self._update_entity(model_name, entity_id, data)

    def delete(
        self,
        model_name: str,
        entity_id: int,
    ) -> bool:
        """Delete entity by ID.

        Args:
            model_name: Model name
            entity_id: Entity ID

        Returns:
            True if deleted

        Raises:
            ModelNotFoundError: If model doesn't exist
            EntityNotFoundError: If entity doesn't exist
        """
        self._validate_model_exists(model_name)

        with self._lock:
            return self._delete_entity(model_name, entity_id)

    # ========== IBulkRepository Implementation ==========

    def bulk_create(
        self,
        model_name: str,
        data_list: list[dict[str, Any]],
        *,
        allow_partial: bool = False,
    ) -> list[dict[str, Any]]:
        """Bulk create entities with atomic transaction support.

        Implementation:
        - If allow_partial=False: All-or-nothing atomic operation
        - If allow_partial=True: Best-effort, skip failures

        Args:
            model_name: Model name
            data_list: List of entity data dicts
            allow_partial: Continue on errors

        Returns:
            List of created entities

        Raises:
            ModelNotFoundError: If model doesn't exist
            ValidationError: If validation fails (and not allow_partial)
            BulkOperationError: If partial failure with allow_partial
        """
        with self._lock:
            # Validate model exists
            self._validate_model_exists(model_name)

            if allow_partial:
                # Best-effort mode: continue on errors
                created: list[dict[str, Any]] = []
                for data in data_list:
                    try:
                        entity = self._create_entity(model_name, data)
                        created.append(entity)
                    except Exception:
                        # Skip failures
                        pass
                return created
            # Atomic mode: all-or-nothing
            # Create snapshot for rollback
            storage_snapshot = self._storage[model_name].copy()
            next_id_snapshot = self._next_ids[model_name]

            created: list[dict[str, Any]] = []
            try:
                # Perform all creates
                for data in data_list:
                    entity = self._create_entity(model_name, data)
                    created.append(entity)
            except Exception:
                # Rollback on any failure
                self._storage[model_name] = storage_snapshot
                self._next_ids[model_name] = next_id_snapshot
                raise
            else:
                # All succeeded - commit by keeping changes
                return created

    def _create_entity(self, model_name: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create single entity without acquiring lock (internal helper).

        Args:
            model_name: Model name
            data: Entity data

        Returns:
            Created entity with ID

        Raises:
            ValidationError: If validation fails
        """
        # Validate data
        validated_data = self._validate_data(
            model_name=model_name,
            data=data,
            partial=False,
            exclude_primary_key=True,
        )

        # Get next ID
        entity_id = self._get_next_id(model_name)
        validated_data["id"] = entity_id

        # Store entity
        self._storage[model_name][entity_id] = validated_data

        return validated_data.copy()

    def bulk_update(
        self,
        model_name: str,
        data_list: list[dict[str, Any]],
        *,
        allow_partial: bool = False,
    ) -> list[dict[str, Any]]:
        """Bulk update entities with atomic transaction support.

        Each dict must contain 'id' field.

        Implementation:
        - If allow_partial=False: All-or-nothing atomic operation
        - If allow_partial=True: Best-effort, skip failures

        Args:
            model_name: Model name
            data_list: List of update dicts (with 'id')
            allow_partial: Continue on errors

        Returns:
            List of updated entities

        Raises:
            ModelNotFoundError: If model doesn't exist
            EntityNotFoundError: If entity doesn't exist (and not allow_partial)
            ValidationError: If validation fails (and not allow_partial)
            BulkOperationError: If partial failure
        """
        with self._lock:
            # Validate model exists
            self._validate_model_exists(model_name)

            if allow_partial:
                # Best-effort mode: continue on errors
                updated: list[dict[str, Any]] = []
                for data in data_list:
                    try:
                        data_copy = data.copy()
                        entity_id = data_copy.pop("id")
                        entity = self._update_entity(model_name, entity_id, data_copy)
                        updated.append(entity)
                    except Exception:
                        # Skip failures
                        pass
                return updated
            # Atomic mode: all-or-nothing
            # Create snapshot for rollback
            storage_snapshot = self._storage[model_name].copy()

            updated: list[dict[str, Any]] = []
            try:
                # Perform all updates
                for data in data_list:
                    data_copy = data.copy()
                    entity_id = data_copy.pop("id")
                    entity = self._update_entity(model_name, entity_id, data_copy)
                    updated.append(entity)
            except Exception:
                # Rollback on any failure
                self._storage[model_name] = storage_snapshot
                raise
            else:
                # All succeeded - commit by keeping changes
                return updated

    def _update_entity(
        self, model_name: str, entity_id: Any, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update single entity without acquiring lock (internal helper).

        Args:
            model_name: Model name
            entity_id: Entity ID
            data: Update data (partial)

        Returns:
            Updated entity

        Raises:
            EntityNotFoundError: If entity doesn't exist
            ValidationError: If validation fails
        """
        # Check entity exists
        if entity_id not in self._storage[model_name]:
            raise EntityNotFoundError(model_name=model_name, entity_id=entity_id)

        # Get existing entity
        existing_entity = self._storage[model_name][entity_id]

        # Merge with existing data
        updated_data = {**existing_entity, **data}

        # Validate merged data
        validated_data = self._validate_data(
            model_name=model_name,
            data=updated_data,
            partial=False,
        )

        # Ensure ID is preserved
        validated_data["id"] = entity_id

        # Update storage
        self._storage[model_name][entity_id] = validated_data

        return validated_data.copy()

    def bulk_delete(
        self,
        model_name: str,
        entity_ids: list[int],
        *,
        allow_partial: bool = False,
    ) -> int:
        """Bulk delete entities with atomic transaction support.

        Implementation:
        - If allow_partial=False: All-or-nothing atomic operation
        - If allow_partial=True: Best-effort, skip failures

        Args:
            model_name: Model name
            entity_ids: List of entity IDs
            allow_partial: Continue on errors

        Returns:
            Count of deleted entities

        Raises:
            ModelNotFoundError: If model doesn't exist
            EntityNotFoundError: If entity doesn't exist (and not allow_partial)
            BulkOperationError: If partial failure
        """
        with self._lock:
            # Validate model exists
            self._validate_model_exists(model_name)

            if allow_partial:
                # Best-effort mode: continue on errors
                deleted_count = 0
                for entity_id in entity_ids:
                    try:
                        if self._delete_entity(model_name, entity_id):
                            deleted_count += 1
                    except Exception:
                        # Skip failures
                        pass
                return deleted_count
            # Atomic mode: all-or-nothing
            # Create snapshot for rollback
            storage_snapshot = self._storage[model_name].copy()

            deleted_count = 0
            try:
                # Perform all deletes
                for entity_id in entity_ids:
                    if self._delete_entity(model_name, entity_id):
                        deleted_count += 1
            except Exception:
                # Rollback on any failure
                self._storage[model_name] = storage_snapshot
                raise
            else:
                # All succeeded - commit by keeping changes
                return deleted_count

    def _delete_entity(self, model_name: str, entity_id: Any) -> bool:
        """Delete single entity without acquiring lock (internal helper).

        Args:
            model_name: Model name
            entity_id: Entity ID

        Returns:
            True if deleted, False if not found

        Raises:
            EntityNotFoundError: If entity doesn't exist
        """
        if entity_id not in self._storage[model_name]:
            raise EntityNotFoundError(model_name=model_name, entity_id=entity_id)

        del self._storage[model_name][entity_id]
        return True

    # ========== Private Helper Methods ==========

    def _validate_model_exists(self, model_name: str) -> None:
        """Validate model exists in schemas.

        Args:
            model_name: Model to check

        Raises:
            ModelNotFoundError: If model doesn't exist
        """
        if model_name not in self._schemas:
            raise ModelNotFoundError(
                model_name=model_name,
                available_models=list(self._schemas.keys()),
            )

    def _validate_data(
        self,
        model_name: str,
        data: dict[str, Any],
        *,
        partial: bool = False,
        exclude_primary_key: bool = False,
    ) -> dict[str, Any]:
        """Validate entity data against schema.

        Delegates to ValidationService for actual validation.

        Args:
            model_name: Model name
            data: Data to validate
            partial: Allow missing required fields
            exclude_primary_key: Exclude primary key from validation (for creation)

        Returns:
            Validated and normalized data

        Raises:
            ValidationError: If validation fails
        """
        schema = self._schemas[model_name]

        # Temporarily add primary key with dummy value if excluding it
        validation_data = data.copy()
        if exclude_primary_key and schema.primary_key not in validation_data:
            # Add a dummy value for primary key to pass validation
            validation_data[schema.primary_key] = 0

        # Delegate to validation service
        result = self._validation_service.validate(
            model_name=model_name,
            data=validation_data,
            schema=schema,
            partial=partial,
        )

        # Remove primary key if it was excluded
        if exclude_primary_key and schema.primary_key in result:
            result.pop(schema.primary_key)

        return result

    def _paginate(
        self,
        entities: list[dict[str, Any]],
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], int]:
        """Paginate entity list.

        Args:
            entities: List of entities
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (paginated_items, total_pages)
        """
        total = len(entities)
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        # Calculate start and end indices
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        # Slice the list
        paginated_items = entities[start_idx:end_idx]

        return (paginated_items, total_pages)

    def _get_next_id(self, model_name: str) -> int:
        """Get next auto-increment ID for model.

        Thread-safe via lock.

        Args:
            model_name: Model name

        Returns:
            Next available ID
        """
        next_id = self._next_ids[model_name]
        self._next_ids[model_name] += 1
        return next_id
