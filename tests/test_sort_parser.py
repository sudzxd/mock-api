"""Tests for SortParser service.

Comprehensive test coverage for sort parameter parsing and validation
functionality.
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Third Party
import pytest
from fastapi import HTTPException

# Project/Local
from mock_api.core.config import Config, FilterSortConfig
from mock_api.core.constants import SortDirection
from mock_api.core.services import SortParser
from mock_api.core.types import FieldSchema, ModelSchema

# =============================================================================
# TEST FIXTURES
# =============================================================================


@pytest.fixture
def sort_parser() -> SortParser:
    """Create SortParser instance."""
    return SortParser()


@pytest.fixture
def user_schema() -> ModelSchema:
    """Create a User model schema for testing."""
    return ModelSchema(
        name="User",
        fields=[
            FieldSchema(name="id", type=int, is_optional=False),
            FieldSchema(name="name", type=str, is_optional=False),
            FieldSchema(name="email", type=str, is_optional=False),
            FieldSchema(name="created_at", type=str, is_optional=False),
            FieldSchema(name="age", type=int, is_optional=False),
        ],
    )


# =============================================================================
# TEST: parse_param()
# =============================================================================


def test_parse_param_single_field_ascending(
    sort_parser: SortParser, user_schema: ModelSchema
) -> None:
    """Test parsing a single ascending sort field."""
    sorts = sort_parser.parse_param("name", "User", user_schema)

    assert len(sorts) == 1
    assert sorts[0].field == "name"
    assert sorts[0].direction == SortDirection.ASC


def test_parse_param_single_field_descending(
    sort_parser: SortParser, user_schema: ModelSchema
) -> None:
    """Test parsing a single descending sort field."""
    sorts = sort_parser.parse_param("-created_at", "User", user_schema)

    assert len(sorts) == 1
    assert sorts[0].field == "created_at"
    assert sorts[0].direction == SortDirection.DESC


def test_parse_param_multiple_fields(
    sort_parser: SortParser, user_schema: ModelSchema
) -> None:
    """Test parsing multiple sort fields."""
    sorts = sort_parser.parse_param("-created_at,name,age", "User", user_schema)

    assert len(sorts) == 3
    assert sorts[0].field == "created_at"
    assert sorts[0].direction == SortDirection.DESC
    assert sorts[1].field == "name"
    assert sorts[1].direction == SortDirection.ASC
    assert sorts[2].field == "age"
    assert sorts[2].direction == SortDirection.ASC


def test_parse_param_mixed_directions(
    sort_parser: SortParser, user_schema: ModelSchema
) -> None:
    """Test parsing fields with mixed sort directions."""
    sorts = sort_parser.parse_param("name,-age,-email", "User", user_schema)

    assert len(sorts) == 3
    assert sorts[0].field == "name"
    assert sorts[0].direction == SortDirection.ASC
    assert sorts[1].field == "age"
    assert sorts[1].direction == SortDirection.DESC
    assert sorts[2].field == "email"
    assert sorts[2].direction == SortDirection.DESC


def test_parse_param_empty(sort_parser: SortParser, user_schema: ModelSchema) -> None:
    """Test parsing with no sort parameter."""
    sorts = sort_parser.parse_param(None, "User", user_schema)
    assert len(sorts) == 0

    sorts = sort_parser.parse_param("", "User", user_schema)
    assert len(sorts) == 0


def test_parse_param_whitespace_handling(
    sort_parser: SortParser, user_schema: ModelSchema
) -> None:
    """Test parsing handles whitespace correctly."""
    sorts = sort_parser.parse_param(" name , -email ", "User", user_schema)

    assert len(sorts) == 2
    assert sorts[0].field == "name"
    assert sorts[1].field == "email"


def test_parse_param_too_many_fields(
    sort_parser: SortParser, user_schema: ModelSchema
) -> None:
    """Test that too many sort fields raises HTTPException."""
    # Create 6 valid sort fields (default max is 5)
    sort_value = "name,email,age,created_at,id,-name"

    with pytest.raises(HTTPException) as exc_info:
        sort_parser.parse_param(sort_value, "User", user_schema)

    assert exc_info.value.status_code == 400
    assert "Too many sort fields" in exc_info.value.detail


def test_parse_param_invalid_field(
    sort_parser: SortParser, user_schema: ModelSchema
) -> None:
    """Test parsing with invalid field raises HTTPException."""
    with pytest.raises(HTTPException) as exc_info:
        sort_parser.parse_param("invalid_field", "User", user_schema)

    assert exc_info.value.status_code == 400
    assert "Invalid sort field 'invalid_field'" in exc_info.value.detail


# =============================================================================
# TEST: parse_single()
# =============================================================================


def test_parse_single_ascending(
    sort_parser: SortParser, user_schema: ModelSchema
) -> None:
    """Test parsing single ascending field."""
    sort_spec = sort_parser.parse_single("name", "User", user_schema)

    assert sort_spec.field == "name"
    assert sort_spec.direction == SortDirection.ASC


def test_parse_single_descending(
    sort_parser: SortParser, user_schema: ModelSchema
) -> None:
    """Test parsing single descending field."""
    sort_spec = sort_parser.parse_single("-created_at", "User", user_schema)

    assert sort_spec.field == "created_at"
    assert sort_spec.direction == SortDirection.DESC


def test_parse_single_invalid_field(
    sort_parser: SortParser, user_schema: ModelSchema
) -> None:
    """Test parsing single invalid field raises HTTPException."""
    with pytest.raises(HTTPException) as exc_info:
        sort_parser.parse_single("invalid_field", "User", user_schema)

    assert exc_info.value.status_code == 400
    assert "Invalid sort field" in exc_info.value.detail


def test_parse_single_descending_invalid_field(
    sort_parser: SortParser, user_schema: ModelSchema
) -> None:
    """Test parsing descending invalid field raises HTTPException."""
    with pytest.raises(HTTPException) as exc_info:
        sort_parser.parse_single("-invalid_field", "User", user_schema)

    assert exc_info.value.status_code == 400
    assert "Invalid sort field 'invalid_field'" in exc_info.value.detail


# =============================================================================
# TEST: validate_field()
# =============================================================================


def test_validate_field_valid(
    sort_parser: SortParser, user_schema: ModelSchema
) -> None:
    """Test validating an existing field."""
    # Should not raise
    sort_parser.validate_field("name", "User", user_schema)
    sort_parser.validate_field("email", "User", user_schema)
    sort_parser.validate_field("created_at", "User", user_schema)


def test_validate_field_invalid(
    sort_parser: SortParser, user_schema: ModelSchema
) -> None:
    """Test that invalid field raises HTTPException."""
    with pytest.raises(HTTPException) as exc_info:
        sort_parser.validate_field("invalid_field", "User", user_schema)

    assert exc_info.value.status_code == 400
    assert "Invalid sort field 'invalid_field'" in exc_info.value.detail
    assert "Available fields:" in exc_info.value.detail


def test_validate_field_error_message_includes_available_fields(
    sort_parser: SortParser, user_schema: ModelSchema
) -> None:
    """Test that error message includes list of available fields."""
    with pytest.raises(HTTPException) as exc_info:
        sort_parser.validate_field("bad_field", "User", user_schema)

    error_detail = exc_info.value.detail
    assert "id" in error_detail
    assert "name" in error_detail
    assert "email" in error_detail


# =============================================================================
# TEST: Integration & Edge Cases
# =============================================================================


def test_integration_complex_query(
    sort_parser: SortParser, user_schema: ModelSchema
) -> None:
    """Test parsing a complex sort query."""
    sorts = sort_parser.parse_param("-created_at,name,-age", "User", user_schema)

    assert len(sorts) == 3

    # Verify each sort spec
    created_at_sort = sorts[0]
    assert created_at_sort.field == "created_at"
    assert created_at_sort.direction == SortDirection.DESC

    name_sort = sorts[1]
    assert name_sort.field == "name"
    assert name_sort.direction == SortDirection.ASC

    age_sort = sorts[2]
    assert age_sort.field == "age"
    assert age_sort.direction == SortDirection.DESC


def test_integration_with_custom_config(user_schema: ModelSchema) -> None:
    """Test SortParser with custom config (lower max sort fields)."""
    custom_config = Config(filter_sort=FilterSortConfig(max_sort_fields=2))
    parser = SortParser(config=custom_config)

    # Should allow 2 fields
    sorts = parser.parse_param("name,email", "User", user_schema)
    assert len(sorts) == 2

    # Should reject 3 fields
    with pytest.raises(HTTPException) as exc_info:
        parser.parse_param("name,email,age", "User", user_schema)

    assert exc_info.value.status_code == 400
    assert "Maximum allowed: 2" in exc_info.value.detail


def test_edge_case_all_descending(
    sort_parser: SortParser, user_schema: ModelSchema
) -> None:
    """Test parsing with all fields descending."""
    sorts = sort_parser.parse_param("-name,-email,-age", "User", user_schema)

    assert len(sorts) == 3
    assert all(s.direction == SortDirection.DESC for s in sorts)


def test_edge_case_all_ascending(
    sort_parser: SortParser, user_schema: ModelSchema
) -> None:
    """Test parsing with all fields ascending."""
    sorts = sort_parser.parse_param("name,email,age", "User", user_schema)

    assert len(sorts) == 3
    assert all(s.direction == SortDirection.ASC for s in sorts)


def test_edge_case_single_descending_prefix(
    sort_parser: SortParser, user_schema: ModelSchema
) -> None:
    """Test that descending prefix is correctly stripped."""
    sort_spec = sort_parser.parse_single("-name", "User", user_schema)

    # Field name should not include the prefix
    assert sort_spec.field == "name"
    assert "-" not in sort_spec.field
    assert sort_spec.direction == SortDirection.DESC
