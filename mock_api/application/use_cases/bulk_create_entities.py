"""Bulk create entities use case."""

from __future__ import annotations

from typing import Any

from mock_api.application.dto.requests import BulkCreateEntitiesRequest
from mock_api.application.dto.responses import BulkCreateEntitiesResponse
from mock_api.core.exceptions import ModelNotFoundError
from mock_api.core.utils.logger import get_logger
from mock_api.domain.repositories.protocols import IBulkRepository
from mock_api.domain.value_objects.schema import ModelSchema

logger = get_logger(__name__)


class BulkCreateEntitiesUseCase:
    """Use case for bulk creating multiple entities.

    Single Responsibility: Bulk create entities efficiently.
    Uses bulk repository operations for better performance.
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

    def execute(self, request: BulkCreateEntitiesRequest) -> BulkCreateEntitiesResponse:
        """Execute bulk create entities use case.

        Flow:
        1. Validate model exists in schemas
        2. Delegate to bulk repository
        3. Return created entities

        Args:
            request: Bulk create request DTO

        Returns:
            BulkEntitiesResponse with created entities

        Raises:
            ModelNotFoundError: If model doesn't exist
            ValidationError: If data is invalid
            BulkOperationError: If bulk operation fails
        """
        logger.info(
            f"Bulk creating {len(request.data_list)} entities",
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

        # Delegate to bulk repository
        created_entities = self._repository.bulk_create(
            request.model_name, request.data_list, allow_partial=False
        )

        logger.info(
            f"Bulk created {len(created_entities)} entities successfully",
            extra={"model_name": request.model_name, "count": len(created_entities)},
        )

        # Map to response DTO
        return BulkCreateEntitiesResponse(
            model_name=request.model_name,
            items=created_entities,
            count=len(created_entities),
        )
