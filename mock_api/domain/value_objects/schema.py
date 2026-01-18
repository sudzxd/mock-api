"""Schema value objects - immutable schema definitions.

These represent parsed schema information from any source format
(Pydantic, OpenAPI, GraphQL, etc.).
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from dataclasses import dataclass
from typing import Any

# =============================================================================
# TYPES & CONSTANTS
# =============================================================================
# Type aliases
SchemaDict = dict[str, "ModelSchema"]


# =============================================================================
# CORE CLASSES
# =============================================================================
@dataclass(frozen=True)
class FieldSchema:
    """Immutable field metadata.

    Represents a single field in a model schema, including type information,
    optionality, defaults, and foreign key relationships.
    """

    name: str
    type: type
    is_optional: bool
    default: Any = None
    is_foreign_key: bool = False
    related_model: str | None = None

    def __post_init__(self) -> None:
        """Validate field schema.

        Raises:
            ValueError: If validation fails
        """
        # Validate name is non-empty
        if not self.name or not self.name.strip():
            raise ValueError("Field name cannot be empty")

        # Validate FK consistency
        if self.is_foreign_key and not self.related_model:
            raise ValueError(
                f"Field {self.name} is marked as foreign key but has no related_model"
            )
        if not self.is_foreign_key and self.related_model:
            raise ValueError(
                f"Field {self.name} has related_model but is not marked as foreign key"
            )


@dataclass(frozen=True)
class ModelSchema:
    """Immutable model schema definition.

    Represents a complete model/type/entity schema parsed from any source format.
    Uses tuple for fields to ensure immutability.

    For Pydantic schemas, model_class stores the original Pydantic model for
    efficient validation (avoiding dynamic model rebuilding).
    """

    name: str
    fields: tuple[FieldSchema, ...]
    primary_key: str = "id"
    model_class: type | None = None

    def get_field(self, name: str) -> FieldSchema | None:
        """Get field by name.

        Args:
            name: Field name to lookup

        Returns:
            FieldSchema if found, None otherwise
        """
        for field in self.fields:
            if field.name == name:
                return field
        return None

    def has_field(self, name: str) -> bool:
        """Check if field exists.

        Args:
            name: Field name to check

        Returns:
            True if field exists
        """
        return self.get_field(name) is not None

    def get_required_fields(self) -> tuple[FieldSchema, ...]:
        """Get all required (non-optional) fields.

        Returns:
            Tuple of required field schemas
        """
        return tuple(field for field in self.fields if not field.is_optional)

    def get_foreign_keys(self) -> tuple[FieldSchema, ...]:
        """Get all foreign key fields.

        Returns:
            Tuple of foreign key field schemas
        """
        return tuple(field for field in self.fields if field.is_foreign_key)
