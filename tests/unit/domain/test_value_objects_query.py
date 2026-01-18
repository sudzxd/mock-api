"""Tests for query value objects."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Third-party
# Project/local
from mock_api.domain.value_objects.query import (
    FilterSpec,
    PaginationParams,
    QueryResult,
    SortSpec,
)


# =============================================================================
# TESTS - FilterSpec
# =============================================================================
def test_filter_spec_creation():
    """FilterSpec should be created with field, operator, and value."""
    # Arrange & Act
    filter_spec = FilterSpec(field="age", operator="gte", value=18)

    # Assert
    assert filter_spec.field == "age"
    assert filter_spec.operator == "gte"
    assert filter_spec.value == 18


def test_filter_spec_with_in_operator() -> None:
    """FilterSpec should handle 'in' operator with list values."""
    # Arrange & Act
    status_values: list[str] = ["active", "pending"]
    filter_spec = FilterSpec(field="status", operator="in", value=status_values)

    # Assert
    assert filter_spec.operator == "in"
    assert isinstance(filter_spec.value, list)
    assert len(filter_spec.value) == 2  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]


# =============================================================================
# TESTS - SortSpec
# =============================================================================
def test_sort_spec_creation_with_ascending():
    """SortSpec should be created with ascending direction."""
    # Arrange & Act
    sort_spec = SortSpec(field="name", direction="asc")

    # Assert
    assert sort_spec.field == "name"
    assert sort_spec.direction == "asc"


def test_sort_spec_creation_with_descending():
    """SortSpec should be created with descending direction."""
    # Arrange & Act
    sort_spec = SortSpec(field="created_at", direction="desc")

    # Assert
    assert sort_spec.field == "created_at"
    assert sort_spec.direction == "desc"


# =============================================================================
# TESTS - PaginationParams
# =============================================================================
def test_pagination_params_creation_with_defaults():
    """PaginationParams should be created with default values."""
    # Arrange & Act
    params = PaginationParams()

    # Assert
    assert params.page == 1
    assert params.page_size == 20


def test_pagination_params_creation_with_custom_values():
    """PaginationParams should be created with custom values."""
    # Arrange & Act
    params = PaginationParams(page=2, page_size=50)

    # Assert
    assert params.page == 2
    assert params.page_size == 50


def test_pagination_params_offset_calculation():
    """PaginationParams.offset should calculate correct offset."""
    # Arrange
    params = PaginationParams(page=3, page_size=20)

    # Act
    offset = params.offset

    # Assert
    assert offset == 40  # (3 - 1) * 20


def test_pagination_params_limit_returns_page_size():
    """PaginationParams.limit should return page_size."""
    # Arrange
    params = PaginationParams(page=1, page_size=50)

    # Act
    limit = params.limit

    # Assert
    assert limit == 50


# =============================================================================
# TESTS - QueryResult
# =============================================================================
def test_query_result_creation() -> None:
    """QueryResult should be created with all fields."""
    # Arrange
    items = ({"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"})

    # Act
    result = QueryResult(
        items=items,
        total=10,
        page=1,
        page_size=2,
        total_pages=5,
    )

    # Assert
    assert len(result.items) == 2
    assert result.total == 10
    assert result.page == 1
    assert result.page_size == 2
    assert result.total_pages == 5


def test_query_result_has_next_returns_true_when_more_pages() -> None:
    """QueryResult.has_next should return True when more pages exist."""
    # Arrange
    result = QueryResult(
        items=(),
        total=100,
        page=2,
        page_size=20,
        total_pages=5,
    )

    # Act & Assert
    assert result.has_next is True


def test_query_result_has_next_returns_false_when_last_page() -> None:
    """QueryResult.has_next should return False on last page."""
    # Arrange
    result = QueryResult(
        items=(),
        total=100,
        page=5,
        page_size=20,
        total_pages=5,
    )

    # Act & Assert
    assert result.has_next is False


def test_query_result_has_prev_returns_true_when_not_first_page() -> None:
    """QueryResult.has_prev should return True when not on first page."""
    # Arrange
    result = QueryResult(
        items=(),
        total=100,
        page=2,
        page_size=20,
        total_pages=5,
    )

    # Act & Assert
    assert result.has_prev is True


def test_query_result_has_prev_returns_false_when_first_page() -> None:
    """QueryResult.has_prev should return False on first page."""
    # Arrange
    result = QueryResult(
        items=(),
        total=100,
        page=1,
        page_size=20,
        total_pages=5,
    )

    # Act & Assert
    assert result.has_prev is False
