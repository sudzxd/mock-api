"""List entities use case."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Any

from mock_api.application.dto.requests import ListEntitiesRequest
from mock_api.application.dto.responses import ListEntitiesResponse

# Project/local
from mock_api.core.exceptions import ModelNotFoundError
from mock_api.core.utils.logger import get_logger
from mock_api.domain.repositories.protocols import IReadRepository
from mock_api.domain.services.protocols import IFilterService, ISortService
from mock_api.domain.value_objects.schema import ModelSchema

# =============================================================================
# LOGGER
# =============================================================================
logger = get_logger(__name__)


# =============================================================================
# CORE CLASSES
# =============================================================================
class ListEntitiesUseCase:
    """Use case for listing entities with filtering, sorting, pagination.

    Single Responsibility: List entities with query capabilities.
    Orchestrates filter parsing, sort parsing, and querying.
    """

    def __init__(
        self,
        repository: IReadRepository[dict[str, Any]],
        filter_service: IFilterService,
        sort_service: ISortService,
        schemas: dict[str, ModelSchema],
    ) -> None:
        """Initialize use case.

        Args:
            repository: Read repository
            filter_service: Filter parsing service
            sort_service: Sort parsing service
            schemas: Model schemas
        """
        self._repository = repository
        self._filter_service = filter_service
        self._sort_service = sort_service
        self._schemas = schemas

    def execute(self, request: ListEntitiesRequest) -> ListEntitiesResponse:
        """Execute list entities use case.

        Flow:
        1. Validate model exists in schemas
        2. Parse filters from query params
        3. Parse sorts from query params
        4. Query repository
        5. Map to response DTO

        Args:
            request: List request

        Returns:
            List response with paginated results

        Raises:
            ModelNotFoundError: If model doesn't exist
            ValidationError: If filters/sorts invalid
        """
        logger.info(
            "Listing entities",
            extra={
                "model_name": request.model_name,
                "page": request.page,
                "page_size": request.page_size,
            },
        )

        # Validate model exists
        if request.model_name not in self._schemas:
            logger.warning(
                "Model not found",
                extra={"model_name": request.model_name},
            )
            raise ModelNotFoundError(
                model_name=request.model_name,
                available_models=list(self._schemas.keys()),
            )

        # Get schema
        schema = self._schemas[request.model_name]

        # Parse filters from query params
        filters = []
        if request.query_params:
            filters = self._filter_service.parse(request.query_params, schema)

        # Parse sorts from query params
        sorts = []
        if request.query_params and "sort" in request.query_params:
            sort_param = request.query_params["sort"]
            sorts = self._sort_service.parse(sort_param, schema)

        # Query repository
        result = self._repository.list(
            request.model_name,
            page=request.page,
            page_size=request.page_size,
            filters=filters if filters else None,
            sorts=sorts if sorts else None,
        )

        logger.info(
            "Entities listed successfully",
            extra={
                "model_name": request.model_name,
                "count": len(result.items),
                "total": result.total,
            },
        )

        # Map to response DTO
        return ListEntitiesResponse(
            model_name=request.model_name,
            items=list(result.items),
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
        )
