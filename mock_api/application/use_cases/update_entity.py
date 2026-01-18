"""Update entity use case."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Any

from mock_api.application.dto.requests import UpdateEntityRequest
from mock_api.application.dto.responses import EntityResponse

# Project/local
from mock_api.core.exceptions import ModelNotFoundError
from mock_api.domain.repositories.protocols import IWriteRepository
from mock_api.domain.value_objects.schema import ModelSchema


# =============================================================================
# CORE CLASSES
# =============================================================================
class UpdateEntityUseCase:
    """Use case for updating entity.

    Single Responsibility: Update one entity with partial data.
    Supports partial updates (only provided fields are updated).
    """

    def __init__(
        self,
        repository: IWriteRepository[dict[str, Any]],
        schemas: dict[str, ModelSchema],
    ) -> None:
        """Initialize use case.

        Args:
            repository: Write repository
            schemas: Model schemas
        """
        self._repository = repository
        self._schemas = schemas

    def execute(self, request: UpdateEntityRequest) -> EntityResponse:
        """Execute update entity use case.

        Flow:
        1. Validate model exists in schemas
        2. Delegate to repository (supports partial updates)
        3. Map to response DTO

        Args:
            request: Update request

        Returns:
            Entity response with updated entity

        Raises:
            ModelNotFoundError: If model doesn't exist
            EntityNotFoundError: If entity doesn't exist
            ValidationError: If data is invalid
        """
        # Validate model exists
        if request.model_name not in self._schemas:
            raise ModelNotFoundError(
                model_name=request.model_name,
                available_models=list(self._schemas.keys()),
            )

        # Delegate to repository
        updated_entity = self._repository.update(
            request.model_name, request.entity_id, request.data
        )

        # Map to response DTO
        return EntityResponse(model_name=request.model_name, data=updated_entity)
