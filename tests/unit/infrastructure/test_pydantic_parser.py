"""Tests for PydanticSchemaParser."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from pathlib import Path

# Third-party
import pytest

# Project/local
from mock_api.core.exceptions.schema import SchemaParseError, SchemaValidationError
from mock_api.infrastructure.parsers.pydantic_parser import PydanticSchemaParser


# =============================================================================
# TESTS - PydanticSchemaParser
# =============================================================================
def test_pydantic_parser_parse_file_extracts_models() -> None:
    """PydanticSchemaParser should extract all models from file."""
    # Arrange
    parser = PydanticSchemaParser()
    file_path = str(Path(__file__).parent.parent.parent / "fixtures" / "test_models.py")

    # Act
    schemas = parser.parse_file(file_path)

    # Assert
    assert len(schemas) == 3
    assert "User" in schemas
    assert "Post" in schemas
    assert "Product" in schemas


def test_pydantic_parser_parse_user_model_fields() -> None:
    """PydanticSchemaParser should extract User model fields correctly."""
    # Arrange
    parser = PydanticSchemaParser()
    file_path = str(Path(__file__).parent.parent.parent / "fixtures" / "test_models.py")

    # Act
    schemas = parser.parse_file(file_path)
    user_schema = schemas["User"]

    # Assert
    assert user_schema.name == "User"
    assert len(user_schema.fields) == 5
    assert user_schema.primary_key == "id"

    # Check specific fields
    id_field = user_schema.get_field("id")
    assert id_field is not None
    assert id_field.type is int
    assert id_field.is_optional is False

    age_field = user_schema.get_field("age")
    assert age_field is not None
    assert age_field.type is int
    assert age_field.is_optional is True


def test_pydantic_parser_detects_foreign_keys() -> None:
    """PydanticSchemaParser should detect foreign key relationships."""
    # Arrange
    parser = PydanticSchemaParser()
    file_path = str(Path(__file__).parent.parent.parent / "fixtures" / "test_models.py")

    # Act
    schemas = parser.parse_file(file_path)
    post_schema = schemas["Post"]

    # Assert
    foreign_keys = post_schema.get_foreign_keys()
    assert len(foreign_keys) == 1
    assert foreign_keys[0].name == "user_id"
    assert foreign_keys[0].is_foreign_key is True
    assert foreign_keys[0].related_model == "User"


def test_pydantic_parser_handles_optional_fields() -> None:
    """PydanticSchemaParser should handle optional fields correctly."""
    # Arrange
    parser = PydanticSchemaParser()
    file_path = str(Path(__file__).parent.parent.parent / "fixtures" / "test_models.py")

    # Act
    schemas = parser.parse_file(file_path)
    product_schema = schemas["Product"]

    # Assert
    description_field = product_schema.get_field("description")
    assert description_field is not None
    assert description_field.is_optional is True
    assert description_field.type is str


def test_pydantic_parser_handles_field_defaults() -> None:
    """PydanticSchemaParser should extract field defaults."""
    # Arrange
    parser = PydanticSchemaParser()
    file_path = str(Path(__file__).parent.parent.parent / "fixtures" / "test_models.py")

    # Act
    schemas = parser.parse_file(file_path)
    product_schema = schemas["Product"]

    # Assert
    in_stock_field = product_schema.get_field("in_stock")
    assert in_stock_field is not None
    assert in_stock_field.default is True


def test_pydantic_parser_supports_file_checks_python_extension() -> None:
    """PydanticSchemaParser.supports_file() should check .py extension."""
    # Arrange
    parser = PydanticSchemaParser()

    # Act & Assert
    assert parser.supports_file("models.py") is True
    assert parser.supports_file("schema.json") is False
    assert parser.supports_file("api.yaml") is False


def test_pydantic_parser_raises_error_with_invalid_file() -> None:
    """PydanticSchemaParser should raise SchemaParseError for invalid file."""
    # Arrange
    parser = PydanticSchemaParser()

    # Act & Assert
    with pytest.raises(SchemaParseError):
        parser.parse_file("nonexistent_file.py")


def test_pydantic_parser_validates_foreign_key_references() -> None:
    """PydanticSchemaParser should validate foreign key references."""
    # Arrange
    parser = PydanticSchemaParser()
    file_path = str(Path(__file__).parent.parent.parent / "fixtures" / "test_models.py")

    # Act
    schemas = parser.parse_file(file_path)

    # Assert - Should not raise, all FKs are valid
    parser.validate_schema(schemas)


def test_pydantic_parser_raises_error_for_invalid_foreign_keys() -> None:
    """PydanticSchemaParser should raise error for invalid FK references."""
    # Arrange
    parser = PydanticSchemaParser()
    from mock_api.domain.value_objects.schema import FieldSchema, ModelSchema

    # Create schema with invalid FK
    invalid_schema = ModelSchema(
        name="Comment",
        fields=(
            FieldSchema(name="id", type=int, is_optional=False),
            FieldSchema(
                name="post_id",
                type=int,
                is_optional=False,
                is_foreign_key=True,
                related_model="NonExistentPost",
            ),
        ),
        primary_key="id",
    )

    # Act & Assert
    with pytest.raises(SchemaValidationError):
        parser.validate_schema({"Comment": invalid_schema})
