"""Validation exceptions."""

from __future__ import annotations

from typing import Any

from .base import MockAPIError


class ValidationError(MockAPIError):
    """Data validation failed.

    Raised when:
    - Entity data doesn't match schema
    - Missing required fields
    - Type mismatches
    - Invalid field values
    - Invalid filter/sort specifications
    """

    def __init__(
        self,
        message: str,
        *,
        model_name: str | None = None,
        field_name: str | None = None,
        field_value: Any = None,
        expected_type: type | None = None,
        actual_type: type | None = None,
        errors: list[dict[str, Any]] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Validation error message
            model_name: Model being validated
            field_name: Field that failed validation
            field_value: Invalid value
            expected_type: Expected type
            actual_type: Actual type received
            errors: List of validation errors (for multiple failures)
            details: Additional context
        """
        self.model_name = model_name
        self.field_name = field_name
        self.field_value = field_value
        self.expected_type = expected_type
        self.actual_type = actual_type
        self.errors = errors or []

        # Build error message
        full_message = "Validation failed: " + message

        # Add model/field context
        if model_name:
            full_message += f" (model: {model_name}"
            if field_name:
                full_message += f", field: {field_name}"
            full_message += ")"

        # Add type mismatch info
        if expected_type and actual_type:
            full_message += (
                f" - expected {expected_type.__name__}, got {actual_type.__name__}"
            )

        super().__init__(full_message, details=details)
