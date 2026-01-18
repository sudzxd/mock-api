"""Tests for BulkDeleteEntities use case."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Any

# Third-party
import pytest

# Project/local
from mock_api.application.dto.requests import BulkDeleteEntitiesRequest
from mock_api.application.use_cases.bulk_delete_entities import (
    BulkDeleteEntitiesUseCase,
)
from mock_api.core.exceptions.repository import EntityNotFoundError, ModelNotFoundError
from mock_api.domain.value_objects.schema import ModelSchema
from mock_api.infrastructure.repositories.memory.memory_repository import (
    MemoryRepository,
)


# =============================================================================
# TESTS - BulkDeleteEntitiesUseCase
# =============================================================================
def test_bulk_delete_entities_use_case_deletes_entities_successfully(
    memory_repository: MemoryRepository,
    schemas_dict: dict[str, ModelSchema],
    sample_user_data: dict[str, Any],
) -> None:
    """BulkDeleteEntitiesUseCase should delete multiple entities successfully."""
    # Arrange - Create entities first
    use_case = BulkDeleteEntitiesUseCase(memory_repository, schemas_dict)
    entity1 = memory_repository.create("User", sample_user_data)
    entity2 = memory_repository.create("User", sample_user_data)
    entity3 = memory_repository.create("User", sample_user_data)

    # Prepare delete request
    entity_ids = [entity1["id"], entity2["id"]]
    request = BulkDeleteEntitiesRequest(model_name="User", entity_ids=entity_ids)

    # Act
    response = use_case.execute(request)

    # Assert
    assert response.count == 2
    assert response.model_name == "User"

    # Verify entities are deleted
    with pytest.raises(EntityNotFoundError):
        memory_repository.get("User", entity1["id"])
    with pytest.raises(EntityNotFoundError):
        memory_repository.get("User", entity2["id"])

    # Verify entity3 still exists
    existing_entity = memory_repository.get("User", entity3["id"])
    assert existing_entity["id"] == entity3["id"]


def test_bulk_delete_entities_use_case_raises_error_with_invalid_model(
    memory_repository: MemoryRepository,
    schemas_dict: dict[str, ModelSchema],
) -> None:
    """BulkDeleteEntitiesUseCase should raise ModelNotFoundError for invalid model."""
    # Arrange
    use_case = BulkDeleteEntitiesUseCase(memory_repository, schemas_dict)
    request = BulkDeleteEntitiesRequest(
        model_name="InvalidModel",
        entity_ids=[1, 2],
    )

    # Act & Assert
    with pytest.raises(ModelNotFoundError):
        use_case.execute(request)


def test_bulk_delete_entities_use_case_handles_empty_list(
    memory_repository: MemoryRepository,
    schemas_dict: dict[str, ModelSchema],
) -> None:
    """BulkDeleteEntitiesUseCase should handle empty list gracefully."""
    # Arrange
    use_case = BulkDeleteEntitiesUseCase(memory_repository, schemas_dict)
    request = BulkDeleteEntitiesRequest(model_name="User", entity_ids=[])

    # Act
    response = use_case.execute(request)

    # Assert
    assert response.count == 0
    assert response.model_name == "User"


def test_bulk_delete_entities_use_case_handles_nonexistent_ids(
    memory_repository: MemoryRepository,
    schemas_dict: dict[str, ModelSchema],
) -> None:
    """BulkDeleteEntitiesUseCase raises EntityNotFoundError for nonexistent IDs."""
    # Arrange
    use_case = BulkDeleteEntitiesUseCase(memory_repository, schemas_dict)
    request = BulkDeleteEntitiesRequest(
        model_name="User",
        entity_ids=[999, 1000],
    )

    # Act & Assert
    with pytest.raises(EntityNotFoundError):
        use_case.execute(request)


def test_bulk_delete_entities_use_case_handles_partial_nonexistent_ids(
    memory_repository: MemoryRepository,
    schemas_dict: dict[str, ModelSchema],
    sample_user_data: dict[str, Any],
) -> None:
    """BulkDeleteEntitiesUseCase fails if any ID doesn't exist (allow_partial=False)."""
    # Arrange - Create one entity
    use_case = BulkDeleteEntitiesUseCase(memory_repository, schemas_dict)
    entity1 = memory_repository.create("User", sample_user_data)

    # Try to delete one existing and one nonexistent
    request = BulkDeleteEntitiesRequest(
        model_name="User",
        entity_ids=[entity1["id"], 999],
    )

    # Act & Assert - Should fail because 999 doesn't exist
    with pytest.raises(EntityNotFoundError):
        use_case.execute(request)
