"""Sort parsing service implementation."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Project/local
from mock_api.core.exceptions import ValidationError
from mock_api.domain.services.protocols import ISortService
from mock_api.domain.value_objects.query import SortSpec
from mock_api.domain.value_objects.schema import ModelSchema


# =============================================================================
# CORE CLASSES
# =============================================================================
class SortService(ISortService):
    """Parse sort parameters into sort specifications.

    Supported formats:
    - ?sort=name -> [SortSpec(field='name', direction='asc')]
    - ?sort=-created_at -> [SortSpec(field='created_at', direction='desc')]
    - ?sort=name,-age -> [SortSpec(...), SortSpec(...)]
    """

    def __init__(self) -> None:
        """Initialize sort service."""
        pass  # Stateless service

    def parse(
        self,
        sort_param: str | None,
        schema: ModelSchema,
    ) -> list[SortSpec]:
        """Parse sort parameter into sort specifications.

        Implementation:
        1. Split by comma
        2. For each field:
           - Check for '-' prefix (desc)
           - Validate field exists
           - Create SortSpec

        Args:
            sort_param: Sort parameter string
            schema: Model schema

        Returns:
            List of sort specifications

        Raises:
            ValidationError: If sorts are invalid
        """
        if not sort_param:
            return []

        sorts: list[SortSpec] = []

        # Split by comma
        sort_strings = [s.strip() for s in sort_param.split(",")]

        for sort_str in sort_strings:
            if not sort_str:
                continue

            # Parse single sort
            sort_spec = self._parse_single_sort(sort_str, schema)

            # Validate sort
            self.validate_sort(sort_spec, schema)

            sorts.append(sort_spec)

        return sorts

    def validate_sort(
        self,
        sort_spec: SortSpec,
        schema: ModelSchema,
    ) -> None:
        """Validate sort against schema.

        Args:
            sort_spec: Sort to validate
            schema: Model schema

        Raises:
            ValidationError: If sort is invalid
        """
        # Validate field exists
        if not schema.has_field(sort_spec.field):
            raise ValidationError(
                message=f"Field '{sort_spec.field}' not found in model '{schema.name}'",
                model_name=schema.name,
            )

    def _parse_single_sort(
        self,
        sort_str: str,
        _schema: ModelSchema,
    ) -> SortSpec:
        """Parse single sort string to SortSpec.

        Args:
            sort_str: Sort string (e.g., 'name', '-age')
            _schema: Model schema (reserved for future use)

        Returns:
            SortSpec instance

        Raises:
            ValidationError: If parsing fails
        """
        # Check for '-' prefix (descending)
        if sort_str.startswith("-"):
            field_name = sort_str[1:]  # Remove '-' prefix
            direction = "desc"
        else:
            field_name = sort_str
            direction = "asc"

        return SortSpec(field=field_name, direction=direction)
