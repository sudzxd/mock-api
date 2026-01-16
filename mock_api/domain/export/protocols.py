"""Protocols for API collection export strategies.

This module defines the interface for exporting API schemas to various
testing tool formats (Postman, Insomnia, HTTPie, etc.).

TODO: Implement for Issue #47
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


class IExportStrategy(Protocol):
    """Protocol for API collection exporters.

    Future implementations (Issue #47):
        - PostmanExporter: Export to Postman Collection v2.1
        - InsomniaExporter: Export to Insomnia v4
        - HTTPieExporter: Export to .http files
        - OpenAPIExporter: Export to OpenAPI 3.x spec (Issue #9)

    Example usage (future):
        >>> exporter = PostmanExporter()
        >>> collection = exporter.export(schemas, config)
        >>> with open("api.postman.json", "w") as f:
        ...     f.write(collection)
    """

    def export(self, schemas: dict[str, ModelSchema], config: ExportConfig) -> str:
        """Export schemas to collection format.

        Args:
            schemas: Dictionary of model schemas
            config: Export configuration (base URL, examples, etc.)

        Returns:
            Exported collection as string (JSON/text format)

        Note:
            Should generate realistic example data for requests.
            Should include all CRUD + bulk operations.
        """
        ...

    def get_format_name(self) -> str:
        """Get the name of this export format.

        Returns:
            Format name (e.g., "postman", "insomnia", "httpie")
        """
        ...


class ExportConfig:
    """Configuration for export operations.

    Attributes:
        base_url: Base URL for API endpoints
        generate_examples: Whether to include example request bodies
        include_bulk: Whether to include bulk operation endpoints
    """

    def __init__(
        self,
        base_url: str = "http://localhost:3000/api/v1",
        generate_examples: bool = True,
        include_bulk: bool = True,
    ) -> None:
        self.base_url = base_url
        self.generate_examples = generate_examples
        self.include_bulk = include_bulk
