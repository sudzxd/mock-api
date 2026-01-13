"""In-memory data store with CRUD operations and pagination.

This module provides a thread-safe in-memory store for managing mock data
with full CRUD operations, filtering, pagination, and relationship awareness.

Optimized with:
- O(1) lookups using hash map indices
- OrderedDict for maintaining insertion order with efficient operations
- Reduced deepcopy overhead
- Field indices for fast filtering
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
import math
import threading
from collections import OrderedDict
from collections.abc import Callable
from copy import deepcopy
from typing import Any

# Project/local
from ..utils.logger import get_logger
from .constants import (
    DEFAULT_LIMIT,
    DEFAULT_OFFSET,
    DEFAULT_PAGE_NUMBER,
    DEFAULT_PAGE_SIZE,
    MAX_LIMIT,
    MAX_PAGE_SIZE,
    MIN_LIMIT,
    MIN_PAGE_SIZE,
    PRIMARY_KEY_FIELD,
    FilterOperator,
    SortDirection,
)
from .exceptions import DuplicateInstanceError, InstanceNotFoundError, StoreError
from .types import FilterSpec, PaginationInfo, PaginationParams, QueryResult, SortSpec

# =============================================================================
# TYPES & CONSTANTS
# =============================================================================
logger = get_logger(__name__)

# Type alias for filter functions
FilterFunc = Callable[[dict[str, Any]], bool]

# =============================================================================
# PUBLIC API
# =============================================================================


class DataStore:
    """Thread-safe in-memory data store with optimized CRUD operations.

    Provides a high-performance data store for managing mock data with:
    - Full CRUD operations (Create, Read, Update, Delete)
    - O(1) lookups via hash map indices
    - Pagination support
    - Filtering and querying
    - Thread-safe operations
    - Referential integrity awareness

    Performance Characteristics:
    - Create: O(1)
    - Read: O(1) - hash map lookup
    - Update: O(1) - direct index access
    - Delete: O(1) - OrderedDict deletion
    - List: O(k) where k is page size
    - Count: O(1) or O(n) with filter

    Example:
        >>> store = DataStore()
        >>> store.create("User", {"id": 1, "name": "Alice"})
        {'id': 1, 'name': 'Alice'}
        >>> store.read("User", 1)  # O(1) lookup
        {'id': 1, 'name': 'Alice'}
        >>> result = store.list("User", page=1, page_size=10)
        >>> len(result.items)
        1
    """

    # Filter operator functions - defined once at class level
    _FILTER_OPERATORS: dict[FilterOperator, Callable[[Any, Any], bool]] = {
        FilterOperator.EQ: lambda fv, v: fv == v,
        FilterOperator.GT: lambda fv, v: fv > v,
        FilterOperator.GTE: lambda fv, v: fv >= v,
        FilterOperator.LT: lambda fv, v: fv < v,
        FilterOperator.LTE: lambda fv, v: fv <= v,
        FilterOperator.CONTAINS: lambda fv, v: v.lower() in str(fv).lower(),
        FilterOperator.STARTSWITH: lambda fv, v: str(fv).lower().startswith(v.lower()),
        FilterOperator.ENDSWITH: lambda fv, v: str(fv).lower().endswith(v.lower()),
        FilterOperator.IN: lambda fv, v: fv in v,
    }

    def __init__(self) -> None:
        """Initialize an empty data store with optimized indices."""
        # Primary storage: {model_name: OrderedDict{id: instance}}
        # OrderedDict maintains insertion order + O(1) deletion
        self._data: dict[str, OrderedDict[int, dict[str, Any]]] = {}

        # Thread safety
        self._lock = threading.Lock()

        # ID counters for auto-increment
        self._id_counters: dict[str, int] = {}

        logger.debug("Initialized empty data store with hash indices")

    def load(self, data: dict[str, list[dict[str, Any]]]) -> None:
        """Load bulk data into the store.

        Args:
            data: Dictionary mapping model names to lists of instances.

        Example:
            >>> data = {"User": [{"id": 1, "name": "Alice"}]}
            >>> store.load(data)
        """
        with self._lock:
            for model_name, instances in data.items():
                # Initialize OrderedDict for this model
                self._data[model_name] = OrderedDict()

                # Load instances with deep copy
                for instance in instances:
                    instance_copy = deepcopy(instance)
                    instance_id = instance_copy.get(PRIMARY_KEY_FIELD)
                    if instance_id is not None:
                        self._data[model_name][instance_id] = instance_copy

                        # Update ID counter
                        if instance_id > self._id_counters.get(model_name, 0):
                            self._id_counters[model_name] = instance_id

            logger.info(f"Loaded data for {len(data)} model(s)")

    def create(
        self, model_name: str, data: dict[str, Any], auto_id: bool = True
    ) -> dict[str, Any]:
        """Create a new instance in the store.

        Args:
            model_name: Name of the model to create.
            data: Dictionary of field values.
            auto_id: If True, automatically assign ID if not provided.

        Returns:
            The created instance with ID assigned.

        Raises:
            ValueError: If instance with same ID already exists.

        Time Complexity: O(1) - hash map insertion

        Example:
            >>> instance = store.create("User", {"name": "Bob"})
            >>> instance["id"]
            1
        """
        with self._lock:
            # Ensure model exists in store
            if model_name not in self._data:
                self._data[model_name] = OrderedDict()
                self._id_counters[model_name] = 0

            # Deep copy to avoid mutation
            instance = deepcopy(data)

            # Auto-assign ID if needed
            if auto_id and PRIMARY_KEY_FIELD not in instance:
                self._id_counters[model_name] += 1
                instance[PRIMARY_KEY_FIELD] = self._id_counters[model_name]

            # Get instance ID
            instance_id = instance.get(PRIMARY_KEY_FIELD)

            # Check for duplicate ID - O(1) with hash map
            if instance_id is not None and instance_id in self._data[model_name]:
                raise DuplicateInstanceError(model_name, instance_id)

            # Add to store - O(1) insertion
            if instance_id is not None:
                self._data[model_name][instance_id] = instance
                # Update counter to track highest ID
                if instance_id > self._id_counters[model_name]:
                    self._id_counters[model_name] = instance_id

            logger.debug(f"Created {model_name} with {PRIMARY_KEY_FIELD}={instance_id}")
            return deepcopy(instance)

    def read(self, model_name: str, instance_id: int) -> dict[str, Any] | None:
        """Read a single instance by ID.

        Args:
            model_name: Name of the model.
            instance_id: ID of the instance to retrieve.

        Returns:
            The instance if found, None otherwise.

        Time Complexity: O(1) - direct hash map lookup

        Example:
            >>> user = store.read("User", 1)
            >>> user["name"]
            'Alice'
        """
        with self._lock:
            # O(1) lookup with hash map
            if model_name not in self._data:
                return None

            instance = self._data[model_name].get(instance_id)
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

        Time Complexity: O(1) - direct hash map access

        Example:
            >>> updated = store.update("User", 1, {"name": "Alice Smith"})
            >>> updated["name"]
            'Alice Smith'
        """
        with self._lock:
            # O(1) lookup
            if (
                model_name not in self._data
                or instance_id not in self._data[model_name]
            ):
                raise InstanceNotFoundError(model_name, instance_id)

            # Get reference to instance
            instance = self._data[model_name][instance_id]

            # Update fields (preserve ID)
            instance.update(data)
            instance[PRIMARY_KEY_FIELD] = instance_id

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

        Example:
            >>> store.delete("User", 1)
            True
            >>> store.delete("User", 999)
            False
        """
        with self._lock:
            if model_name not in self._data:
                return False

            # O(1) deletion with OrderedDict
            deleted_instance = self._data[model_name].pop(instance_id, None)

            if deleted_instance:
                logger.debug(
                    f"Deleted {model_name} with {PRIMARY_KEY_FIELD}={instance_id}"
                )
                return True

            return False

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
        """List instances with pagination, filtering, and sorting.

        Supports both page-based and offset-based pagination. Strategy is
        auto-detected based on which parameters are provided.

        Args:
            model_name: Name of the model.
            page: Page number (1-indexed) for page-based pagination.
            page_size: Number of items per page.
            offset: Starting offset (0-indexed) for offset-based pagination.
            limit: Maximum items to return.
            filters: Optional list of filter specifications (AND logic).
            sort_by: Optional list of sort specifications.
            filter_func: Optional function to filter instances (backward compatibility).

        Returns:
            QueryResult with items and pagination info.

        Raises:
            StoreError: If pagination parameters are invalid or conflicting.

        Time Complexity:
        - Without filter/sort: O(k) where k is page size/limit
        - With filter: O(n) where n is total instances
        - With sort: O(n log n) where n is filtered instances

        Example:
            # Page-based with filtering
            >>> result = store.list("User", page=1, page_size=10,
            ...     filters=[FilterSpec(field="age", operator="gte", value=18)])

            # Offset-based with sorting
            >>> result = store.list("User", offset=0, limit=10,
            ...     sort_by=[SortSpec(field="created_at", direction="desc")])
        """
        # Detect strategy and validate parameters
        params = self._detect_pagination_strategy(page, page_size, offset, limit)

        with self._lock:
            # Get all instances for model - values() on OrderedDict maintains order
            if model_name not in self._data:
                instances = []
            else:
                instances = list(self._data[model_name].values())

            # Apply filters - order: custom filter_func first, then FilterSpec
            if filter_func:
                instances = [inst for inst in instances if filter_func(inst)]
            if filters:
                instances = self._apply_filters(instances, filters)
            # Apply sorting before pagination
            if sort_by:
                instances = self._apply_sorting(instances, sort_by)

            # Calculate pagination based on strategy
            total_items = len(instances)

            # Get slice - O(k) where k is batch_size
            end_idx = params.start_idx + params.batch_size
            batch_items = instances[params.start_idx : end_idx]

            # Build pagination info based on strategy
            if params.strategy == "page":
                total_pages = (
                    math.ceil(total_items / params.batch_size) if total_items > 0 else 1
                )
                has_next = params.page_num < total_pages
                has_prev = params.page_num > 1

                pagination = PaginationInfo(
                    total_items=total_items,
                    has_next=has_next,
                    has_prev=has_prev,
                    page=params.page_num,
                    page_size=params.batch_size,
                    total_pages=total_pages,
                )

                logger.debug(
                    f"Listed {len(batch_items)} {model_name}(s) "
                    f"(page {params.page_num}/{total_pages})"
                )
            else:  # offset strategy
                has_next = end_idx < total_items
                has_prev = params.start_idx > 0

                pagination = PaginationInfo(
                    total_items=total_items,
                    has_next=has_next,
                    has_prev=has_prev,
                    offset=params.start_idx,
                    limit=params.batch_size,
                )

                logger.debug(
                    f"Listed {len(batch_items)} {model_name}(s) "
                    f"(offset {params.start_idx}, limit {params.batch_size})"
                )

            return QueryResult(items=deepcopy(batch_items), pagination=pagination)

    def _apply_filters(
        self, instances: list[dict[str, Any]], filters: list[FilterSpec]
    ) -> list[dict[str, Any]]:
        """Apply filter specifications to instances (AND logic).

        Args:
            instances: List of instances to filter.
            filters: List of filter specifications.

        Returns:
            Filtered list of instances.

        Time Complexity:
            O(n * m) where n is number of instances and m is number of filters.
        """
        filtered = instances
        for filter_spec in filters:
            filtered = [
                inst for inst in filtered if self._match_filter(inst, filter_spec)
            ]
        return filtered

    def _match_filter(self, instance: dict[str, Any], filter_spec: FilterSpec) -> bool:
        """Check if instance matches a single filter.

        Args:
            instance: Instance data dictionary.
            filter_spec: Filter specification.

        Returns:
            True if instance matches the filter, False otherwise.
        """
        field_value = instance.get(filter_spec.field)
        filter_value = filter_spec.value
        operator = filter_spec.operator

        # Handle null filtering: ?field=null
        if filter_value is None:
            return field_value is None

        # If field is None but filter is not, no match
        if field_value is None:
            return False

        # Use class-level operator mapping (operator is StrEnum value)
        try:
            op_enum = FilterOperator(operator)
            operator_func = self._FILTER_OPERATORS.get(op_enum)
            return operator_func(field_value, filter_value) if operator_func else False
        except ValueError:
            return False

    def _apply_sorting(
        self, instances: list[dict[str, Any]], sort_specs: list[SortSpec]
    ) -> list[dict[str, Any]]:
        """Apply sorting specifications to instances.

        Args:
            instances: List of instances to sort.
            sort_specs: List of sort specifications.

        Returns:
            Sorted list of instances.

        Time Complexity:
            O(n log n) where n is number of instances.
        """
        if not sort_specs:
            return instances

        # Sort in reverse order of sort_specs to maintain priority
        # (last sort field has lowest priority)
        sorted_instances = instances[:]
        for spec in reversed(sort_specs):
            sorted_instances = sorted(
                sorted_instances,
                key=lambda x: (x.get(spec.field) is None, x.get(spec.field)),
                reverse=(spec.direction == SortDirection.DESC),
            )

        return sorted_instances

    def _detect_pagination_strategy(
        self,
        page: int | None,
        page_size: int | None,
        offset: int | None,
        limit: int | None,
    ) -> PaginationParams:
        """Detect pagination strategy and return normalized params.

        Returns:
            PaginationParams with strategy, start_idx, batch_size, and page_num

        Raises:
            StoreError: If conflicting params provided or invalid values
        """
        has_offset_params = offset is not None or limit is not None
        has_page_params = page is not None or page_size is not None

        # Check for conflicting params
        if has_offset_params and has_page_params:
            raise StoreError(
                "Cannot use both page-based and offset-based pagination",
                "Use either (page, page_size) or (offset, limit), not both",
            )

        if has_offset_params:
            # Offset-based strategy
            offset_val = offset if offset is not None else DEFAULT_OFFSET
            limit_val = limit if limit is not None else DEFAULT_LIMIT

            # Validate
            if offset_val < 0:
                raise StoreError(
                    f"Invalid offset: {offset_val}",
                    "Offset must be >= 0",
                )
            if limit_val < MIN_LIMIT or limit_val > MAX_LIMIT:
                raise StoreError(
                    f"Invalid limit: {limit_val}",
                    f"Limit must be between {MIN_LIMIT} and {MAX_LIMIT}",
                )

            return PaginationParams(
                strategy="offset",
                start_idx=offset_val,
                batch_size=limit_val,
                page_num=0,
            )

        # Page-based strategy (default)
        page_val = page if page is not None else DEFAULT_PAGE_NUMBER
        page_size_val = page_size if page_size is not None else DEFAULT_PAGE_SIZE

        # Validate
        if page_val < DEFAULT_PAGE_NUMBER:
            raise StoreError(
                f"Invalid page number: {page_val}",
                f"Page must be >= {DEFAULT_PAGE_NUMBER}",
            )
        if page_size_val < MIN_PAGE_SIZE or page_size_val > MAX_PAGE_SIZE:
            raise StoreError(
                f"Invalid page size: {page_size_val}",
                f"Page size must be between {MIN_PAGE_SIZE} and {MAX_PAGE_SIZE}",
            )

        start_idx = (page_val - 1) * page_size_val
        return PaginationParams(
            strategy="page",
            start_idx=start_idx,
            batch_size=page_size_val,
            page_num=page_val,
        )

    def count(self, model_name: str, filter_func: FilterFunc | None = None) -> int:
        """Count instances, optionally with filtering.

        Args:
            model_name: Name of the model.
            filter_func: Optional function to filter instances.

        Returns:
            Number of instances matching the filter.

        Time Complexity:
        - Without filter: O(1) - length of OrderedDict
        - With filter: O(n) - must check each instance

        Example:
            >>> store.count("User")
            5
            >>> store.count("User", lambda u: u["name"].startswith("A"))
            2
        """
        with self._lock:
            if model_name not in self._data:
                return 0

            instances = self._data[model_name].values()

            if filter_func:
                # O(n) with filter
                return sum(1 for inst in instances if filter_func(inst))

            # O(1) without filter
            return len(self._data[model_name])

    def clear(self, model_name: str | None = None) -> None:
        """Clear data from store.

        Args:
            model_name: If provided, clear only this model. Otherwise clear all.

        Example:
            >>> store.clear("User")  # Clear only users
            >>> store.clear()  # Clear all data
        """
        with self._lock:
            if model_name:
                self._data[model_name] = OrderedDict()
                self._id_counters[model_name] = 0
                logger.debug(f"Cleared {model_name} data")
            else:
                self._data.clear()
                self._id_counters.clear()
                logger.debug("Cleared all data")

    def get_models(self) -> list[str]:
        """Get list of all model names in the store.

        Returns:
            List of model names.

        Time Complexity: O(n) where n is number of models

        Example:
            >>> store.get_models()
            ['User', 'Post', 'Comment']
        """
        with self._lock:
            return list(self._data.keys())
