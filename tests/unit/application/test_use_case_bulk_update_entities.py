"""Tests for BulkUpdateEntities use case."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Any

# Third-party
import pytest

# Project/local
from mock_api.application.dto.requests import BulkUpdateEntitiesRequest
from mock_api.application.use_cases.bulk_update_entities import (
    BulkUpdateEntitiesUseCase,
)
from mock_api.core.exceptions.repository import EntityNotFoundError, ModelNotFoundError
from mock_api.core.exceptions.validation import ValidationError
from mock_api.domain.value_objects.schema import ModelSchema
from mock_api.infrastructure.repositories.memory.memory_repository import (
    MemoryRepository,
)


# =============================================================================
# TESTS - BulkUpdateEntitiesUseCase
# =============================================================================
def test_bulk_update_entities_use_case_updates_entities_successfully(
    memory_repository: MemoryRepository,
    schemas_dict: dict[str, ModelSchema],
    sample_user_data: dict[str, Any],
) -> None:
    """BulkUpdateEntitiesUseCase should update multiple entities successfully."""
    # Arrange - Create entities first
    use_case = BulkUpdateEntitiesUseCase(memory_repository, schemas_dict)
    entity1 = memory_repository.create("User", sample_user_data)
    entity2 = memory_repository.create("User", sample_user_data)

    # Prepare update data
    update_data = [
        {"id": entity1["id"], "name": "Updated Alice", "age": 31},
        {"id": entity2["id"], "email": "updated@example.com"},
    ]
    request = BulkUpdateEntitiesRequest(model_name="User", data_list=update_data)

    # Act
    response = use_case.execute(request)

    # Assert
    assert len(response.items) == 2
    assert response.count == 2
    assert response.items[0]["name"] == "Updated Alice"
    assert response.items[0]["age"] == 31
    assert response.items[1]["email"] == "updated@example.com"


def test_bulk_update_entities_use_case_raises_error_with_invalid_model(
    memory_repository: MemoryRepository,
    schemas_dict: dict[str, ModelSchema],
) -> None:
    """BulkUpdateEntitiesUseCase should raise ModelNotFoundError for invalid model."""
    # Arrange
    use_case = BulkUpdateEntitiesUseCase(memory_repository, schemas_dict)
    request = BulkUpdateEntitiesRequest(
        model_name="InvalidModel",
        data_list=[{"id": 1, "name": "Test"}],
    )

    # Act & Assert
    with pytest.raises(ModelNotFoundError):
        use_case.execute(request)


def test_bulk_update_entities_use_case_raises_error_with_missing_id(
    memory_repository: MemoryRepository,
    schemas_dict: dict[str, ModelSchema],
    sample_user_data: dict[str, Any],
) -> None:
    """BulkUpdateEntitiesUseCase should raise error when 'id' field is missing."""
    # Arrange - Create entity first
    use_case = BulkUpdateEntitiesUseCase(memory_repository, schemas_dict)
    memory_repository.create("User", sample_user_data)

    # Prepare update data without 'id'
    update_data = [{"name": "Updated Alice"}]  # Missing 'id'
    request = BulkUpdateEntitiesRequest(model_name="User", data_list=update_data)

    # Act & Assert
    with pytest.raises(ValidationError):
        use_case.execute(request)


def test_bulk_update_entities_use_case_handles_empty_list(
    memory_repository: MemoryRepository,
    schemas_dict: dict[str, ModelSchema],
) -> None:
    """BulkUpdateEntitiesUseCase should handle empty list gracefully."""
    # Arrange
    use_case = BulkUpdateEntitiesUseCase(memory_repository, schemas_dict)
    request = BulkUpdateEntitiesRequest(model_name="User", data_list=[])

    # Act
    response = use_case.execute(request)

    # Assert
    assert len(response.items) == 0
    assert response.count == 0


def test_bulk_update_entities_use_case_raises_error_with_nonexistent_id(
    memory_repository: MemoryRepository,
    schemas_dict: dict[str, ModelSchema],
) -> None:
    """BulkUpdateEntitiesUseCase should raise EntityNotFoundError for nonexistent ID."""
    # Arrange
    use_case = BulkUpdateEntitiesUseCase(memory_repository, schemas_dict)
    request = BulkUpdateEntitiesRequest(
        model_name="User",
        data_list=[{"id": 999, "name": "Test"}],
    )

    # Act & Assert
    with pytest.raises(EntityNotFoundError):
        use_case.execute(request)
