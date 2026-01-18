"""Bulk delete entities use case."""

from __future__ import annotations

from typing import Any

from mock_api.application.dto.requests import BulkDeleteEntitiesRequest
from mock_api.application.dto.responses import BulkDeleteEntitiesResponse
from mock_api.core.exceptions import ModelNotFoundError
from mock_api.core.utils.logger import get_logger
from mock_api.domain.repositories.protocols import IBulkRepository
from mock_api.domain.value_objects.schema import ModelSchema

logger = get_logger(__name__)


class BulkDeleteEntitiesUseCase:
    """Use case for bulk deleting multiple entities.

    Single Responsibility: Bulk delete entities efficiently.
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

    def execute(self, request: BulkDeleteEntitiesRequest) -> BulkDeleteEntitiesResponse:
        """Execute bulk delete entities use case.

        Flow:
        1. Validate model exists in schemas
        2. Delegate to bulk repository
        3. Return count of deleted entities

        Args:
            request: Bulk delete request DTO

        Returns:
            BulkDeleteEntitiesResponse with deletion count

        Raises:
            ModelNotFoundError: If model doesn't exist
            EntityNotFoundError: If entity ID not found
            BulkOperationError: If bulk operation fails
        """
        logger.info(
            f"Bulk deleting {len(request.entity_ids)} entities",
            extra={"model_name": request.model_name, "count": len(request.entity_ids)},
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
        deleted_count = self._repository.bulk_delete(
            request.model_name, request.entity_ids, allow_partial=False
        )

        logger.info(
            f"Bulk deleted {deleted_count} entities successfully",
            extra={"model_name": request.model_name, "count": deleted_count},
        )

        # Map to response DTO
        return BulkDeleteEntitiesResponse(
            model_name=request.model_name,
            count=deleted_count,
        )
