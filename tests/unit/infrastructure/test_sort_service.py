"""Tests for SortService."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Third-party
import pytest

# Project/local
from mock_api.core.exceptions.validation import ValidationError
from mock_api.domain.value_objects.schema import ModelSchema
from mock_api.infrastructure.services.sort_service import SortService


# =============================================================================
# TESTS - SortService
# =============================================================================
def test_sort_service_parse_simple_ascending_sort(user_schema: ModelSchema) -> None:
    """SortService should parse simple ascending sort."""
    # Arrange
    service = SortService()
    sort_param = "name"

    # Act
    sorts = service.parse(sort_param, user_schema)

    # Assert
    assert len(sorts) == 1
    assert sorts[0].field == "name"
    assert sorts[0].direction == "asc"


def test_sort_service_parse_descending_sort_with_minus(
    user_schema: ModelSchema,
) -> None:
    """SortService should parse descending sort with minus prefix."""
    # Arrange
    service = SortService()
    sort_param = "-age"

    # Act
    sorts = service.parse(sort_param, user_schema)

    # Assert
    assert len(sorts) == 1
    assert sorts[0].field == "age"
    assert sorts[0].direction == "desc"


def test_sort_service_parse_multiple_sorts(user_schema: ModelSchema) -> None:
    """SortService should parse multiple sort fields."""
    # Arrange
    service = SortService()
    sort_param = "name,-age"

    # Act
    sorts = service.parse(sort_param, user_schema)

    # Assert
    assert len(sorts) == 2
    assert sorts[0].field == "name"
    assert sorts[0].direction == "asc"
    assert sorts[1].field == "age"
    assert sorts[1].direction == "desc"


def test_sort_service_parse_empty_string_returns_empty_list(
    user_schema: ModelSchema,
) -> None:
    """SortService should return empty list for empty string."""
    # Arrange
    service = SortService()
    sort_param = ""

    # Act
    sorts = service.parse(sort_param, user_schema)

    # Assert
    assert len(sorts) == 0


def test_sort_service_parse_none_returns_empty_list(user_schema: ModelSchema) -> None:
    """SortService should return empty list for None."""
    # Arrange
    service = SortService()
    sort_param = None

    # Act
    sorts = service.parse(sort_param, user_schema)

    # Assert
    assert len(sorts) == 0


def test_sort_service_validate_sort_with_valid_field(user_schema: ModelSchema) -> None:
    """SortService.validate_sort() should pass with valid field."""
    # Arrange
    service = SortService()
    from mock_api.domain.value_objects.query import SortSpec

    sort_spec = SortSpec(field="name", direction="asc")

    # Act & Assert (should not raise)
    service.validate_sort(sort_spec, user_schema)


def test_sort_service_validate_sort_raises_error_with_invalid_field(
    user_schema: ModelSchema,
) -> None:
    """SortService.validate_sort() should raise error with invalid field."""
    # Arrange
    service = SortService()
    from mock_api.domain.value_objects.query import SortSpec

    sort_spec = SortSpec(field="invalid_field", direction="asc")

    # Act & Assert
    with pytest.raises(ValidationError):
        service.validate_sort(sort_spec, user_schema)


def test_sort_service_parse_ignores_empty_segments(user_schema: ModelSchema) -> None:
    """SortService should ignore empty segments in comma-separated list."""
    # Arrange
    service = SortService()
    sort_param = "name,,age"

    # Act
    sorts = service.parse(sort_param, user_schema)

    # Assert
    assert len(sorts) == 2
    assert sorts[0].field == "name"
    assert sorts[1].field == "age"
