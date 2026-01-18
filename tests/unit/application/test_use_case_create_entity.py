"""Tests for CreateEntity use case."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Any

# Third-party
import pytest

# Project/local
from mock_api.application.dto.requests import CreateEntityRequest
from mock_api.application.use_cases.create_entity import CreateEntityUseCase
from mock_api.core.exceptions.repository import ModelNotFoundError
from mock_api.core.exceptions.validation import ValidationError
from mock_api.domain.value_objects.schema import ModelSchema
from mock_api.infrastructure.repositories.memory.memory_repository import (
    MemoryRepository,
)


# =============================================================================
# TESTS - CreateEntityUseCase
# =============================================================================
def test_create_entity_use_case_creates_entity_successfully(
    memory_repository: MemoryRepository,
    schemas_dict: dict[str, ModelSchema],
    sample_user_data: dict[str, Any],
) -> None:
    """CreateEntityUseCase should create entity with valid data."""
    # Arrange
    use_case = CreateEntityUseCase(memory_repository, schemas_dict)
    request = CreateEntityRequest(model_name="User", data=sample_user_data)

    # Act
    response = use_case.execute(request)

    # Assert
    assert response.data is not None
    assert response.data["id"] == 1
    assert response.data["name"] == "Alice"
    assert response.data["email"] == "alice@example.com"


def test_create_entity_use_case_raises_error_with_invalid_model(
    memory_repository: MemoryRepository,
    schemas_dict: dict[str, ModelSchema],
    sample_user_data: dict[str, Any],
) -> None:
    """CreateEntityUseCase should raise ModelNotFoundError for invalid model."""
    # Arrange
    use_case = CreateEntityUseCase(memory_repository, schemas_dict)
    request = CreateEntityRequest(model_name="InvalidModel", data=sample_user_data)

    # Act & Assert
    with pytest.raises(ModelNotFoundError):
        use_case.execute(request)


def test_create_entity_use_case_raises_error_with_invalid_data(
    memory_repository: MemoryRepository, schemas_dict: dict[str, ModelSchema]
) -> None:
    """CreateEntityUseCase should raise ValidationError for invalid data."""
    # Arrange
    use_case = CreateEntityUseCase(memory_repository, schemas_dict)
    invalid_data = {"name": "Alice"}  # Missing required fields
    request = CreateEntityRequest(model_name="User", data=invalid_data)

    # Act & Assert
    with pytest.raises(ValidationError):
        use_case.execute(request)


def test_create_entity_use_case_assigns_auto_increment_id(
    memory_repository: MemoryRepository,
    schemas_dict: dict[str, ModelSchema],
    sample_user_data: dict[str, Any],
) -> None:
    """CreateEntityUseCase should assign auto-increment IDs."""
    # Arrange
    use_case = CreateEntityUseCase(memory_repository, schemas_dict)
    request1 = CreateEntityRequest(model_name="User", data=sample_user_data)
    request2 = CreateEntityRequest(model_name="User", data=sample_user_data)

    # Act
    response1 = use_case.execute(request1)
    response2 = use_case.execute(request2)

    # Assert
    assert response1.data["id"] == 1
    assert response2.data["id"] == 2
