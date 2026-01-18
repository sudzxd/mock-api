"""Get entity use case."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Any

from mock_api.application.dto.requests import GetEntityRequest
from mock_api.application.dto.responses import EntityResponse

# Project/local
from mock_api.core.exceptions import ModelNotFoundError
from mock_api.domain.repositories.protocols import IReadRepository
from mock_api.domain.value_objects.schema import ModelSchema


# =============================================================================
# CORE CLASSES
# =============================================================================
class GetEntityUseCase:
    """Use case for getting single entity by ID.

    Single Responsibility: Retrieve one entity by ID.
    """

    def __init__(
        self,
        repository: IReadRepository[dict[str, Any]],
        schemas: dict[str, ModelSchema],
    ) -> None:
        """Initialize use case.

        Args:
            repository: Read repository
            schemas: Model schemas
        """
        self._repository = repository
        self._schemas = schemas

    def execute(self, request: GetEntityRequest) -> EntityResponse:
        """Execute get entity use case.

        Flow:
        1. Validate model exists in schemas
        2. Delegate to repository
        3. Raise if not found
        4. Map to response DTO

        Args:
            request: Get request

        Returns:
            Entity response with entity data

        Raises:
            ModelNotFoundError: If model doesn't exist
            EntityNotFoundError: If entity doesn't exist
        """
        # Validate model exists
        if request.model_name not in self._schemas:
            raise ModelNotFoundError(
                model_name=request.model_name,
                available_models=list(self._schemas.keys()),
            )

        # Delegate to repository (raises EntityNotFoundError if not found)
        entity = self._repository.get(request.model_name, request.entity_id)

        # Map to response DTO
        return EntityResponse(model_name=request.model_name, data=entity)
