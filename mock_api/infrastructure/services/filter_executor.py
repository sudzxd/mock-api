"""Filter executor implementation.

Executes filter specifications on entity collections.
Extracted from repository to enable reusability across all storage implementations.
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Any

# Project/local
from mock_api.domain.services.protocols import IFilterExecutor
from mock_api.domain.value_objects.query import FilterOperator, FilterSpec


# =============================================================================
# CORE CLASSES
# =============================================================================
class FilterExecutor(IFilterExecutor):
    """Execute filter specifications on entity lists.

    Applies FilterSpec value objects to filter entity collections.
    Supports all FilterOperator values defined in domain.

    Stateless service - can be shared across repositories.
    """

    def apply(
        self,
        entities: list[dict[str, Any]],
        filters: list[FilterSpec] | None,
    ) -> list[dict[str, Any]]:
        """Apply filter specifications to entity list.

        Implementation applies each filter sequentially to narrow results.

        Args:
            entities: List of entities to filter
            filters: Filter specifications to apply (None = no filtering)

        Returns:
            Filtered entity list

        Example:
            >>> executor = FilterExecutor()
            >>> entities = [{"age": 25}, {"age": 30}, {"age": 35}]
            >>> filters = [FilterSpec(field="age", operator="gte", value=30)]
            >>> executor.apply(entities, filters)
            [{"age": 30}, {"age": 35}]
        """
        if not filters:
            return entities

        filtered: list[dict[str, Any]] = entities

        for filter_spec in filters:
            filtered = self._apply_single_filter(filtered, filter_spec)

        return filtered

    def _apply_single_filter(
        self,
        entities: list[dict[str, Any]],
        filter_spec: FilterSpec,
    ) -> list[dict[str, Any]]:
        """Apply single filter to entity list.

        Args:
            entities: List of entities
            filter_spec: Filter to apply

        Returns:
            Filtered entity list
        """
        field = filter_spec.field
        operator = FilterOperator(filter_spec.operator)
        value = filter_spec.value

        # Use match statement for cleaner operator handling
        match operator:
            case FilterOperator.EQ:
                return [e for e in entities if e.get(field) == value]

            case FilterOperator.NE:
                return [e for e in entities if e.get(field) != value]

            case FilterOperator.GT:
                return [
                    e
                    for e in entities
                    if e.get(field) is not None and e.get(field) > value
                ]

            case FilterOperator.GTE:
                return [
                    e
                    for e in entities
                    if e.get(field) is not None and e.get(field) >= value
                ]

            case FilterOperator.LT:
                return [
                    e
                    for e in entities
                    if e.get(field) is not None and e.get(field) < value
                ]

            case FilterOperator.LTE:
                return [
                    e
                    for e in entities
                    if e.get(field) is not None and e.get(field) <= value
                ]

            case FilterOperator.IN:
                return [e for e in entities if e.get(field) in value]

            case FilterOperator.NIN:
                return [e for e in entities if e.get(field) not in value]

            case FilterOperator.CONTAINS:
                return [
                    e
                    for e in entities
                    if isinstance(e.get(field), str) and value in e.get(field, "")
                ]

            case _:
                # Unknown operator - return unfiltered
                # (should not happen with validation)
                return entities
