"""Sort executor implementation.

Executes sort specifications on entity collections.
Extracted from repository to enable reusability across all storage implementations.
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from operator import itemgetter
from typing import Any

# Project/local
from mock_api.domain.services.protocols import ISortExecutor
from mock_api.domain.value_objects.query import SortDirection, SortSpec


# =============================================================================
# CORE CLASSES
# =============================================================================
class SortExecutor(ISortExecutor):
    """Execute sort specifications on entity lists.

    Applies SortSpec value objects to sort entity collections.
    Supports all SortDirection values defined in domain.

    Stateless service - can be shared across repositories.
    """

    def apply(
        self,
        entities: list[dict[str, Any]],
        sorts: list[SortSpec] | None,
    ) -> list[dict[str, Any]]:
        """Apply sort specifications to entity list.

        Implementation applies sorts in reverse order (last sort has highest priority).
        This allows for stable multi-level sorting.

        Args:
            entities: List of entities to sort
            sorts: Sort specifications to apply (None = no sorting)

        Returns:
            Sorted entity list

        Example:
            >>> executor = SortExecutor()
            >>> entities = [{"name": "Bob"}, {"name": "Alice"}]
            >>> sorts = [SortSpec(field="name", direction="asc")]
            >>> executor.apply(entities, sorts)
            [{"name": "Alice"}, {"name": "Bob"}]
        """
        if not sorts:
            return entities

        # Apply sorts in reverse order (last sort has highest priority)
        # This ensures stable multi-level sorting
        sorted_entities = entities.copy()

        for sort_spec in reversed(sorts):
            sorted_entities = self._apply_single_sort(sorted_entities, sort_spec)

        return sorted_entities

    def _apply_single_sort(
        self,
        entities: list[dict[str, Any]],
        sort_spec: SortSpec,
    ) -> list[dict[str, Any]]:
        """Apply single sort to entity list.

        Args:
            entities: List of entities
            sort_spec: Sort to apply

        Returns:
            Sorted entity list
        """
        field = sort_spec.field
        direction = SortDirection(sort_spec.direction)

        # Determine reverse flag based on direction
        reverse = direction == SortDirection.DESC

        # Sort using itemgetter for performance
        return sorted(entities, key=itemgetter(field), reverse=reverse)
