"""Query value objects - immutable query specifications."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Generic, TypeVar

# =============================================================================
# TYPES & CONSTANTS
# =============================================================================
T_co = TypeVar("T_co", covariant=True)

# Domain constants (no external dependencies)
MAX_PAGE_SIZE = 100


class FilterOperator(StrEnum):
    """Filter operators for query filtering."""

    EQ = "eq"  # Equal
    NE = "ne"  # Not equal
    GT = "gt"  # Greater than
    GTE = "gte"  # Greater than or equal
    LT = "lt"  # Less than
    LTE = "lte"  # Less than or equal
    IN = "in"  # In list
    NIN = "nin"  # Not in list
    CONTAINS = "contains"  # String contains


class SortDirection(StrEnum):
    """Sort direction for query sorting."""

    ASC = "asc"
    DESC = "desc"


# Type aliases
EntityDict = dict[str, Any]
QueryParams = dict[str, Any]


# =============================================================================
# CORE CLASSES
# =============================================================================
@dataclass(frozen=True)
class FilterSpec:
    """Immutable filter specification.

    Represents a single filter condition (field, operator, value).
    """

    field: str
    operator: str  # eq, ne, gt, gte, lt, lte, in, nin, contains, etc.
    value: Any

    def __post_init__(self) -> None:
        """Validate filter specification.

        Raises:
            ValueError: If operator is invalid
        """
        # Validate operator is a valid FilterOperator value
        try:
            FilterOperator(self.operator)
        except ValueError as e:
            valid_ops = ", ".join([op.value for op in FilterOperator])
            raise ValueError(
                f"Invalid filter operator '{self.operator}'. "
                f"Valid operators are: {valid_ops}"
            ) from e


@dataclass(frozen=True)
class SortSpec:
    """Immutable sort specification.

    Represents a single sort directive (field, direction).
    """

    field: str
    direction: str  # asc, desc

    def __post_init__(self) -> None:
        """Validate sort specification.

        Raises:
            ValueError: If direction is invalid
        """
        # Validate direction is a valid SortDirection value
        try:
            SortDirection(self.direction)
        except ValueError as e:
            valid_dirs = ", ".join([d.value for d in SortDirection])
            raise ValueError(
                f"Invalid sort direction '{self.direction}'. "
                f"Valid directions are: {valid_dirs}"
            ) from e


@dataclass(frozen=True)
class PaginationParams:
    """Immutable pagination parameters.

    Represents pagination configuration for list queries.
    """

    page: int = 1
    page_size: int = 20

    def __post_init__(self) -> None:
        """Validate pagination parameters.

        Raises:
            ValueError: If pagination parameters are invalid
        """
        # Validate page >= 1
        if self.page < 1:
            raise ValueError(f"Page must be >= 1, got {self.page}")

        # Validate page_size >= 1 and <= MAX_PAGE_SIZE
        if self.page_size < 1:
            raise ValueError(f"Page size must be >= 1, got {self.page_size}")
        if self.page_size > MAX_PAGE_SIZE:
            raise ValueError(
                f"Page size must be <= {MAX_PAGE_SIZE}, got {self.page_size}"
            )

    @property
    def offset(self) -> int:
        """Calculate offset from page and page_size.

        Returns:
            Offset for database queries
        """
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit (alias for page_size).

        Returns:
            Number of items per page
        """
        return self.page_size


@dataclass(frozen=True)
class QueryResult(Generic[T_co]):
    """Immutable query result with pagination metadata.

    Generic container for paginated query results.
    """

    items: tuple[T_co, ...]
    total: int
    page: int
    page_size: int
    total_pages: int

    def __post_init__(self) -> None:
        """Validate query result.

        Raises:
            ValueError: If query result is inconsistent
        """
        # Validate consistency
        if self.total < 0:
            raise ValueError(f"Total must be >= 0, got {self.total}")
        if self.page < 1:
            raise ValueError(f"Page must be >= 1, got {self.page}")
        if self.page_size < 1:
            raise ValueError(f"Page size must be >= 1, got {self.page_size}")
        if self.total_pages < 0:
            raise ValueError(f"Total pages must be >= 0, got {self.total_pages}")

        # Validate items count is consistent with page_size (except for last page)
        if len(self.items) > self.page_size:
            raise ValueError(
                f"Items count ({len(self.items)}) cannot exceed "
                f"page_size ({self.page_size})"
            )

    @property
    def has_next(self) -> bool:
        """Check if there is a next page.

        Returns:
            True if next page exists
        """
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        """Check if there is a previous page.

        Returns:
            True if previous page exists
        """
        return self.page > 1
