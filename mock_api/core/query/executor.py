"""Query executor for in-memory data filtering, sorting, and pagination.

This module provides the MemoryQueryExecutor class which implements the IQueryExecutor
protocol for in-memory query operations.
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
import math
from collections.abc import Callable
from typing import Any

# Project/local
from ...utils.logger import get_logger
from ..constants import (
    DEFAULT_LIMIT,
    DEFAULT_OFFSET,
    DEFAULT_PAGE_NUMBER,
    DEFAULT_PAGE_SIZE,
    MAX_LIMIT,
    MAX_PAGE_SIZE,
    MIN_LIMIT,
    MIN_PAGE_SIZE,
    FilterOperator,
    SortDirection,
)
from ..exceptions import StoreError
from ..types import FilterSpec, PaginationInfo, PaginationParams, QueryResult, SortSpec

# =============================================================================
# TYPES & CONSTANTS
# =============================================================================
logger = get_logger(__name__)

# =============================================================================
# PUBLIC API
# =============================================================================


class MemoryQueryExecutor:
    """In-memory query executor with filtering, sorting, and pagination.

    Internal implementation detail used by InMemoryRepository.
    Not part of the public protocol - each repository can use its own
    query optimization strategy.

    Provides optimized query operations for in-memory data:
    - Filtering with multiple operators (eq, gt, gte, lt, lte, contains, etc.)
    - Sorting with multiple fields and directions
    - Pagination (both page-based and offset-based)

    Performance Characteristics:
    - Without filter/sort: O(k) where k is page size/limit
    - With filter: O(n) where n is total instances
    - With sort: O(n log n) where n is filtered instances

    Example:
        >>> executor = MemoryQueryExecutor()
        >>> items = [{"id": 1, "name": "Alice", "age": 30}, ...]
        >>> result = executor.execute_query(
        ...     "User", items,
        ...     filters=[FilterSpec(field="age", operator="gte", value=18)],
        ...     page=1, page_size=10
        ... )
        >>> len(result.items)
        10
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

    def execute_query(
        self,
        model_name: str,
        items: list[dict[str, Any]],
        filters: list[FilterSpec] | None = None,
        sort_by: list[SortSpec] | None = None,
        page: int | None = None,
        page_size: int | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> QueryResult:
        """Execute a query with filtering, sorting, and pagination.

        Supports both page-based and offset-based pagination. Strategy is
        auto-detected based on which parameters are provided.

        Args:
            model_name: Name of the model being queried.
            items: List of items to query.
            filters: Optional list of filter specifications (AND logic).
            sort_by: Optional list of sort specifications.
            page: Page number (1-indexed) for page-based pagination.
            page_size: Number of items per page.
            offset: Starting offset (0-indexed) for offset-based pagination.
            limit: Maximum items to return.

        Returns:
            QueryResult with filtered, sorted, paginated items and metadata.

        Raises:
            StoreError: If pagination parameters are invalid or conflicting.

        Time Complexity:
        - Without filter/sort: O(k) where k is page size/limit
        - With filter: O(n) where n is total instances
        - With sort: O(n log n) where n is filtered instances

        Example:
            # Page-based with filtering
            >>> result = executor.execute_query("User", items, page=1, page_size=10,
            ...     filters=[FilterSpec(field="age", operator="gte", value=18)])

            # Offset-based with sorting
            >>> result = executor.execute_query("User", items, offset=0, limit=10,
            ...     sort_by=[SortSpec(field="created_at", direction="desc")])
        """
        # Detect strategy and validate parameters
        params = self._detect_pagination_strategy(page, page_size, offset, limit)

        # Apply filters
        filtered_items = items
        if filters:
            filtered_items = self._apply_filters(filtered_items, filters)

        # Apply sorting before pagination
        if sort_by:
            filtered_items = self._apply_sorting(filtered_items, sort_by)

        # Calculate pagination based on strategy
        total_items = len(filtered_items)

        # Get slice - O(k) where k is batch_size
        end_idx = params.start_idx + params.batch_size
        batch_items = filtered_items[params.start_idx : end_idx]

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

        return QueryResult(items=batch_items, pagination=pagination)

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
