"""Base exception classes."""

from __future__ import annotations

from typing import Any


class MockAPIError(Exception):
    """Base exception for all MockAPI errors.

    All custom exceptions inherit from this for easy catching.
    """

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize exception.

        Args:
            message: Error message
            details: Additional error context (for debugging/logging)
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """String representation."""
        return self.message

    def __repr__(self) -> str:
        """Developer representation."""
        return f"{self.__class__.__name__}({self.message!r})"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses.

        Returns:
            Dict with error info (message, type, details)
        """
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }
