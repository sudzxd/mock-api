"""Schema-related exceptions."""

from __future__ import annotations

from typing import Any

from .base import MockAPIError


class SchemaError(MockAPIError):
    """Base exception for schema-related errors."""


class SchemaParseError(SchemaError):
    """Failed to parse schema file.

    Raised when:
    - Syntax errors in schema file
    - Invalid schema format
    - Import errors (for Python schemas)
    """

    def __init__(
        self,
        file_path: str,
        reason: str,
        *,
        line_number: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize parse error.

        Args:
            file_path: Path to schema file
            reason: Why parsing failed
            line_number: Line number where error occurred (if known)
            details: Additional context
        """
        self.file_path = file_path
        self.reason = reason
        self.line_number = line_number

        message = f"Failed to parse schema file '{file_path}': {reason}"
        if line_number is not None:
            message += f" (line {line_number})"

        super().__init__(message, details=details)


class SchemaFileNotFoundError(SchemaError):
    """Schema file not found.

    Raised when:
    - File path doesn't exist
    - File is not readable
    """

    def __init__(
        self,
        file_path: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize file not found error.

        Args:
            file_path: Path to schema file
            details: Additional context
        """
        self.file_path = file_path

        message = f"Schema file not found: '{file_path}'"
        super().__init__(message, details=details)


class SchemaValidationError(SchemaError):
    """Schema validation failed.

    Raised when:
    - Invalid foreign key references
    - Circular dependencies
    - Missing required metadata
    - Type inconsistencies
    """

    def __init__(
        self,
        message: str,
        *,
        model_name: str | None = None,
        field_name: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Validation error message
            model_name: Model where validation failed
            field_name: Field where validation failed
            details: Additional context
        """
        self.model_name = model_name
        self.field_name = field_name

        # Build error message
        full_message = "Schema validation failed: " + message
        if model_name:
            full_message += f" (model: {model_name}"
            if field_name:
                full_message += f", field: {field_name}"
            full_message += ")"

        super().__init__(full_message, details=details)


class UnsupportedSchemaError(SchemaError):
    """Schema format not supported.

    Raised when:
    - No parser available for file format
    - File extension not recognized
    """

    def __init__(
        self,
        file_path: str,
        supported_formats: list[str] | None = None,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize unsupported format error.

        Args:
            file_path: Path to schema file
            supported_formats: List of supported file extensions
            details: Additional context
        """
        self.file_path = file_path
        self.supported_formats = supported_formats or []

        message = f"Unsupported schema format: '{file_path}'"
        if self.supported_formats:
            message += f". Supported formats: {', '.join(self.supported_formats)}"

        super().__init__(message, details=details)
