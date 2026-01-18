"""Storage-related exceptions."""

from __future__ import annotations

from typing import Any

from .base import MockAPIError


class StorageError(MockAPIError):
    """Base exception for storage errors."""


class UnsupportedStorageError(StorageError):
    """Storage backend not supported.

    Raised when:
    - Unknown storage URL scheme
    - Storage backend not registered
    """

    def __init__(
        self,
        storage_url: str,
        supported_schemes: list[str] | None = None,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize unsupported storage error.

        Args:
            storage_url: Storage URL that's not supported
            supported_schemes: List of supported URL schemes
            details: Additional context
        """
        self.storage_url = storage_url
        self.supported_schemes = supported_schemes or []

        message = f"Unsupported storage URL: '{storage_url}'"
        if self.supported_schemes:
            message += f". Supported schemes: {', '.join(self.supported_schemes)}"

        super().__init__(message, details=details)
