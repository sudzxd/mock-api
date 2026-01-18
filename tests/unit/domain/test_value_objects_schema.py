"""Tests for schema value objects."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Third-party
# Project/local
from mock_api.domain.value_objects.schema import FieldSchema, ModelSchema


# =============================================================================
# TESTS - FieldSchema
# =============================================================================
def test_field_schema_creation_with_required_field() -> None:
    """FieldSchema should be created with required fields."""
    # Arrange & Act
    field = FieldSchema(name="email", type=str, is_optional=False)

    # Assert
    assert field.name == "email"
    assert field.type is str
    assert field.is_optional is False
    assert field.default is None
    assert field.is_foreign_key is False


def test_field_schema_creation_with_optional_field() -> None:
    """FieldSchema should be created with optional fields and defaults."""
    # Arrange & Act
    field = FieldSchema(
        name="age",
        type=int,
        is_optional=True,
        default=0,
        is_foreign_key=False,
        related_model=None,
    )

    # Assert
    assert field.name == "age"
    assert field.type is int
    assert field.is_optional is True
    assert field.default == 0


def test_field_schema_with_foreign_key() -> None:
    """FieldSchema should handle foreign key relationships."""
    # Arrange & Act
    field = FieldSchema(
        name="user_id",
        type=int,
        is_optional=False,
        is_foreign_key=True,
        related_model="User",
    )

    # Assert
    assert field.is_foreign_key is True
    assert field.related_model == "User"


# =============================================================================
# TESTS - ModelSchema
# =============================================================================
def test_model_schema_creation() -> None:
    """ModelSchema should be created with fields."""
    # Arrange
    fields = (
        FieldSchema(name="id", type=int, is_optional=False),
        FieldSchema(name="name", type=str, is_optional=False),
    )

    # Act
    schema = ModelSchema(name="User", fields=fields, primary_key="id")

    # Assert
    assert schema.name == "User"
    assert len(schema.fields) == 2
    assert schema.primary_key == "id"


def test_model_schema_get_field_returns_field_when_exists() -> None:
    """ModelSchema.get_field() should return field when it exists."""
    # Arrange
    fields = (
        FieldSchema(name="id", type=int, is_optional=False),
        FieldSchema(name="name", type=str, is_optional=False),
    )
    schema = ModelSchema(name="User", fields=fields, primary_key="id")

    # Act
    field = schema.get_field("name")

    # Assert
    assert field is not None
    assert field.name == "name"
    assert field.type is str


def test_model_schema_get_field_returns_none_when_not_exists() -> None:
    """ModelSchema.get_field() should return None when field doesn't exist."""
    # Arrange
    fields = (FieldSchema(name="id", type=int, is_optional=False),)
    schema = ModelSchema(name="User", fields=fields, primary_key="id")

    # Act
    field = schema.get_field("nonexistent")

    # Assert
    assert field is None


def test_model_schema_has_field_returns_true_when_exists() -> None:
    """ModelSchema.has_field() should return True when field exists."""
    # Arrange
    fields = (
        FieldSchema(name="id", type=int, is_optional=False),
        FieldSchema(name="email", type=str, is_optional=False),
    )
    schema = ModelSchema(name="User", fields=fields, primary_key="id")

    # Act & Assert
    assert schema.has_field("email") is True


def test_model_schema_has_field_returns_false_when_not_exists() -> None:
    """ModelSchema.has_field() should return False when field doesn't exist."""
    # Arrange
    fields = (FieldSchema(name="id", type=int, is_optional=False),)
    schema = ModelSchema(name="User", fields=fields, primary_key="id")

    # Act & Assert
    assert schema.has_field("email") is False


def test_model_schema_get_required_fields() -> None:
    """ModelSchema.get_required_fields() should return only required fields."""
    # Arrange
    fields = (
        FieldSchema(name="id", type=int, is_optional=False),
        FieldSchema(name="name", type=str, is_optional=False),
        FieldSchema(name="age", type=int, is_optional=True),
        FieldSchema(name="bio", type=str, is_optional=True),
    )
    schema = ModelSchema(name="User", fields=fields, primary_key="id")

    # Act
    required = schema.get_required_fields()

    # Assert
    assert len(required) == 2
    assert all(not f.is_optional for f in required)
    assert required[0].name == "id"
    assert required[1].name == "name"


def test_model_schema_get_foreign_keys() -> None:
    """ModelSchema.get_foreign_keys() should return only foreign key fields."""
    # Arrange
    fields = (
        FieldSchema(name="id", type=int, is_optional=False),
        FieldSchema(name="name", type=str, is_optional=False),
        FieldSchema(
            name="user_id",
            type=int,
            is_optional=False,
            is_foreign_key=True,
            related_model="User",
        ),
        FieldSchema(
            name="category_id",
            type=int,
            is_optional=False,
            is_foreign_key=True,
            related_model="Category",
        ),
    )
    schema = ModelSchema(name="Post", fields=fields, primary_key="id")

    # Act
    foreign_keys = schema.get_foreign_keys()

    # Assert
    assert len(foreign_keys) == 2
    assert all(f.is_foreign_key for f in foreign_keys)
    assert foreign_keys[0].related_model == "User"
    assert foreign_keys[1].related_model == "Category"
