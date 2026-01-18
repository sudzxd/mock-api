"""Tests for FilterService."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Third-party
import pytest

# Project/local
from mock_api.core.exceptions.validation import ValidationError
from mock_api.domain.value_objects.schema import ModelSchema
from mock_api.infrastructure.services.filter_service import FilterService


# =============================================================================
# TESTS - FilterService
# =============================================================================
def test_filter_service_parse_simple_filter(user_schema: ModelSchema) -> None:
    """FilterService should parse simple equality filter."""
    # Arrange
    service = FilterService()
    query_params = {"name": "Alice"}

    # Act
    filters = service.parse(query_params, user_schema)

    # Assert
    assert len(filters) == 1
    assert filters[0].field == "name"
    assert filters[0].operator == "eq"
    assert filters[0].value == "Alice"


def test_filter_service_parse_filter_with_operator(user_schema: ModelSchema) -> None:
    """FilterService should parse filter with operator suffix."""
    # Arrange
    service = FilterService()
    query_params = {"age__gte": "30"}

    # Act
    filters = service.parse(query_params, user_schema)

    # Assert
    assert len(filters) == 1
    assert filters[0].field == "age"
    assert filters[0].operator == "gte"
    assert filters[0].value == 30  # Converted to int


def test_filter_service_parse_multiple_filters(user_schema: ModelSchema) -> None:
    """FilterService should parse multiple filters."""
    # Arrange
    service = FilterService()
    query_params = {"name": "Alice", "age__gte": "30"}

    # Act
    filters = service.parse(query_params, user_schema)

    # Assert
    assert len(filters) == 2
    assert filters[0].field == "name"
    assert filters[1].field == "age"


def test_filter_service_skip_pagination_params(user_schema: ModelSchema) -> None:
    """FilterService should skip pagination parameters."""
    # Arrange
    service = FilterService()
    query_params = {"name": "Alice", "page": "1", "page_size": "20", "sort": "name"}

    # Act
    filters = service.parse(query_params, user_schema)

    # Assert
    assert len(filters) == 1
    assert filters[0].field == "name"


def test_filter_service_parse_in_operator_with_comma_separated_values(
    user_schema: ModelSchema,
) -> None:
    """FilterService should parse 'in' operator with comma-separated values."""
    # Arrange
    service = FilterService()
    query_params = {"age__in": "25,30,35"}

    # Act
    filters = service.parse(query_params, user_schema)

    # Assert
    assert len(filters) == 1
    assert filters[0].operator == "in"
    assert filters[0].value == ["25", "30", "35"]


def test_filter_service_raises_error_with_invalid_field(
    user_schema: ModelSchema,
) -> None:
    """FilterService should raise ValidationError for invalid field."""
    # Arrange
    service = FilterService()
    query_params = {"invalid_field": "value"}

    # Act & Assert
    with pytest.raises(ValidationError):
        service.parse(query_params, user_schema)


def test_filter_service_validate_filter_with_valid_field(
    user_schema: ModelSchema,
) -> None:
    """FilterService.validate_filter() should pass with valid field."""
    # Arrange
    service = FilterService()
    from mock_api.domain.value_objects.query import FilterSpec

    filter_spec = FilterSpec(field="name", operator="eq", value="Alice")

    # Act & Assert (should not raise)
    service.validate_filter(filter_spec, user_schema)


def test_filter_service_validate_filter_raises_error_with_invalid_field(
    user_schema: ModelSchema,
) -> None:
    """FilterService.validate_filter() should raise error with invalid field."""
    # Arrange
    service = FilterService()
    from mock_api.domain.value_objects.query import FilterSpec

    filter_spec = FilterSpec(field="invalid", operator="eq", value="value")

    # Act & Assert
    with pytest.raises(ValidationError):
        service.validate_filter(filter_spec, user_schema)


@pytest.mark.parametrize(
    "operator",
    ["eq", "ne", "gt", "gte", "lt", "lte", "in", "nin", "contains"],
)
def test_filter_service_supports_all_operators(
    user_schema: ModelSchema, operator: str
) -> None:
    """FilterService should support all standard operators."""
    # Arrange
    service = FilterService()
    from mock_api.domain.value_objects.query import FilterSpec

    filter_spec = FilterSpec(field="name", operator=operator, value="test")

    # Act & Assert (should not raise)
    service.validate_filter(filter_spec, user_schema)
