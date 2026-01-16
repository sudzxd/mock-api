"""Protocols for data import/export strategies.

This module defines interfaces for importing and exporting runtime data
in various formats (JSON, CSV, etc.).

TODO: Implement for Issue #46
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Any, Protocol

# =============================================================================
# PUBLIC API
# =============================================================================


class IDataImporter(Protocol):
    """Protocol for data import strategies.

    Future implementations (Issue #46):
        - JSONDataImporter: Import from JSON files
        - CSVDataImporter: Import from CSV files
        - SQLDumpImporter: Import from SQL dump files

    Example usage (future):
        >>> importer = JSONDataImporter()
        >>> result = importer.import_data("seed-data.json")
        >>> result.created_count
        150
    """

    def import_data(self, source: str) -> ImportResult:
        """Import data from a source file.

        Args:
            source: Path to data file

        Returns:
            Import result with counts and errors

        Raises:
            ImportError: If data cannot be imported
        """
        ...

    def supports_format(self, file_path: str) -> bool:
        """Check if this importer supports the file format.

        Args:
            file_path: Path to file

        Returns:
            True if format is supported
        """
        ...


class IDataExporter(Protocol):
    """Protocol for data export strategies.

    Future implementations (Issue #46):
        - JSONDataExporter: Export to JSON files
        - CSVDataExporter: Export to CSV files
        - SQLDumpExporter: Export to SQL dump files

    Example usage (future):
        >>> exporter = JSONDataExporter()
        >>> data = exporter.export_data(models)
        >>> with open("backup.json", "w") as f:
        ...     f.write(data)
    """

    def export_data(self, models: dict[str, list[dict[str, Any]]]) -> str:
        """Export model data to string format.

        Args:
            models: Dictionary mapping model names to instance lists

        Returns:
            Exported data as string

        Note:
            Should handle datetime serialization properly.
        """
        ...

    def get_format_name(self) -> str:
        """Get the name of this export format.

        Returns:
            Format name (e.g., "json", "csv")
        """
        ...


class ImportResult:
    """Result of data import operation.

    Attributes:
        created_count: Number of instances created
        updated_count: Number of instances updated
        error_count: Number of errors
        errors: List of error messages
    """

    def __init__(
        self,
        created_count: int = 0,
        updated_count: int = 0,
        error_count: int = 0,
        errors: list[str] | None = None,
    ) -> None:
        self.created_count = created_count
        self.updated_count = updated_count
        self.error_count = error_count
        self.errors = errors or []
