"""Tests for FilterParser service.

Comprehensive test coverage for filter parameter parsing, validation,
and type coercion functionality.
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard Library
from datetime import date, datetime
from enum import Enum

# Third Party
import pytest
from fastapi import HTTPException

# Project/Local
from mock_api.core.config import Config, FilterSortConfig
from mock_api.core.constants import FilterOperator
from mock_api.core.services import FilterParser
from mock_api.core.types import FieldSchema, ModelSchema
from starlette.datastructures import QueryParams

# =============================================================================
# TEST FIXTURES
# =============================================================================


class Priority(int, Enum):
    """Test enum - int based."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Status(str, Enum):
    """Test enum - str based."""

    ACTIVE = "active"
    INACTIVE = "inactive"


@pytest.fixture
def filter_parser() -> FilterParser:
    """Create FilterParser instance."""
    return FilterParser()


@pytest.fixture
def user_schema() -> ModelSchema:
    """Create a User model schema for testing."""
    return ModelSchema(
        name="User",
        fields=[
            FieldSchema(name="id", type=int, is_optional=False),
            FieldSchema(name="name", type=str, is_optional=False),
            FieldSchema(name="age", type=int, is_optional=False),
            FieldSchema(name="email", type=str, is_optional=False),
            FieldSchema(name="is_active", type=bool, is_optional=False),
            FieldSchema(name="score", type=float, is_optional=False),
            FieldSchema(name="bio", type=str, is_optional=True),
        ],
    )


@pytest.fixture
def product_schema() -> ModelSchema:
    """Create a Product model schema with enums."""
    return ModelSchema(
        name="Product",
        fields=[
            FieldSchema(name="id", type=int, is_optional=False),
            FieldSchema(name="name", type=str, is_optional=False),
            FieldSchema(
                name="priority",
                type=Priority,
                is_optional=False,
                is_enum=True,
                enum_values=[1, 2, 3],
            ),
            FieldSchema(
                name="status",
                type=Status,
                is_optional=False,
                is_enum=True,
                enum_values=["active", "inactive"],
            ),
        ],
    )


@pytest.fixture
def event_schema() -> ModelSchema:
    """Create an Event model schema with datetime fields."""
    return ModelSchema(
        name="Event",
        fields=[
            FieldSchema(name="id", type=int, is_optional=False),
            FieldSchema(name="title", type=str, is_optional=False),
            FieldSchema(name="created_at", type=datetime, is_optional=False),
            FieldSchema(name="event_date", type=date, is_optional=False),
        ],
    )


# =============================================================================
# TEST: parse_params()
# =============================================================================


def test_parse_params_single_filter(
    filter_parser: FilterParser, user_schema: ModelSchema
) -> None:
    """Test parsing a single filter parameter."""
    query_params = QueryParams({"age__gte": "18"})
    filters = filter_parser.parse_params(query_params, "User", user_schema)

    assert len(filters) == 1
    assert filters[0].field == "age"
    assert filters[0].operator == FilterOperator.GTE
    assert filters[0].value == 18


def test_parse_params_multiple_filters(
    filter_parser: FilterParser, user_schema: ModelSchema
) -> None:
    """Test parsing multiple filter parameters."""
    query_params = QueryParams(
        {"age__gte": "18", "name__contains": "John", "is_active": "true"}
    )
    filters = filter_parser.parse_params(query_params, "User", user_schema)

    assert len(filters) == 3
    assert filters[0].field == "age"
    assert filters[1].field == "name"
    assert filters[2].field == "is_active"


def test_parse_params_ignores_reserved_params(
    filter_parser: FilterParser, user_schema: ModelSchema
) -> None:
    """Test that pagination/sort params are ignored."""
    query_params = QueryParams(
        {
            "age__gte": "18",
            "page": "1",
            "page_size": "20",
            "offset": "0",
            "limit": "10",
            "sort": "name",
        }
    )
    filters = filter_parser.parse_params(query_params, "User", user_schema)

    # Only age filter, pagination/sort params ignored
    assert len(filters) == 1
    assert filters[0].field == "age"


def test_parse_params_too_many_filters(
    filter_parser: FilterParser, user_schema: ModelSchema
) -> None:
    """Test that too many filters raises HTTPException."""
    # Create 11 valid filters using existing fields (default max is 10)
    params = {
        "name": "John",
        "age__gte": "18",
        "age__lte": "65",
        "email__contains": "test",
        "is_active": "true",
        "score__gt": "5.0",
        "id__gte": "1",
        "bio__contains": "test",
        "name__startswith": "J",
        "email__endswith": ".com",
        "age": "25",  # 11th filter
    }
    query_params = QueryParams(params)

    with pytest.raises(HTTPException) as exc_info:
        filter_parser.parse_params(query_params, "User", user_schema)

    assert exc_info.value.status_code == 400
    assert "Too many filters" in exc_info.value.detail


def test_parse_params_empty(
    filter_parser: FilterParser, user_schema: ModelSchema
) -> None:
    """Test parsing with no filter parameters."""
    query_params = QueryParams({})
    filters = filter_parser.parse_params(query_params, "User", user_schema)

    assert len(filters) == 0


# =============================================================================
# TEST: parse_single()
# =============================================================================


def test_parse_single_with_operator(
    filter_parser: FilterParser, user_schema: ModelSchema
) -> None:
    """Test parsing field__operator=value format."""
    filter_spec = filter_parser.parse_single("age__gte", "18", "User", user_schema)

    assert filter_spec.field == "age"
    assert filter_spec.operator == FilterOperator.GTE
    assert filter_spec.value == 18


def test_parse_single_without_operator_implicit_eq(
    filter_parser: FilterParser, user_schema: ModelSchema
) -> None:
    """Test parsing field=value format (implicit eq operator)."""
    filter_spec = filter_parser.parse_single("name", "John", "User", user_schema)

    assert filter_spec.field == "name"
    assert filter_spec.operator == FilterOperator.EQ
    assert filter_spec.value == "John"


def test_parse_single_invalid_value(
    filter_parser: FilterParser, user_schema: ModelSchema
) -> None:
    """Test that invalid value raises HTTPException."""
    with pytest.raises(HTTPException) as exc_info:
        filter_parser.parse_single("age__gte", "not_a_number", "User", user_schema)

    assert exc_info.value.status_code == 400
    assert "Invalid value for age" in exc_info.value.detail


# =============================================================================
# TEST: validate_field()
# =============================================================================


def test_validate_field_valid(
    filter_parser: FilterParser, user_schema: ModelSchema
) -> None:
    """Test validating an existing field."""
    field_schema = filter_parser.validate_field("age", "User", user_schema)

    assert field_schema.name == "age"
    assert field_schema.type is int


def test_validate_field_invalid(
    filter_parser: FilterParser, user_schema: ModelSchema
) -> None:
    """Test that invalid field raises HTTPException."""
    with pytest.raises(HTTPException) as exc_info:
        filter_parser.validate_field("invalid_field", "User", user_schema)

    assert exc_info.value.status_code == 400
    assert "Invalid filter field 'invalid_field'" in exc_info.value.detail


# =============================================================================
# TEST: validate_operator()
# =============================================================================


@pytest.mark.parametrize(
    "operator_str,expected",
    [
        ("eq", FilterOperator.EQ),
        ("gt", FilterOperator.GT),
        ("gte", FilterOperator.GTE),
        ("lt", FilterOperator.LT),
        ("lte", FilterOperator.LTE),
        ("contains", FilterOperator.CONTAINS),
        ("startswith", FilterOperator.STARTSWITH),
        ("endswith", FilterOperator.ENDSWITH),
        ("in", FilterOperator.IN),
    ],
)
def test_validate_operator_valid(
    filter_parser: FilterParser, operator_str: str, expected: FilterOperator
) -> None:
    """Test validating all supported operators."""
    operator = filter_parser.validate_operator(operator_str)
    assert operator == expected


def test_validate_operator_invalid(filter_parser: FilterParser) -> None:
    """Test that invalid operator raises HTTPException."""
    with pytest.raises(HTTPException) as exc_info:
        filter_parser.validate_operator("invalid_op")

    assert exc_info.value.status_code == 400
    assert "Invalid filter operator 'invalid_op'" in exc_info.value.detail


# =============================================================================
# TEST: coerce_value()
# =============================================================================


def test_coerce_value_null(
    filter_parser: FilterParser, user_schema: ModelSchema
) -> None:
    """Test coercing 'null' string to None."""
    bio_field = next(f for f in user_schema.fields if f.name == "bio")
    value = filter_parser.coerce_value("null", bio_field, FilterOperator.EQ)

    assert value is None


def test_coerce_value_in_operator(
    filter_parser: FilterParser, user_schema: ModelSchema
) -> None:
    """Test coercing IN operator with comma-separated values."""
    age_field = next(f for f in user_schema.fields if f.name == "age")
    value = filter_parser.coerce_value("18,25,30", age_field, FilterOperator.IN)

    assert value == [18, 25, 30]


def test_coerce_value_single(
    filter_parser: FilterParser, user_schema: ModelSchema
) -> None:
    """Test coercing single value."""
    age_field = next(f for f in user_schema.fields if f.name == "age")
    value = filter_parser.coerce_value("18", age_field, FilterOperator.GTE)

    assert value == 18


# =============================================================================
# TEST: coerce_single_value() - Type Coercion
# =============================================================================


def test_coerce_single_value_string(
    filter_parser: FilterParser, user_schema: ModelSchema
) -> None:
    """Test coercing string value."""
    name_field = next(f for f in user_schema.fields if f.name == "name")
    value = filter_parser.coerce_single_value("John", name_field)

    assert value == "John"
    assert isinstance(value, str)


def test_coerce_single_value_int(
    filter_parser: FilterParser, user_schema: ModelSchema
) -> None:
    """Test coercing int value."""
    age_field = next(f for f in user_schema.fields if f.name == "age")
    value = filter_parser.coerce_single_value("25", age_field)

    assert value == 25
    assert isinstance(value, int)


def test_coerce_single_value_bool_true(
    filter_parser: FilterParser, user_schema: ModelSchema
) -> None:
    """Test coercing bool value (true)."""
    is_active_field = next(f for f in user_schema.fields if f.name == "is_active")

    for true_value in ["true", "True", "TRUE", "1", "yes"]:
        value = filter_parser.coerce_single_value(true_value, is_active_field)
        assert value is True


def test_coerce_single_value_bool_false(
    filter_parser: FilterParser, user_schema: ModelSchema
) -> None:
    """Test coercing bool value (false)."""
    is_active_field = next(f for f in user_schema.fields if f.name == "is_active")

    for false_value in ["false", "False", "FALSE", "0", "no"]:
        value = filter_parser.coerce_single_value(false_value, is_active_field)
        assert value is False


def test_coerce_single_value_float(
    filter_parser: FilterParser, user_schema: ModelSchema
) -> None:
    """Test coercing float value."""
    score_field = next(f for f in user_schema.fields if f.name == "score")
    value = filter_parser.coerce_single_value("3.14", score_field)

    assert value == 3.14
    assert isinstance(value, float)


def test_coerce_single_value_datetime(
    filter_parser: FilterParser, event_schema: ModelSchema
) -> None:
    """Test coercing datetime value."""
    created_at_field = next(f for f in event_schema.fields if f.name == "created_at")
    value = filter_parser.coerce_single_value("2024-01-15T10:30:00", created_at_field)

    assert isinstance(value, datetime)
    assert value.year == 2024
    assert value.month == 1
    assert value.day == 15


def test_coerce_single_value_date(
    filter_parser: FilterParser, event_schema: ModelSchema
) -> None:
    """Test coercing date value."""
    event_date_field = next(f for f in event_schema.fields if f.name == "event_date")
    value = filter_parser.coerce_single_value("2024-01-15", event_date_field)

    assert isinstance(value, date)
    assert value.year == 2024
    assert value.month == 1
    assert value.day == 15


def test_coerce_single_value_enum_int_based(
    filter_parser: FilterParser, product_schema: ModelSchema
) -> None:
    """Test coercing int-based enum."""
    priority_field = next(f for f in product_schema.fields if f.name == "priority")
    value = filter_parser.coerce_single_value("2", priority_field)

    assert value == 2
    assert isinstance(value, int)


def test_coerce_single_value_enum_str_based(
    filter_parser: FilterParser, product_schema: ModelSchema
) -> None:
    """Test coercing str-based enum."""
    status_field = next(f for f in product_schema.fields if f.name == "status")
    value = filter_parser.coerce_single_value("active", status_field)

    assert value == "active"
    assert isinstance(value, str)


def test_coerce_single_value_enum_invalid(
    filter_parser: FilterParser, product_schema: ModelSchema
) -> None:
    """Test that invalid enum value raises ValueError."""
    priority_field = next(f for f in product_schema.fields if f.name == "priority")

    with pytest.raises(ValueError) as exc_info:
        filter_parser.coerce_single_value("999", priority_field)

    assert "Invalid value" in str(exc_info.value)
    assert "Valid values" in str(exc_info.value)


def test_coerce_single_value_invalid_type(
    filter_parser: FilterParser, user_schema: ModelSchema
) -> None:
    """Test that invalid type conversion raises ValueError."""
    age_field = next(f for f in user_schema.fields if f.name == "age")

    with pytest.raises(ValueError) as exc_info:
        filter_parser.coerce_single_value("not_a_number", age_field)

    assert "Cannot convert" in str(exc_info.value)


# =============================================================================
# TEST: Integration
# =============================================================================


def test_integration_complex_query(
    filter_parser: FilterParser, user_schema: ModelSchema
) -> None:
    """Test parsing a complex query with multiple operators."""
    query_params = QueryParams(
        {
            "age__gte": "18",
            "age__lte": "65",
            "name__startswith": "J",
            "is_active": "true",
            "score__gt": "5.0",
        }
    )
    filters = filter_parser.parse_params(query_params, "User", user_schema)

    assert len(filters) == 5

    # Verify each filter
    age_gte_filter = next(
        f for f in filters if f.field == "age" and f.operator == FilterOperator.GTE
    )
    assert age_gte_filter.value == 18

    age_lte_filter = next(
        f for f in filters if f.field == "age" and f.operator == FilterOperator.LTE
    )
    assert age_lte_filter.value == 65

    name_filter = next(f for f in filters if f.field == "name")
    assert name_filter.operator == FilterOperator.STARTSWITH
    assert name_filter.value == "J"

    is_active_filter = next(f for f in filters if f.field == "is_active")
    assert is_active_filter.value is True

    score_filter = next(f for f in filters if f.field == "score")
    assert score_filter.operator == FilterOperator.GT
    assert score_filter.value == 5.0


def test_integration_with_custom_config(user_schema: ModelSchema) -> None:
    """Test FilterParser with custom config (lower max filters)."""
    custom_config = Config(filter_sort=FilterSortConfig(max_filters=2))
    parser = FilterParser(config=custom_config)

    query_params = QueryParams(
        {"age": "18", "name": "John", "email": "test@example.com"}
    )

    with pytest.raises(HTTPException) as exc_info:
        parser.parse_params(query_params, "User", user_schema)

    assert exc_info.value.status_code == 400
    assert "Maximum allowed: 2" in exc_info.value.detail
