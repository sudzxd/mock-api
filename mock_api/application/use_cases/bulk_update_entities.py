"""Bulk update entities use case."""

from __future__ import annotations

from typing import Any

from mock_api.application.dto.requests import BulkUpdateEntitiesRequest
from mock_api.application.dto.responses import BulkUpdateEntitiesResponse
from mock_api.core.exceptions import ModelNotFoundError, ValidationError
from mock_api.core.utils.logger import get_logger
from mock_api.domain.repositories.protocols import IBulkRepository
from mock_api.domain.value_objects.schema import ModelSchema

logger = get_logger(__name__)


class BulkUpdateEntitiesUseCase:
    """Use case for bulk updating multiple entities.

    Single Responsibility: Bulk update entities efficiently.
    Uses bulk repository operations for better performance.
    Each item in data_list must contain 'id' field.
    """

    def __init__(
        self,
        repository: IBulkRepository[dict[str, Any]],
        schemas: dict[str, ModelSchema],
    ) -> None:
        """Initialize use case.

        Args:
            repository: Bulk repository
            schemas: Model schemas
        """
        self._repository = repository
        self._schemas = schemas

    def execute(self, request: BulkUpdateEntitiesRequest) -> BulkUpdateEntitiesResponse:
        """Execute bulk update entities use case.

        Flow:
        1. Validate model exists in schemas
        2. Delegate to bulk repository
        3. Return updated entities

        Args:
            request: Bulk update request DTO

        Returns:
            BulkEntitiesResponse with updated entities

        Raises:
            ModelNotFoundError: If model doesn't exist
            ValidationError: If data is invalid
            EntityNotFoundError: If entity ID not found
            BulkOperationError: If bulk operation fails
        """
        logger.info(
            f"Bulk updating {len(request.data_list)} entities",
            extra={"model_name": request.model_name, "count": len(request.data_list)},
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

        # Validate that all items have 'id' field
        for i, item in enumerate(request.data_list):
            if "id" not in item:
                raise ValidationError(
                    f"Missing required field 'id' in item at index {i}",
                    model_name=request.model_name,
                    field_name="id",
                )

        # Delegate to bulk repository
        updated_entities = self._repository.bulk_update(
            request.model_name, request.data_list, allow_partial=False
        )

        logger.info(
            f"Bulk updated {len(updated_entities)} entities successfully",
            extra={"model_name": request.model_name, "count": len(updated_entities)},
        )

        # Map to response DTO
        return BulkUpdateEntitiesResponse(
            model_name=request.model_name,
            items=updated_entities,
            count=len(updated_entities),
        )
