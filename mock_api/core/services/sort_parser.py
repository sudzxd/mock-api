"""Sort parameter parser service.

This module provides the SortParser service for parsing and validating
sort query parameters from HTTP requests into typed SortSpec objects.
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Third-party
from fastapi import HTTPException

# Project/local
from ...utils.logger import get_logger
from ..config import Config, get_config
from ..constants import (
    SORT_DESC_PREFIX,
    SORT_FIELD_DELIMITER,
    HTTPStatus,
    SortDirection,
)
from ..protocols import ISortParser
from ..types import ModelSchema, SortSpec

# =============================================================================
# TYPES & CONSTANTS
# =============================================================================
logger = get_logger(__name__)


# =============================================================================
# PUBLIC API
# =============================================================================


class SortParser(ISortParser):
    """Parse and validate sort query parameters.

    Implements ISortParser protocol for dependency injection and extensibility.

    Parses HTTP query parameters into typed SortSpec objects with proper
    validation. Supports ascending/descending sort directions and multiple
    sort fields.
    """

    def __init__(self, config: Config | None = None) -> None:
        """Initialize SortParser with optional config.

        Args:
            config: Configuration instance. If None, loads global config.

        Example:
            >>> parser = SortParser()
            >>> parser = SortParser(config=custom_config)
        """
        self._config = config or get_config()
        logger.debug("Initialized SortParser")

    def parse_param(
        self,
        sort_value: str | None,
        model_name: str,
        schema: ModelSchema,
    ) -> list[SortSpec]:
        """Parse sort query parameter into SortSpec objects.

        Parses HTTP query parameter like ?sort=-created_at,name into
        typed SortSpec objects. Validates field names and enforces
        maximum sort field limits.

        Args:
            sort_value: Sort parameter value (e.g., "-created_at,name").
            model_name: Name of the model being queried.
            schema: Model schema for field validation.

        Returns:
            List of sort specifications.

        Raises:
            HTTPException: If too many sort fields or validation fails.
        """
        if not sort_value:
            return []

        # Parse comma-separated fields
        field_specs = [f.strip() for f in sort_value.split(SORT_FIELD_DELIMITER)]
        sort_specs = [
            self.parse_single(field_spec, model_name, schema)
            for field_spec in field_specs
        ]

        # Check max sort fields limit
        max_sort_fields = self._config.filter_sort.max_sort_fields
        if len(sort_specs) > max_sort_fields:
            logger.warning(
                f"Too many sort fields for {model_name}: "
                f"{len(sort_specs)} > {max_sort_fields}"
            )
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Too many sort fields. Maximum allowed: {max_sort_fields}",
            )

        logger.debug(f"Parsed {len(sort_specs)} sort field(s) for {model_name}")
        return sort_specs

    def parse_single(
        self, field_spec: str, model_name: str, schema: ModelSchema
    ) -> SortSpec:
        """Parse a single sort field specification.

        Parses field specification format: -field (descending) or field
        (ascending).

        Args:
            field_spec: Field specification (e.g., "-created_at" or "name").
            model_name: Name of the model being queried.
            schema: Model schema for field validation.

        Returns:
            SortSpec object.

        Raises:
            HTTPException: If field is invalid.
        """
        # Check for descending prefix
        if field_spec.startswith(SORT_DESC_PREFIX):
            direction = SortDirection.DESC
            field_name = field_spec[1:]
        else:
            direction = SortDirection.ASC
            field_name = field_spec

        # Validate field exists
        self.validate_field(field_name, model_name, schema)

        return SortSpec(field=field_name, direction=direction)

    def validate_field(
        self, field_name: str, model_name: str, schema: ModelSchema
    ) -> None:
        """Validate sort field exists in schema.

        Args:
            field_name: Name of the field to validate.
            model_name: Name of the model being queried.
            schema: Model schema.

        Raises:
            HTTPException: If field doesn't exist.
        """
        field_names = [f.name for f in schema.fields]
        if field_name not in field_names:
            logger.warning(f"Invalid sort field '{field_name}' for {model_name}.")
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Invalid sort field '{field_name}' for {model_name}. "
                f"Available fields: {', '.join(field_names)}",
            )
