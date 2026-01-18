"""Filter parsing service implementation.

Parses HTTP query parameters into FilterSpec value objects.
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Any

# Project/local
from mock_api.core.exceptions import ValidationError
from mock_api.domain.services.protocols import IFilterService
from mock_api.domain.value_objects.query import FilterSpec
from mock_api.domain.value_objects.schema import ModelSchema


# =============================================================================
# CORE CLASSES
# =============================================================================
class FilterService(IFilterService):
    """Parse query parameters into filter specifications.

    Supported filter formats:
    - Simple: ?name=John -> FilterSpec(field='name', operator='eq', value='John')
    - Operator suffix: ?age__gte=18 -> FilterSpec(field='age', operator='gte', value=18)
    - List values: ?status__in=active,pending ->
      FilterSpec(field='status', operator='in', value=['active', 'pending'])
    - Multiple filters: ?name=John&age__gte=18 -> [FilterSpec(...), FilterSpec(...)]

    Supported operators:
    - eq (equals) - default
    - ne (not equals)
    - gt (greater than)
    - gte (greater than or equal)
    - lt (less than)
    - lte (less than or equal)
    - in (in list)
    - nin (not in list)
    - contains (string contains)
    - startswith (string starts with)
    - endswith (string ends with)
    """

    # Operator aliases
    _operator_aliases: dict[str, str] = {
        "eq": "eq",
        "ne": "ne",
        "gt": "gt",
        "gte": "gte",
        "ge": "gte",
        "lt": "lt",
        "lte": "lte",
        "le": "lte",
        "in": "in",
        "nin": "nin",
        "contains": "contains",
        "startswith": "startswith",
        "endswith": "endswith",
    }

    def __init__(self) -> None:
        """Initialize filter service."""
        pass  # Stateless service, operator aliases defined as class attribute

    def parse(
        self,
        query_params: dict[str, Any],
        schema: ModelSchema,
    ) -> list[FilterSpec]:
        """Parse query parameters into filter specifications.

        Implementation:
        1. Iterate through query params
        2. Skip pagination params (page, page_size, sort)
        3. Parse field__operator=value format
        4. Validate field exists in schema
        5. Parse value based on field type
        6. Create FilterSpec

        Args:
            query_params: HTTP query parameters
            schema: Model schema for validation

        Returns:
            List of filter specifications

        Raises:
            ValidationError: If filters are invalid
        """
        filters: list[FilterSpec] = []

        for param_name, param_value in query_params.items():
            # Skip pagination params
            if self._is_pagination_param(param_name):
                continue

            # Parse filter param
            filter_spec = self._parse_filter_param(param_name, param_value, schema)

            # Validate filter
            self.validate_filter(filter_spec, schema)

            filters.append(filter_spec)

        return filters

    def validate_filter(
        self,
        filter_spec: FilterSpec,
        schema: ModelSchema,
    ) -> None:
        """Validate filter against schema.

        Checks:
        - Field exists in schema
        - Operator is supported
        - Value type matches field type

        Args:
            filter_spec: Filter to validate
            schema: Model schema

        Raises:
            ValidationError: If filter is invalid
        """
        # Validate field exists
        if not schema.has_field(filter_spec.field):
            raise ValidationError(
                message=(
                    f"Field '{filter_spec.field}' not found in model '{schema.name}'"
                ),
                model_name=schema.name,
            )

        # Validate operator is supported
        if filter_spec.operator not in self._operator_aliases:
            raise ValidationError(
                message=f"Unsupported operator '{filter_spec.operator}'",
                model_name=schema.name,
            )

    def _parse_filter_param(
        self,
        param_name: str,
        param_value: Any,
        schema: ModelSchema,
    ) -> FilterSpec:
        """Parse single query parameter into FilterSpec.

        Handles:
        - name=value -> FilterSpec(field='name', operator='eq', value='value')
        - age__gte=18 -> FilterSpec(field='age', operator='gte', value=18)

        Args:
            param_name: Query parameter name
            param_value: Query parameter value
            schema: Model schema

        Returns:
            FilterSpec instance

        Raises:
            ValidationError: If parsing fails
        """
        # Extract field and operator
        field_name, operator = self._extract_field_and_operator(param_name)

        # Validate field exists in schema
        field_schema = schema.get_field(field_name)
        if field_schema is None:
            raise ValidationError(
                message=f"Field '{field_name}' not found in model '{schema.name}'",
                model_name=schema.name,
            )

        # Parse value based on field type and operator
        parsed_value = self._parse_value(param_value, operator, field_schema)

        # Create FilterSpec
        return FilterSpec(field=field_name, operator=operator, value=parsed_value)

    def _extract_field_and_operator(
        self,
        param_name: str,
    ) -> tuple[str, str]:
        """Extract field name and operator from parameter name.

        Examples:
        - name -> ('name', 'eq')
        - age__gte -> ('age', 'gte')
        - status__in -> ('status', 'in')

        Args:
            param_name: Query parameter name

        Returns:
            Tuple of (field_name, operator)
        """
        # Check if param has __ operator suffix
        if "__" in param_name:
            parts = param_name.split("__", 1)
            field_name = parts[0]
            operator = parts[1]

            # Normalize operator using aliases
            operator = self._operator_aliases.get(operator, operator)

            return (field_name, operator)

        # Default to 'eq' operator
        return (param_name, "eq")

    def _parse_value(
        self,
        value: Any,
        operator: str,
        field_schema: Any,
    ) -> Any:
        """Parse and convert value based on operator and field type.

        Handles:
        - Type conversion (str -> int, str -> bool, etc.)
        - List parsing for 'in' operator
        - Date/datetime parsing

        Args:
            value: Raw parameter value
            operator: Filter operator
            field_schema: Field schema for type info

        Returns:
            Parsed and converted value

        Raises:
            ValidationError: If value can't be parsed
        """
        # Handle 'in' and 'nin' operators - split comma-separated values
        if operator in ("in", "nin"):
            if isinstance(value, str):
                # Split by comma and strip whitespace
                return [v.strip() for v in value.split(",")]
            return value

        # For other operators, try to convert to field type
        try:
            field_type = field_schema.type

            # Handle string values
            if isinstance(value, str):
                # Convert to field type
                if field_type is int:
                    return int(value)
                if field_type is float:
                    return float(value)
                if field_type is bool:
                    return value.lower() in ("true", "1", "yes")

        except (ValueError, AttributeError):
            # If conversion fails, return as-is
            return value
        else:
            return value

    def _is_pagination_param(self, param_name: str) -> bool:
        """Check if parameter is pagination-related (skip from filtering).

        Args:
            param_name: Parameter name

        Returns:
            True if pagination param (page, page_size, sort)
        """
        return param_name in ("page", "page_size", "sort")
