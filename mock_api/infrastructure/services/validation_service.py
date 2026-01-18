"""Validation service implementation."""

from __future__ import annotations

from typing import Any, cast

from pydantic import (
    BaseModel,
    create_model,
)
from pydantic import (
    ValidationError as PydanticValidationError,
)

from ...core.exceptions.validation import ValidationError
from ...domain.services.protocols import IValidationService
from ...domain.value_objects.schema import FieldSchema, ModelSchema


class ValidationService(IValidationService):
    """Validate entity data against schema using Pydantic.

    Builds dynamic Pydantic models from ModelSchema and validates data.
    Caches Pydantic models for performance.
    """

    def __init__(self) -> None:
        """Initialize validation service."""
        self._pydantic_model_cache: dict[str, type[BaseModel]] = {}

    def validate(
        self,
        model_name: str,
        data: dict[str, Any],
        schema: ModelSchema,
        *,
        partial: bool = False,
    ) -> dict[str, Any]:
        """Validate entity data.

        Uses Pydantic for validation.

        Args:
            model_name: Model name
            data: Data to validate
            schema: Model schema
            partial: Allow missing required fields

        Returns:
            Validated and normalized data

        Raises:
            ValidationError: If validation fails
        """
        pydantic_model = self._build_pydantic_model(schema)

        try:
            if partial:
                # For partial updates, only validate provided fields
                validated = pydantic_model.model_validate(data, strict=False)
                # Only return fields that were in the input
                result = {k: v for k, v in validated.model_dump().items() if k in data}
            else:
                # Full validation
                validated = pydantic_model.model_validate(data)
                result = validated.model_dump()

        except PydanticValidationError as e:
            # Convert Pydantic errors to dict format
            error_dicts = [dict(err) for err in e.errors()]
            raise ValidationError(
                message=f"Validation failed for {model_name}",
                model_name=model_name,
                errors=error_dicts,
            ) from e
        else:
            return result

    def validate_field(
        self,
        field_name: str,
        field_value: Any,
        field_schema: FieldSchema,
    ) -> Any:
        """Validate single field value.

        Args:
            field_name: Field name
            field_value: Value to validate
            field_schema: Field schema

        Returns:
            Validated value

        Raises:
            ValidationError: If validation fails
        """
        # Determine field type with optionality
        field_type = (
            field_schema.type | None if field_schema.is_optional else field_schema.type
        )

        # Create single-field Pydantic model for validation
        field_definition = (
            field_type,
            None if field_schema.is_optional else ...,
        )
        single_field_model = cast(
            type[BaseModel],
            create_model(
                "SingleFieldModel",
                **{field_name: field_definition},  # pyright: ignore[reportCallIssue,reportArgumentType]
            ),
        )

        try:
            validated = single_field_model.model_validate({field_name: field_value})
            return getattr(validated, field_name)
        except PydanticValidationError as e:
            error_dicts = [dict(err) for err in e.errors()]
            raise ValidationError(
                message=f"Validation failed for field {field_name}",
                model_name=field_name,
                errors=error_dicts,
            ) from e

    def _build_pydantic_model(self, schema: ModelSchema) -> type[BaseModel]:
        """Build or retrieve Pydantic BaseModel class for validation.

        Optimization: For Pydantic schemas, use the original model_class directly.
        Only build dynamic models for OpenAPI/GraphQL schemas.

        Args:
            schema: Model schema

        Returns:
            Pydantic BaseModel class
        """
        # Check cache
        if schema.name in self._pydantic_model_cache:
            return self._pydantic_model_cache[schema.name]

        # Optimization: Use original Pydantic model if available
        if schema.model_class is not None:
            # For Pydantic schemas - use original model directly
            pydantic_model = cast(type[BaseModel], schema.model_class)
            self._pydantic_model_cache[schema.name] = pydantic_model
            return pydantic_model

        # For OpenAPI/GraphQL schemas - build dynamic model
        field_defs: dict[str, Any] = {}
        for field in schema.fields:
            # Determine field type with optionality
            field_type = field.type | None if field.is_optional else field.type

            # Add default if specified
            if field.default is not None:
                field_defs[field.name] = (field_type, field.default)
            elif field.is_optional:
                field_defs[field.name] = (field_type, None)
            else:
                field_defs[field.name] = (field_type, ...)

        # Create Pydantic model dynamically
        pydantic_model = create_model(schema.name, **field_defs)  # pyright: ignore[reportCallIssue,reportArgumentType]

        # Cache it
        self._pydantic_model_cache[schema.name] = pydantic_model

        return pydantic_model
