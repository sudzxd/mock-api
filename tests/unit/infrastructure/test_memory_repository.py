"""Tests for MemoryRepository."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Any

# Third-party
import pytest

# Project/local
from mock_api.core.exceptions.repository import EntityNotFoundError, ModelNotFoundError
from mock_api.core.exceptions.validation import ValidationError
from mock_api.domain.value_objects.query import FilterSpec, SortSpec
from mock_api.infrastructure.repositories.memory.memory_repository import (
    MemoryRepository,
)


# =============================================================================
# TESTS - CREATE
# =============================================================================
def test_memory_repository_create_entity_successfully(
    memory_repository: MemoryRepository, sample_user_data: dict[str, Any]
) -> None:
    """MemoryRepository.create() should create entity with auto-generated ID."""
    # Act
    entity = memory_repository.create("User", sample_user_data)

    # Assert
    assert entity["id"] == 1
    assert entity["name"] == "Alice"
    assert entity["email"] == "alice@example.com"


def test_memory_repository_create_raises_error_with_invalid_model(
    memory_repository: MemoryRepository, sample_user_data: dict[str, Any]
) -> None:
    """MemoryRepository.create() should raise ModelNotFoundError for invalid model."""
    # Act & Assert
    with pytest.raises(ModelNotFoundError):
        memory_repository.create("InvalidModel", sample_user_data)


def test_memory_repository_create_raises_error_with_missing_fields(
    memory_repository: MemoryRepository,
) -> None:
    """MemoryRepository.create() should raise ValidationError for missing fields."""
    # Arrange
    invalid_data = {"name": "Alice"}  # Missing email and created_at

    # Act & Assert
    with pytest.raises(ValidationError):
        memory_repository.create("User", invalid_data)


def test_memory_repository_create_auto_increments_ids(
    memory_repository: MemoryRepository, sample_user_data: dict[str, Any]
) -> None:
    """MemoryRepository.create() should auto-increment IDs."""
    # Act
    entity1 = memory_repository.create("User", sample_user_data)
    entity2 = memory_repository.create("User", sample_user_data)

    # Assert
    assert entity1["id"] == 1
    assert entity2["id"] == 2


# =============================================================================
# TESTS - GET
# =============================================================================
def test_memory_repository_get_returns_entity_when_exists(
    memory_repository: MemoryRepository, sample_user_data: dict[str, Any]
) -> None:
    """MemoryRepository.get() should return entity when it exists."""
    # Arrange
    created = memory_repository.create("User", sample_user_data)

    # Act
    entity = memory_repository.get("User", created["id"])

    # Assert
    assert entity is not None
    assert entity["id"] == created["id"]
    assert entity["name"] == "Alice"


def test_memory_repository_get_raises_error_when_not_exists(
    memory_repository: MemoryRepository,
) -> None:
    """MemoryRepository.get() should raise EntityNotFoundError when not exists."""
    # Act & Assert
    with pytest.raises(EntityNotFoundError):
        memory_repository.get("User", 999)


def test_memory_repository_get_raises_error_with_invalid_model(
    memory_repository: MemoryRepository,
) -> None:
    """MemoryRepository.get() should raise ModelNotFoundError for invalid model."""
    # Act & Assert
    with pytest.raises(ModelNotFoundError):
        memory_repository.get("InvalidModel", 1)


# =============================================================================
# TESTS - UPDATE
# =============================================================================
def test_memory_repository_update_entity_successfully(
    memory_repository: MemoryRepository, sample_user_data: dict[str, Any]
) -> None:
    """MemoryRepository.update() should update entity with new values."""
    # Arrange
    created = memory_repository.create("User", sample_user_data)
    update_data = {"age": 31}

    # Act
    updated = memory_repository.update("User", created["id"], update_data)

    # Assert
    assert updated["id"] == created["id"]
    assert updated["age"] == 31
    assert updated["name"] == "Alice"  # Unchanged


def test_memory_repository_update_raises_error_when_not_exists(
    memory_repository: MemoryRepository,
) -> None:
    """MemoryRepository.update() should raise EntityNotFoundError when not exists."""
    # Act & Assert
    with pytest.raises(EntityNotFoundError):
        memory_repository.update("User", 999, {"age": 31})


def test_memory_repository_update_raises_error_with_invalid_model(
    memory_repository: MemoryRepository,
) -> None:
    """MemoryRepository.update() should raise ModelNotFoundError for invalid model."""
    # Act & Assert
    with pytest.raises(ModelNotFoundError):
        memory_repository.update("InvalidModel", 1, {"age": 31})


# =============================================================================
# TESTS - DELETE
# =============================================================================
def test_memory_repository_delete_entity_successfully(
    memory_repository: MemoryRepository, sample_user_data: dict[str, Any]
) -> None:
    """MemoryRepository.delete() should remove entity."""
    # Arrange
    created = memory_repository.create("User", sample_user_data)

    # Act
    memory_repository.delete("User", created["id"])

    # Assert
    with pytest.raises(EntityNotFoundError):
        memory_repository.get("User", created["id"])


def test_memory_repository_delete_raises_error_when_not_exists(
    memory_repository: MemoryRepository,
) -> None:
    """MemoryRepository.delete() should raise EntityNotFoundError when not exists."""
    # Act & Assert
    with pytest.raises(EntityNotFoundError):
        memory_repository.delete("User", 999)


# =============================================================================
# TESTS - LIST
# =============================================================================
def test_memory_repository_list_returns_all_entities(
    memory_repository: MemoryRepository, sample_user_data: dict[str, Any]
) -> None:
    """MemoryRepository.list() should return all entities."""
    # Arrange
    memory_repository.create("User", sample_user_data)
    memory_repository.create("User", {**sample_user_data, "name": "Bob"})

    # Act
    result = memory_repository.list("User")

    # Assert
    assert result.total == 2
    assert len(result.items) == 2


def test_memory_repository_list_with_pagination(
    memory_repository: MemoryRepository, sample_user_data: dict[str, Any]
) -> None:
    """MemoryRepository.list() should handle pagination."""
    # Arrange
    for i in range(5):
        memory_repository.create("User", {**sample_user_data, "name": f"User{i}"})

    # Act
    result = memory_repository.list("User", page=2, page_size=2)

    # Assert
    assert result.page == 2
    assert result.page_size == 2
    assert len(result.items) == 2
    assert result.total == 5
    assert result.total_pages == 3


def test_memory_repository_list_with_filters(
    memory_repository: MemoryRepository, sample_user_data: dict[str, Any]
) -> None:
    """MemoryRepository.list() should filter results."""
    # Arrange
    memory_repository.create("User", {**sample_user_data, "age": 25})
    memory_repository.create("User", {**sample_user_data, "age": 30})
    memory_repository.create("User", {**sample_user_data, "age": 35})

    filters = [FilterSpec(field="age", operator="gte", value=30)]

    # Act
    result = memory_repository.list("User", filters=filters)

    # Assert
    assert result.total == 2
    assert all(item["age"] >= 30 for item in result.items)


def test_memory_repository_list_with_sorting(
    memory_repository: MemoryRepository, sample_user_data: dict[str, Any]
) -> None:
    """MemoryRepository.list() should sort results."""
    # Arrange
    memory_repository.create("User", {**sample_user_data, "name": "Charlie"})
    memory_repository.create("User", {**sample_user_data, "name": "Alice"})
    memory_repository.create("User", {**sample_user_data, "name": "Bob"})

    sorts = [SortSpec(field="name", direction="asc")]

    # Act
    result = memory_repository.list("User", sorts=sorts)

    # Assert
    assert result.items[0]["name"] == "Alice"
    assert result.items[1]["name"] == "Bob"
    assert result.items[2]["name"] == "Charlie"


# =============================================================================
# TESTS - EXISTS
# =============================================================================
def test_memory_repository_exists_returns_true_when_entity_exists(
    memory_repository: MemoryRepository, sample_user_data: dict[str, Any]
) -> None:
    """MemoryRepository.exists() should return True when entity exists."""
    # Arrange
    created = memory_repository.create("User", sample_user_data)

    # Act
    exists = memory_repository.exists("User", created["id"])

    # Assert
    assert exists is True


def test_memory_repository_exists_returns_false_when_entity_not_exists(
    memory_repository: MemoryRepository,
) -> None:
    """MemoryRepository.exists() should return False when entity doesn't exist."""
    # Act
    exists = memory_repository.exists("User", 999)

    # Assert
    assert exists is False


# =============================================================================
# TESTS - COUNT
# =============================================================================
def test_memory_repository_count_returns_total(
    memory_repository: MemoryRepository, sample_user_data: dict[str, Any]
) -> None:
    """MemoryRepository.count() should return total count."""
    # Arrange
    memory_repository.create("User", sample_user_data)
    memory_repository.create("User", sample_user_data)
    memory_repository.create("User", sample_user_data)

    # Act
    count = memory_repository.count("User")

    # Assert
    assert count == 3


def test_memory_repository_count_with_filters(
    memory_repository: MemoryRepository, sample_user_data: dict[str, Any]
) -> None:
    """MemoryRepository.count() should count filtered results."""
    # Arrange
    memory_repository.create("User", {**sample_user_data, "age": 25})
    memory_repository.create("User", {**sample_user_data, "age": 30})
    memory_repository.create("User", {**sample_user_data, "age": 35})

    filters = [FilterSpec(field="age", operator="gt", value=28)]

    # Act
    count = memory_repository.count("User", filters=filters)

    # Assert
    assert count == 2
