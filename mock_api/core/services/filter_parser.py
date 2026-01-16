"""Filter parameter parser service.

This module provides the FilterParser service for parsing and validating
filter query parameters from HTTP requests into typed FilterSpec objects.
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Any

# Third-party
from fastapi import HTTPException
from pydantic import TypeAdapter
from starlette.datastructures import QueryParams

# Project/local
from ...utils.logger import get_logger
from ..config import Config, get_config
from ..constants import (
    FILTER_OPERATOR_DELIMITER,
    IN_OPERATOR_DELIMITER,
    FilterOperator,
    HTTPStatus,
    QueryParam,
)
from ..protocols import IFilterParser
from ..types import FieldSchema, FilterSpec, ModelSchema

# =============================================================================
# TYPES & CONSTANTS
# =============================================================================
logger = get_logger(__name__)

# Query parameter values
NULL_VALUE_STRING = "null"


# =============================================================================
# PUBLIC API
# =============================================================================


class FilterParser(IFilterParser):
    """Parse and validate filter query parameters.

    Implements IFilterParser protocol for dependency injection and extensibility.

    Parses HTTP query parameters into typed FilterSpec objects with proper
    validation and type coercion. Supports multiple filter operators and
    handles complex types including enums, datetimes, and lists.
    """

    def __init__(self, config: Config | None = None) -> None:
        """Initialize FilterParser with optional config.

        Args:
            config: Configuration instance. If None, loads global config.

        Example:
            >>> parser = FilterParser()
            >>> parser = FilterParser(config=custom_config)
        """
        self._config = config or get_config()
        logger.debug("Initialized FilterParser")

    def parse_params(
        self,
        query_params: QueryParams,
        model_name: str,
        schema: ModelSchema,
    ) -> list[FilterSpec]:
        """Parse filter query parameters into FilterSpec objects.

        Parses HTTP query parameters like ?age__gte=18&name=John into
        typed FilterSpec objects. Validates field names, operators, and
        coerces values to appropriate types.

        Args:
            query_params: Raw query parameters from HTTP request.
            model_name: Name of the model being queried.
            schema: Model schema for field validation.

        Returns:
            List of filter specifications.

        Raises:
            HTTPException: If too many filters or validation fails.
        """
        filters: list[FilterSpec] = []
        reserved_params = {
            QueryParam.PAGE,
            QueryParam.PAGE_SIZE,
            QueryParam.OFFSET,
            QueryParam.LIMIT,
            QueryParam.SORT,
        }

        for param_name, param_value in query_params.items():
            if param_name in reserved_params:
                continue

            filter_spec = self.parse_single(param_name, param_value, model_name, schema)
            filters.append(filter_spec)

        # Check max filters limit
        max_filters = self._config.filter_sort.max_filters
        if len(filters) > max_filters:
            logger.warning(
                f"Too many filters for {model_name}: {len(filters)} > {max_filters}"
            )
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Too many filters. Maximum allowed: {max_filters}",
            )

        logger.debug(f"Parsed {len(filters)} filter(s) for {model_name}")
        return filters

    def parse_single(
        self,
        param_name: str,
        param_value: str,
        model_name: str,
        schema: ModelSchema,
    ) -> FilterSpec:
        """Parse a single filter parameter into FilterSpec.

        Parses query parameter format: field__operator=value or field=value
        (implicit eq operator).

        Args:
            param_name: Query parameter name (e.g., "age__gte" or "name").
            param_value: Query parameter value.
            model_name: Name of the model being queried.
            schema: Model schema for field validation.

        Returns:
            FilterSpec object.

        Raises:
            HTTPException: If field, operator, or value is invalid.
        """
        # Parse field__operator or field (implicit eq)
        if FILTER_OPERATOR_DELIMITER in param_name:
            field_name, operator_str = param_name.split(FILTER_OPERATOR_DELIMITER, 1)
        else:
            field_name, operator_str = param_name, FilterOperator.EQ

        # Validate and get field schema
        field_schema = self.validate_field(field_name, model_name, schema)

        # Validate and get operator enum
        operator = self.validate_operator(operator_str)

        # Coerce value based on field type
        try:
            coerced_value = self.coerce_value(param_value, field_schema, operator)
        except ValueError as e:
            logger.warning(f"Invalid value for {field_name} in {model_name}: {str(e)}")
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Invalid value for {field_name}: {str(e)}",
            ) from e

        return FilterSpec(field=field_name, operator=operator, value=coerced_value)

    def validate_field(
        self,
        field_name: str,
        model_name: str,
        schema: ModelSchema,
    ) -> FieldSchema:
        """Validate filter field exists in schema.

        Args:
            field_name: Name of the field to validate.
            model_name: Name of the model being queried.
            schema: Model schema.

        Returns:
            FieldSchema for the validated field.

        Raises:
            HTTPException: If field doesn't exist.
        """
        field_map = {f.name: f for f in schema.fields}
        if field_name not in field_map:
            logger.warning(f"Invalid filter field '{field_name}' for {model_name}.")
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Invalid filter field '{field_name}' for {model_name}.",
            )
        return field_map[field_name]

    def validate_operator(self, operator_str: str) -> FilterOperator:
        """Validate filter operator is supported.

        Args:
            operator_str: Operator string (e.g., "gte", "contains").

        Returns:
            FilterOperator enum value.

        Raises:
            HTTPException: If operator is invalid.
        """
        try:
            return FilterOperator(operator_str)
        except ValueError as e:
            logger.warning(f"Invalid filter operator: '{operator_str}'")
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Invalid filter operator '{operator_str}'. ",
            ) from e

    def coerce_value(
        self,
        value: str,
        field_schema: FieldSchema,
        operator: FilterOperator,
    ) -> Any:
        """Coerce string query parameter to field type.

        Handles special cases:
        - "null" → None
        - IN operator → list of coerced values
        - Type-specific coercion (int, bool, datetime, enum, etc.)

        Args:
            value: Raw string value from query parameter.
            field_schema: Schema of the field being filtered.
            operator: Filter operator being used.

        Returns:
            Type-coerced value.

        Raises:
            ValueError: If coercion fails.
        """
        if value.lower() == NULL_VALUE_STRING:
            return None

        if operator == FilterOperator.IN:
            value_list = [v.strip() for v in value.split(IN_OPERATOR_DELIMITER)]
            return [self.coerce_single_value(v, field_schema) for v in value_list]

        return self.coerce_single_value(value, field_schema)

    def coerce_single_value(self, value: str, field_schema: FieldSchema) -> Any:
        """Coerce a single value based on field type using Pydantic.

        Uses Pydantic's TypeAdapter for robust type coercion, automatically
        handling int, float, bool, str, datetime, date, and Enum types.

        Args:
            value: Raw string value.
            field_schema: Schema of the field.

        Returns:
            Type-coerced value.

        Raises:
            ValueError: If coercion fails.
        """
        try:
            adapter: TypeAdapter[Any] = TypeAdapter(field_schema.type)
            return adapter.validate_python(value)
        except Exception as e:
            if field_schema.is_enum:
                valid_values = ", ".join(str(v) for v in field_schema.enum_values)
                raise ValueError(
                    f"Invalid value '{value}' for enum. Valid values: {valid_values}"
                ) from e
            raise ValueError(
                f"Cannot convert '{value}' to {field_schema.type.__name__}"
            ) from e
