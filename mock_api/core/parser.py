"""Schema parser for extracting model definitions from Pydantic files.

This module provides a facade/delegate to the schema parser implementation.
Delegates to: mock_api/implementations/parsing/pydantic_parser.py
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Project/local
from ..implementations.parsing import PydanticSchemaParser
from .types import ModelSchema

# =============================================================================
# PUBLIC API
# =============================================================================


class SchemaParser:
    """Facade for schema parsing that delegates to implementation layer.

    This class provides a stable interface while delegating actual parsing
    to the implementation layer, following the facade pattern.
    """

    def __init__(self) -> None:
        """Initialize parser with Pydantic implementation."""
        self._parser = PydanticSchemaParser()

    def parse_file(self, file_path: str) -> dict[str, ModelSchema]:
        """Parse schemas from a Python file containing Pydantic models.

        Args:
            file_path: Path to Python file with Pydantic models

        Returns:
            Dictionary mapping model names to ModelSchema objects

        Raises:
            SchemaFileNotFoundError: If file doesn't exist
            SchemaParseError: If file cannot be parsed
            SchemaValidationError: If models are invalid
        """
        return self._parser.parse_file(file_path)

    def get_models_with_field(self, field_name: str) -> set[str]:
        """Get all model names that contain a specific field.

        Args:
            field_name: Name of the field to search for

        Returns:
            Set of model names containing the field
        """
        return self._parser.get_models_with_field(field_name)

    def get_models_with_type(self, field_type: type) -> set[str]:
        """Get all model names that contain fields of a specific type.

        Args:
            field_type: Python type to search for

        Returns:
            Set of model names containing fields of the given type
        """
        return self._parser.get_models_with_type(field_type)

    def has_field(self, model_name: str, field_name: str) -> bool:
        """Check if a model has a specific field.

        Args:
            model_name: Name of the model
            field_name: Name of the field

        Returns:
            True if model has the field, False otherwise
        """
        return self._parser.has_field(model_name, field_name)
