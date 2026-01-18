"""Service protocols - parsing and validation contracts."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Any, Protocol

# Project/local
from ..value_objects.query import FilterSpec, SortSpec
from ..value_objects.schema import ModelSchema


# =============================================================================
# PROTOCOLS (SERVICES)
# =============================================================================
class IFilterService(Protocol):
    """Parse and validate query filters.

    Converts HTTP query parameters to FilterSpec value objects.
    Supports various operators: eq, ne, gt, gte, lt, lte, in, contains, etc.
    """

    def parse(
        self,
        query_params: dict[str, Any],
        schema: ModelSchema,
    ) -> list[FilterSpec]:
        """Parse query parameters into filter specifications.

        Supported formats:
        - ?name=John -> FilterSpec(field='name', operator='eq', value='John')
        - ?age__gte=18 -> FilterSpec(field='age', operator='gte', value=18)
        - ?status__in=active,pending ->
          FilterSpec(field='status', operator='in', value=['active', 'pending'])

        Args:
            query_params: HTTP query parameters
            schema: Model schema for validation

        Returns:
            List of validated filter specifications

        Raises:
            ValidationError: If filters are invalid or reference unknown fields
        """
        ...

    def validate_filter(
        self,
        filter_spec: FilterSpec,
        schema: ModelSchema,
    ) -> None:
        """Validate single filter against schema.

        Args:
            filter_spec: Filter to validate
            schema: Model schema

        Raises:
            ValidationError: If filter is invalid
        """
        ...


class ISortService(Protocol):
    """Parse and validate sort specifications.

    Converts sort query parameters to SortSpec value objects.
    """

    def parse(
        self,
        sort_param: str | None,
        schema: ModelSchema,
    ) -> list[SortSpec]:
        """Parse sort parameter into sort specifications.

        Supported formats:
        - ?sort=name -> [SortSpec(field='name', direction='asc')]
        - ?sort=-created_at -> [SortSpec(field='created_at', direction='desc')]
        - ?sort=name,-age -> [SortSpec(...), SortSpec(...)]

        Args:
            sort_param: Sort parameter string
            schema: Model schema for validation

        Returns:
            List of validated sort specifications

        Raises:
            ValidationError: If sorts are invalid or reference unknown fields
        """
        ...

    def validate_sort(
        self,
        sort_spec: SortSpec,
        schema: ModelSchema,
    ) -> None:
        """Validate single sort against schema.

        Args:
            sort_spec: Sort to validate
            schema: Model schema

        Raises:
            ValidationError: If sort is invalid
        """
        ...


class IValidationService(Protocol):
    """Validate entity data against schema.

    Used by repositories before persisting data.
    """

    def validate(
        self,
        model_name: str,
        data: dict[str, Any],
        schema: ModelSchema,
        *,
        partial: bool = False,
    ) -> dict[str, Any]:
        """Validate entity data against schema.

        Args:
            model_name: Model name (for error messages)
            data: Entity data to validate
            schema: Model schema
            partial: If True, allow missing required fields (for updates)

        Returns:
            Validated and normalized data

        Raises:
            ValidationError: If data is invalid
        """
        ...

    def validate_field(
        self,
        field_name: str,
        field_value: Any,
        field_schema: Any,
    ) -> Any:
        """Validate single field value.

        Args:
            field_name: Field name
            field_value: Field value to validate
            field_schema: Field schema

        Returns:
            Validated and normalized value

        Raises:
            ValidationError: If field value is invalid
        """
        ...


class IFilterExecutor(Protocol):
    """Execute filter specifications on entity collections.

    Applies FilterSpec value objects to filter entity lists.
    Separates filter execution logic from repositories.
    """

    def apply(
        self,
        entities: list[dict[str, Any]],
        filters: list[FilterSpec] | None,
    ) -> list[dict[str, Any]]:
        """Apply filter specifications to entity list.

        Implementation applies each filter sequentially to narrow results.
        Supports operators: eq, ne, gt, gte, lt, lte, in, nin, contains.

        Args:
            entities: List of entities to filter
            filters: Filter specifications to apply (None = no filtering)

        Returns:
            Filtered entity list

        Example:
            >>> entities = [{"age": 25}, {"age": 30}]
            >>> filters = [FilterSpec(field="age", operator="gte", value=30)]
            >>> executor.apply(entities, filters)
            [{"age": 30}]
        """
        ...


class ISortExecutor(Protocol):
    """Execute sort specifications on entity collections.

    Applies SortSpec value objects to sort entity lists.
    Separates sort execution logic from repositories.
    """

    def apply(
        self,
        entities: list[dict[str, Any]],
        sorts: list[SortSpec] | None,
    ) -> list[dict[str, Any]]:
        """Apply sort specifications to entity list.

        Implementation applies sorts in order of priority.
        Supports directions: asc (ascending), desc (descending).

        Args:
            entities: List of entities to sort
            sorts: Sort specifications to apply (None = no sorting)

        Returns:
            Sorted entity list

        Example:
            >>> entities = [{"name": "Bob"}, {"name": "Alice"}]
            >>> sorts = [SortSpec(field="name", direction="asc")]
            >>> executor.apply(entities, sorts)
            [{"name": "Alice"}, {"name": "Bob"}]
        """
        ...
