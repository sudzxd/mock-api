"""Repository validation service for data integrity checks.

This module provides validation utilities for repository operations including
batch size validation, primary key validation, and data integrity checks.
"""

from __future__ import annotations

from typing import Any

from ...constants import PRIMARY_KEY_FIELD
from ...exceptions import BatchSizeExceededError


class RepositoryValidator:
    """Validator for repository operations.

    Provides stateless validation methods for CRUD and bulk operations.
    All methods are pure functions with no side effects.

    Example:
        >>> validator = RepositoryValidator()
        >>> validator.validate_batch_size(1000, 500)  # Raises BatchSizeExceededError
        >>> validator.validate_id_present({"id": 1, "name": "Alice"})  # OK
    """

    def validate_batch_size(self, batch_size: int, max_batch_size: int | None) -> None:
        """Validate batch size against maximum allowed.

        Args:
            batch_size: Actual batch size.
            max_batch_size: Maximum allowed batch size (None = no limit).

        Raises:
            BatchSizeExceededError: If batch size exceeds maximum.

        Example:
            >>> validator.validate_batch_size(100, 1000)  # OK
            >>> validator.validate_batch_size(2000, 1000)  # Raises error
        """
        if max_batch_size and batch_size > max_batch_size:
            raise BatchSizeExceededError(batch_size, max_batch_size)

    def validate_id_present(self, data: dict[str, Any]) -> None:
        """Validate that primary key field is present in data.

        Args:
            data: Dictionary to validate.

        Raises:
            ValueError: If primary key field is missing.

        Example:
            >>> validator.validate_id_present({"id": 1, "name": "Alice"})  # OK
            >>> validator.validate_id_present({"name": "Bob"})  # Raises ValueError
        """
        if PRIMARY_KEY_FIELD not in data:
            raise ValueError(f"Missing required field '{PRIMARY_KEY_FIELD}' for update")

    def validate_id_type(self, instance_id: Any) -> None:
        """Validate that instance ID is of correct type.

        Args:
            instance_id: ID to validate.

        Raises:
            TypeError: If ID is not an integer.

        Example:
            >>> validator.validate_id_type(123)  # OK
            >>> validator.validate_id_type("123")  # Raises TypeError
        """
        if not isinstance(instance_id, int):
            raise TypeError(
                f"Instance ID must be int, got {type(instance_id).__name__}"
            )
