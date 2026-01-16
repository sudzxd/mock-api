"""Result builder utility for bulk operations.

This module provides utilities for building standardized result dictionaries
for bulk CRUD operations.
"""

from __future__ import annotations

from typing import Any

from ..constants import BulkResponseKey
from ..types import BulkOperationError


class ResultBuilder:
    """Builder for standardized bulk operation results.

    Provides consistent result formatting across all bulk operations.
    All methods are stateless utility functions.

    Example:
        >>> builder = ResultBuilder()
        >>> result = builder.build_bulk_result("created", 10, items, [])
        >>> result
        {'created': 10, 'data': [...], 'errors': []}
    """

    @staticmethod
    def build_bulk_result(
        operation_key: str,
        count: int,
        data: list[dict[str, Any]] | list[int],
        errors: list[BulkOperationError] | None = None,
        data_key: str = BulkResponseKey.DATA,
    ) -> dict[str, Any]:
        """Build standardized bulk operation result.

        Args:
            operation_key: Result key (e.g., "created", "updated", "deleted").
            count: Number of successful operations.
            data: List of data items or IDs.
            errors: List of errors that occurred (optional).
            data_key: Key for data in result (default: "data", or "ids" for delete).

        Returns:
            Standardized result dictionary with keys:
            - {operation_key}: count of successful operations
            - {data_key}: list of data items or IDs
            - errors (optional): list of error dictionaries if any errors occurred

        Example:
            >>> errors = [BulkOperationError(0, {"name": "Alice"}, "Duplicate")]
            >>> result = ResultBuilder.build_bulk_result("created", 2, items, errors)
            >>> result.keys()
            dict_keys(['created', 'data', 'errors'])
        """
        result = {operation_key: count, data_key: data}
        if errors:
            result[BulkResponseKey.ERRORS] = [
                {"index": e.index, "item": e.item, "error": e.error} for e in errors
            ]
        return result
