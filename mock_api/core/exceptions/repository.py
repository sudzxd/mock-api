"""Repository/storage-related exceptions."""

from __future__ import annotations

from typing import Any

from .base import MockAPIError


class RepositoryError(MockAPIError):
    """Base exception for repository errors."""


class ModelNotFoundError(RepositoryError):
    """Model/collection doesn't exist in schema.

    Raised when:
    - Attempting operations on unknown model
    - Model name typo
    """

    def __init__(
        self,
        model_name: str,
        available_models: list[str] | None = None,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize model not found error.

        Args:
            model_name: Model name that wasn't found
            available_models: List of available model names
            details: Additional context
        """
        self.model_name = model_name
        self.available_models = available_models or []

        # Build error message
        message = f"Model '{model_name}' not found"
        if self.available_models:
            message += f". Available models: {', '.join(self.available_models)}"

        super().__init__(message, details=details)


class EntityNotFoundError(RepositoryError):
    """Entity with given ID doesn't exist.

    Raised when:
    - GET/UPDATE/DELETE on non-existent ID
    """

    def __init__(
        self,
        model_name: str,
        entity_id: int,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize entity not found error.

        Args:
            model_name: Model name
            entity_id: Entity ID that wasn't found
            details: Additional context
        """
        self.model_name = model_name
        self.entity_id = entity_id

        message = f"Entity with ID {entity_id} not found in model '{model_name}'"
        super().__init__(message, details=details)


class DuplicateKeyError(RepositoryError):
    """Unique constraint violation.

    Raised when:
    - Creating entity with duplicate unique field
    - Updating entity causing duplicate
    """

    def __init__(
        self,
        model_name: str,
        field_name: str,
        field_value: Any,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize duplicate key error.

        Args:
            model_name: Model name
            field_name: Field with unique constraint
            field_value: Duplicate value
            details: Additional context
        """
        self.model_name = model_name
        self.field_name = field_name
        self.field_value = field_value

        message = (
            f"Duplicate value '{field_value}' for field '{field_name}' "
            f"in model '{model_name}'"
        )
        super().__init__(message, details=details)


class BulkOperationError(RepositoryError):
    """Bulk operation failed with partial results.

    Raised when:
    - Bulk operation fails mid-way
    - Some items succeeded, some failed
    - Contains partial results for debugging
    """

    def __init__(
        self,
        operation: str,  # 'create', 'update', 'delete'
        total: int,
        succeeded: int,
        failed: int,
        errors: list[dict[str, Any]],
        *,
        partial_results: list[Any] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize bulk operation error.

        Args:
            operation: Operation type
            total: Total items attempted
            succeeded: Number of successful operations
            failed: Number of failed operations
            errors: List of error details for failed items
            partial_results: Successfully processed items
            details: Additional context
        """
        self.operation = operation
        self.total = total
        self.succeeded = succeeded
        self.failed = failed
        self.errors = errors
        self.partial_results = partial_results or []

        message = (
            f"Bulk {operation} operation failed: {succeeded}/{total} succeeded, "
            f"{failed} failed"
        )
        super().__init__(message, details=details)
