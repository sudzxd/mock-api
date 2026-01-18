"""Data generation exceptions."""

from __future__ import annotations

from typing import Any

from .base import MockAPIError


class GenerationError(MockAPIError):
    """Failed to generate fake data.

    Raised when:
    - Cannot generate value for field type
    - Dependency resolution fails (foreign keys)
    - Generator configuration invalid
    """

    def __init__(
        self,
        message: str,
        *,
        model_name: str | None = None,
        field_name: str | None = None,
        field_type: type | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize generation error.

        Args:
            message: Error message
            model_name: Model being generated
            field_name: Field that failed generation
            field_type: Field type
            details: Additional context
        """
        ...
