"""Create entity use case."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Any

from mock_api.application.dto.requests import CreateEntityRequest
from mock_api.application.dto.responses import EntityResponse

# Project/local
from mock_api.core.exceptions import ModelNotFoundError
from mock_api.core.utils.logger import get_logger
from mock_api.domain.repositories.protocols import IWriteRepository
from mock_api.domain.value_objects.schema import ModelSchema

# =============================================================================
# LOGGER
# =============================================================================
logger = get_logger(__name__)


# =============================================================================
# CORE CLASSES
# =============================================================================
class CreateEntityUseCase:
    """Use case for creating a single entity.

    Single Responsibility: Create one entity with validation.
    Delegates validation and persistence to repository.
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

    def execute(self, request: CreateEntityRequest) -> EntityResponse:
        """Execute create entity use case.

        Flow:
        1. Validate model exists in schemas
        2. Delegate to repository (repository validates data)
        3. Map to response DTO

        Args:
            request: Create request

        Returns:
            Entity response with created entity

        Raises:
            ModelNotFoundError: If model doesn't exist
            ValidationError: If data is invalid
        """
        logger.info(
            "Creating entity",
            extra={
                "model_name": request.model_name,
                "data_keys": list(request.data.keys()),
            },
        )

        # Validate model exists
        if request.model_name not in self._schemas:
            logger.warning(
                "Model not found",
                extra={
                    "model_name": request.model_name,
                    "available_models": list(self._schemas.keys()),
                },
            )
            raise ModelNotFoundError(
                model_name=request.model_name,
                available_models=list(self._schemas.keys()),
            )

        # Delegate to repository
        created_entity = self._repository.create(request.model_name, request.data)

        logger.info(
            "Entity created successfully",
            extra={
                "model_name": request.model_name,
                "entity_id": created_entity.get("id"),
            },
        )

        # Map to response DTO
        return EntityResponse(model_name=request.model_name, data=created_entity)
