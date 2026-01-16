"""Protocols for schema parsing strategies.

This module defines the interface that all schema parsers must implement,
enabling support for multiple schema formats (Pydantic, TypeScript, OpenAPI).
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Protocol

# Project/local
from ...core.types import ModelSchema

# =============================================================================
# PUBLIC API
# =============================================================================


class ISchemaParser(Protocol):
    """Protocol for parsing schemas from various sources.

    Current implementations:
        - PydanticSchemaParser: Parse Python Pydantic models

    Future implementations:
        - TypeScriptSchemaParser: Parse TypeScript interfaces
        - OpenAPISchemaParser: Parse OpenAPI 3.x specifications (Issue #9)
        - JSONSchemaParser: Parse JSON Schema definitions

    Example:
        >>> parser = PydanticSchemaParser()
        >>> schemas = parser.parse_file("models.py")
        >>> schemas["User"].fields
        [FieldSchema(name="id", type=int, ...), ...]
    """

    def parse_file(self, file_path: str) -> dict[str, ModelSchema]:
        """Parse schemas from a source file.

        Args:
            file_path: Path to source file containing model definitions

        Returns:
            Dictionary mapping model names to ModelSchema objects

        Raises:
            SchemaParseError: If source cannot be parsed
            SchemaFileNotFoundError: If source file doesn't exist
        """
        ...
