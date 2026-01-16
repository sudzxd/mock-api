"""Pydantic model factory service.

This module provides the ModelFactory service for creating Pydantic models
from ModelSchema definitions for use in FastAPI route handlers.
"""

# pyright: reportArgumentType=false, reportCallIssue=false

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Any, cast

# Third-party
from pydantic import BaseModel, create_model

# Project/local
from ...utils.logger import get_logger
from ..constants import PRIMARY_KEY_FIELD, ModelName, ResponseKey
from ..protocols import IModelFactory
from ..types import ModelSchema

# =============================================================================
# TYPES & CONSTANTS
# =============================================================================
logger = get_logger(__name__)


# =============================================================================
# PUBLIC API
# =============================================================================


class ModelFactory(IModelFactory):
    """Factory for creating Pydantic models from schemas.

    Implements IModelFactory protocol for dependency injection and extensibility.

    Creates three types of models:
    1. Response models - Full model with all fields (uses original Pydantic model)
    2. Input models - Excludes ID field for POST/PUT requests
    3. List response models - Wraps items in pagination response

    Example:
        >>> factory = ModelFactory()
        >>> response_model = factory.create_response_model(user_schema)
        >>> input_model = factory.create_input_model(user_schema)
        >>> list_model = factory.create_list_response_model(response_model)
    """

    def __init__(self) -> None:
        """Initialize ModelFactory.

        Example:
            >>> factory = ModelFactory()
        """
        logger.debug("Initialized ModelFactory")

    def create_response_model(self, schema: ModelSchema) -> type[BaseModel]:
        """Create Pydantic response model from schema.

        Uses the original Pydantic model from the schema for full type safety
        and validation. This model includes all fields including the ID.

        Args:
            schema: Model schema containing field definitions.

        Returns:
            Pydantic model class for API responses.

        Raises:
            ValueError: If schema is missing pydantic_model.

        Example:
            >>> response_model = factory.create_response_model(user_schema)
            >>> instance = response_model(id=1, name="Alice", email="alice@example.com")
        """
        if schema.pydantic_model is None:
            raise ValueError(f"Schema for {schema.name} missing pydantic_model")

        logger.debug(f"Created response model for {schema.name}")
        return schema.pydantic_model

    def create_input_model(self, schema: ModelSchema) -> type[BaseModel]:
        """Create Pydantic input model from schema (excludes ID field).

        Input models are used for POST/PUT requests where the ID is
        auto-generated (POST) or provided separately in the path (PUT).

        The ID field is excluded from the input model since it's not
        part of the request body.

        Args:
            schema: Model schema containing field definitions.

        Returns:
            Pydantic model class for API request bodies.

        Example:
            >>> input_model = factory.create_input_model(user_schema)
            >>> instance = input_model(name="Alice", email="alice@example.com")
        """
        fields = self._build_input_fields(schema)
        model_name = f"{schema.name}{ModelName.INPUT_SUFFIX}"

        model = create_model(model_name, **fields)  # pyright: ignore[reportCallIssue,reportUnknownVariableType]
        logger.debug(f"Created input model {model_name} for {schema.name}")
        return cast(type[BaseModel], model)

    def create_list_response_model(
        self, item_model: type[BaseModel]
    ) -> type[BaseModel]:
        """Create paginated list response model.

        Wraps the item model in a list response with pagination metadata.
        The response includes:
        - items: List of item instances
        - pagination: Pagination information (total, has_next, has_prev, etc.)

        Args:
            item_model: Pydantic model for individual items.

        Returns:
            Pydantic model class for paginated list responses.
        """
        model_name = f"{item_model.__name__}{ModelName.LIST_SUFFIX}"

        # Import PaginationInfo here to avoid circular imports
        from ..router import PaginationInfo

        list_fields = {
            ResponseKey.ITEMS: (list[item_model], ...),  # type: ignore[valid-type]
            ResponseKey.PAGINATION: (PaginationInfo, ...),
        }

        model = create_model(model_name, **list_fields)  # pyright: ignore[reportCallIssue,reportUnknownVariableType]
        logger.debug(f"Created list response model {model_name}")
        return cast(type[BaseModel], model)

    # =============================================================================
    # PRIVATE HELPERS
    # =============================================================================

    def _build_input_fields(self, schema: ModelSchema) -> dict[str, tuple[type, Any]]:
        """Build clean field definitions for input model.

        Creates field definitions suitable for pydantic.create_model().
        Excludes the primary key field and handles optional fields properly.

        Args:
            schema: Model schema containing field definitions.

        Returns:
            Dictionary mapping field names to (type, default) tuples.

        Example:
            >>> fields = factory._build_input_fields(user_schema)
            >>> # {'name': (str, ...), 'email': (str, ...), 'age': (int | None, None)}
        """
        fields: dict[str, tuple[type, Any]] = {}

        for field in schema.fields:
            # Skip primary key field for input models
            if field.name == PRIMARY_KEY_FIELD:
                continue

            # Create clean field definition with proper Optional typing
            field_type = field.type | None if field.is_optional else field.type
            default_value = None if field.is_optional else ...
            fields[field.name] = (field_type, default_value)

        return fields
