"""Delete entity use case."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Any

from mock_api.application.dto.requests import DeleteEntityRequest

# Project/local
from mock_api.core.exceptions import ModelNotFoundError
from mock_api.domain.repositories.protocols import IWriteRepository
from mock_api.domain.value_objects.schema import ModelSchema


# =============================================================================
# CORE CLASSES
# =============================================================================
class DeleteEntityUseCase:
    """Use case for deleting entity.

    Single Responsibility: Delete one entity by ID.
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

    def execute(self, request: DeleteEntityRequest) -> bool:
        """Execute delete entity use case.

        Flow:
        1. Validate model exists in schemas
        2. Delegate to repository
        3. Return deletion status

        Args:
            request: Delete request

        Returns:
            True if deleted, False if not found

        Raises:
            ModelNotFoundError: If model doesn't exist
        """
        # Validate model exists
        if request.model_name not in self._schemas:
            raise ModelNotFoundError(
                model_name=request.model_name,
                available_models=list(self._schemas.keys()),
            )

        # Delegate to repository
        return self._repository.delete(request.model_name, request.entity_id)
