"""Tests for schema parser."""

from __future__ import annotations

from pathlib import Path

import pytest
from mock_api.core.parser import SchemaParser

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def parser() -> SchemaParser:
    """Create a SchemaParser instance."""
    return SchemaParser()


@pytest.fixture
def test_models_file() -> str:
    """Path to test models fixture file."""
    return str(Path(__file__).parent / "fixtures" / "test_models.py")


@pytest.fixture
def empty_models_file() -> str:
    """Path to empty models fixture file (no Pydantic models)."""
    return str(Path(__file__).parent / "fixtures" / "empty_models.py")


@pytest.fixture
def inheritance_models_file() -> str:
    """Path to inheritance models fixture file."""
    return str(Path(__file__).parent / "fixtures" / "inheritance_models.py")


@pytest.fixture
def optional_fk_models_file() -> str:
    """Path to optional foreign key models fixture file."""
    return str(Path(__file__).parent / "fixtures" / "optional_fk_models.py")


@pytest.fixture
def enum_models_file() -> str:
    """Path to enum models fixture file."""
    return str(Path(__file__).parent / "fixtures" / "enum_models.py")


# =============================================================================
# TESTS: File Loading
# =============================================================================


def test_parse_file_with_nonexistent_file_raises_file_not_found_error(
    parser: SchemaParser,
) -> None:
    """Test that parsing a nonexistent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="Schema file not found"):
        parser.parse_file("nonexistent.py")


def test_parse_file_with_non_python_file_raises_value_error(
    parser: SchemaParser,
) -> None:
    """Test that parsing a non-.py file raises ValueError."""
    with pytest.raises(ValueError, match="must be a Python file"):
        parser.parse_file("models.txt")


def test_parse_file_with_valid_file_returns_schemas(
    parser: SchemaParser, test_models_file: str
) -> None:
    """Test that parsing a valid file returns model schemas."""
    schemas = parser.parse_file(test_models_file)

    assert isinstance(schemas, dict)
    assert len(schemas) == 3
    assert "User" in schemas
    assert "Post" in schemas
    assert "Comment" in schemas


def test_parse_file_with_no_models_returns_empty_dict(
    parser: SchemaParser, empty_models_file: str
) -> None:
    """Test that parsing a file with no models returns an empty dict."""
    schemas = parser.parse_file(empty_models_file)

    assert isinstance(schemas, dict)
    assert len(schemas) == 0


# =============================================================================
# TESTS: Model Schema Extraction
# =============================================================================


def test_parser_extracts_user_model_with_correct_fields(
    parser: SchemaParser, test_models_file: str
) -> None:
    """Test that User model is parsed with all fields correctly."""
    schemas = parser.parse_file(test_models_file)
    user = schemas["User"]

    assert user.name == "User"
    assert len(user.fields) == 5

    field_names = [f.name for f in user.fields]
    assert "id" in field_names
    assert "name" in field_names
    assert "email" in field_names
    assert "age" in field_names
    assert "created_at" in field_names


def test_parser_detects_field_types_correctly(
    parser: SchemaParser, test_models_file: str
) -> None:
    """Test that field types are extracted correctly."""
    schemas = parser.parse_file(test_models_file)
    user = schemas["User"]

    id_field = next(f for f in user.fields if f.name == "id")
    assert id_field.type is int

    name_field = next(f for f in user.fields if f.name == "name")
    assert name_field.type is str


def test_parser_detects_optional_fields_correctly(
    parser: SchemaParser, test_models_file: str
) -> None:
    """Test that optional fields are detected."""
    schemas = parser.parse_file(test_models_file)
    user = schemas["User"]

    age_field = next(f for f in user.fields if f.name == "age")
    assert age_field.is_optional is True

    name_field = next(f for f in user.fields if f.name == "name")
    assert name_field.is_optional is False


def test_parser_handles_model_inheritance(
    parser: SchemaParser, inheritance_models_file: str
) -> None:
    """Test that inherited fields are included in model schema."""
    schemas = parser.parse_file(inheritance_models_file)
    article = schemas["Article"]

    # Article should have its own fields plus inherited ones
    field_names = [f.name for f in article.fields]

    # Own fields
    assert "id" in field_names
    assert "title" in field_names
    assert "content" in field_names
    assert "author_id" in field_names

    # Inherited fields from TimestampedModel
    assert "created_at" in field_names
    assert "updated_at" in field_names

    # Verify total field count (4 own + 2 inherited)
    assert len(article.fields) == 6


# =============================================================================
# TESTS: Foreign Key Detection
# =============================================================================


def test_parser_detects_foreign_key_fields(
    parser: SchemaParser, test_models_file: str
) -> None:
    """Test that _id fields are detected as foreign keys."""
    schemas = parser.parse_file(test_models_file)
    post = schemas["Post"]

    author_id_field = next(f for f in post.fields if f.name == "author_id")
    assert author_id_field.is_foreign_key is True
    assert author_id_field.related_model == "User"


def test_parser_does_not_mark_id_field_as_foreign_key(
    parser: SchemaParser, test_models_file: str
) -> None:
    """Test that 'id' field is not marked as a foreign key."""
    schemas = parser.parse_file(test_models_file)
    user = schemas["User"]

    id_field = next(f for f in user.fields if f.name == "id")
    assert id_field.is_foreign_key is False


def test_parser_detects_optional_foreign_keys(
    parser: SchemaParser, optional_fk_models_file: str
) -> None:
    """Test that optional foreign key fields are still detected as FKs."""
    schemas = parser.parse_file(optional_fk_models_file)
    task = schemas["Task"]

    assignee_id_field = next(f for f in task.fields if f.name == "assignee_id")
    assert assignee_id_field.is_foreign_key is True
    assert assignee_id_field.is_optional is True
    assert assignee_id_field.related_model == "User"


# =============================================================================
# TESTS: Relationship Detection
# =============================================================================


def test_parser_creates_many_to_one_relationship_for_foreign_key(
    parser: SchemaParser, test_models_file: str
) -> None:
    """Test that many-to-one relationships are created for foreign keys."""
    schemas = parser.parse_file(test_models_file)
    post = schemas["Post"]

    # Post has author_id (many-to-one) and comments (one-to-many inverse)
    author_rel = next(
        r for r in post.relationships if r.relationship_type == "many_to_one"
    )
    assert author_rel.field_name == "author_id"
    assert author_rel.related_model == "User"
    assert author_rel.relationship_type == "many_to_one"


def test_parser_creates_inverse_one_to_many_relationship(
    parser: SchemaParser, test_models_file: str
) -> None:
    """Test that inverse one-to-many relationships are created."""
    schemas = parser.parse_file(test_models_file)
    user = schemas["User"]

    # User should have one-to-many relationship with Post
    post_rel = next((r for r in user.relationships if r.related_model == "Post"), None)
    assert post_rel is not None
    assert post_rel.relationship_type == "one_to_many"
    assert post_rel.field_name == "posts"


def test_parser_handles_multiple_foreign_keys_in_one_model(
    parser: SchemaParser, test_models_file: str
) -> None:
    """Test that models with multiple foreign keys are handled correctly."""
    schemas = parser.parse_file(test_models_file)
    comment = schemas["Comment"]

    assert len(comment.relationships) == 2

    post_rel = next(r for r in comment.relationships if r.related_model == "Post")
    assert post_rel.field_name == "post_id"

    user_rel = next(r for r in comment.relationships if r.related_model == "User")
    assert user_rel.field_name == "user_id"


# =============================================================================
# TESTS: Pydantic Model Reference
# =============================================================================


def test_parser_stores_reference_to_pydantic_model(
    parser: SchemaParser, test_models_file: str
) -> None:
    """Test that original Pydantic model is stored in schema."""
    schemas = parser.parse_file(test_models_file)
    user = schemas["User"]

    assert user.pydantic_model is not None
    assert user.pydantic_model.__name__ == "User"


# =============================================================================
# TESTS: Enum Field Detection
# =============================================================================


def test_parser_detects_enum_fields(
    parser: SchemaParser, enum_models_file: str
) -> None:
    """Test that enum fields are detected and marked correctly."""
    schemas = parser.parse_file(enum_models_file)
    user = schemas["User"]

    status_field = next(f for f in user.fields if f.name == "status")
    assert status_field.is_enum is True
    assert len(status_field.enum_values) == 3
    assert "active" in status_field.enum_values
    assert "inactive" in status_field.enum_values
    assert "suspended" in status_field.enum_values


def test_parser_extracts_enum_values_correctly(
    parser: SchemaParser, enum_models_file: str
) -> None:
    """Test that enum values are extracted in correct order."""
    schemas = parser.parse_file(enum_models_file)
    task = schemas["Task"]

    priority_field = next(f for f in task.fields if f.name == "priority")
    assert priority_field.is_enum is True
    assert priority_field.enum_values == [1, 2, 3, 4]


def test_parser_handles_optional_enum_fields(
    parser: SchemaParser, enum_models_file: str
) -> None:
    """Test that optional enum fields are handled correctly."""
    schemas = parser.parse_file(enum_models_file)
    task = schemas["Task"]

    status_field = next(f for f in task.fields if f.name == "status")
    assert status_field.is_enum is True
    assert status_field.is_optional is True
    assert len(status_field.enum_values) == 3


def test_parser_does_not_mark_regular_fields_as_enum(
    parser: SchemaParser, enum_models_file: str
) -> None:
    """Test that non-enum fields are not marked as enums."""
    schemas = parser.parse_file(enum_models_file)
    user = schemas["User"]

    name_field = next(f for f in user.fields if f.name == "name")
    assert name_field.is_enum is False
    assert len(name_field.enum_values) == 0
