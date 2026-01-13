"""Type definitions for the core module.

This module defines the data structures used throughout the core functionality
including schema representations, relationships, and field metadata.
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from dataclasses import dataclass, field
from typing import Any

# Third-party
from pydantic import BaseModel

# =============================================================================
# SCHEMA TYPES
# =============================================================================


@dataclass
class FieldSchema:
    """Schema for a single model field.

    Attributes:
        name: Field name (e.g., "email", "author_id").
        type: Python type of the field (e.g., str, int).
        is_optional: Whether the field accepts None.
        default: Default value if specified, None otherwise.
        is_foreign_key: True if field name ends with "_id" (except "id").
        related_model: Name of related model if this is a foreign key.
        is_enum: True if field type is an Enum class.
        enum_values: List of valid enum values if is_enum is True.
    """

    name: str
    type: type
    is_optional: bool
    default: Any = None
    is_foreign_key: bool = False
    related_model: str | None = None
    is_enum: bool = False
    enum_values: list[Any] = field(default_factory=lambda: [])


@dataclass
class Relationship:
    """Represents a relationship between models.

    Attributes:
        field_name: Name of the foreign key field (e.g., "author_id").
        related_model: Name of the model this references (e.g., "User").
        relationship_type: Type of relationship (e.g., "many_to_one", "one_to_many").
    """

    field_name: str
    related_model: str
    relationship_type: str


@dataclass
class ModelSchema:
    """Schema representation of a Pydantic model.

    Attributes:
        name: Model class name (e.g., "User", "Post").
        fields: List of field schemas for this model.
        relationships: List of relationships to other models.
        pydantic_model: Reference to the original Pydantic model class.
    """

    name: str
    fields: list[FieldSchema]
    relationships: list[Relationship] = field(default_factory=lambda: [])
    pydantic_model: type[BaseModel] | None = None


# =============================================================================
# STORE TYPES
# =============================================================================


@dataclass
class PaginationParams:
    """Internal pagination parameters after strategy detection.

    Attributes:
        strategy: Pagination strategy used ("page" or "offset").
        start_idx: Starting index in the data list.
        batch_size: Number of items to return (page_size or limit).
        page_num: Page number (only relevant for page strategy, 0 for offset).
    """

    strategy: str
    start_idx: int
    batch_size: int
    page_num: int


class PaginationInfo(BaseModel):
    """Pagination metadata for query results.

    Supports both page-based and offset-based pagination strategies.
    Fields are optional to support both strategies flexibly.

    Attributes:
        total_items: Total number of items across all pages.
        has_next: Whether there is a next page/batch.
        has_prev: Whether there is a previous page/batch.

        # Page-based fields (None if using offset strategy)
        page: Current page number (1-indexed).
        page_size: Number of items per page.
        total_pages: Total number of pages.

        # Offset-based fields (None if using page strategy)
        offset: Starting offset (0-indexed).
        limit: Maximum items to return.
    """

    # Common fields (always present)
    total_items: int
    has_next: bool
    has_prev: bool

    # Page-based fields (optional)
    page: int | None = None
    page_size: int | None = None
    total_pages: int | None = None

    # Offset-based fields (optional)
    offset: int | None = None
    limit: int | None = None


class QueryResult(BaseModel):
    """Result of a paginated query.

    Attributes:
        items: List of data items for the current page.
        pagination: Pagination metadata.
    """

    items: list[dict[str, Any]]
    pagination: PaginationInfo


# =============================================================================
# FILTER AND SORT TYPES
# =============================================================================


@dataclass
class FilterSpec:
    """Specification for a single filter condition.

    Attributes:
        field: Field name to filter on (e.g., "age", "name").
        operator: Filter operator enum value.
        value: Value to compare against (type-coerced).
    """

    field: str
    operator: str  # FilterOperator enum value (stored as str for serialization)
    value: Any


@dataclass
class SortSpec:
    """Specification for sorting.

    Attributes:
        field: Field name to sort by.
        direction: Sort direction ("asc" or "desc").
    """

    field: str
    direction: str


# =============================================================================
# BULK OPERATION TYPES
# =============================================================================


@dataclass
class BulkOperationError:
    """Error details for a failed bulk operation item.

    Attributes:
        index: Index of the failed item in the original batch.
        item: The data that failed to process.
        error: Error message describing the failure.
    """

    index: int
    item: dict[str, Any]
    error: str
