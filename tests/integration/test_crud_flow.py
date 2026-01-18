"""Integration tests for full CRUD flow."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Any

# Third-party
import pytest

# Project/local
from mock_api.application.dto.requests import (
    CreateEntityRequest,
    DeleteEntityRequest,
    GetEntityRequest,
    ListEntitiesRequest,
    UpdateEntityRequest,
)
from mock_api.application.use_cases.create_entity import CreateEntityUseCase
from mock_api.application.use_cases.delete_entity import DeleteEntityUseCase
from mock_api.application.use_cases.get_entity import GetEntityUseCase
from mock_api.application.use_cases.list_entities import ListEntitiesUseCase
from mock_api.application.use_cases.update_entity import UpdateEntityUseCase
from mock_api.core.exceptions.repository import EntityNotFoundError
from mock_api.domain.value_objects.schema import ModelSchema
from mock_api.infrastructure.repositories.memory.memory_repository import (
    MemoryRepository,
)
from mock_api.infrastructure.services.filter_service import FilterService
from mock_api.infrastructure.services.sort_service import SortService


# =============================================================================
# TESTS - Full CRUD Flow
# =============================================================================
def test_integration_full_crud_flow(
    memory_repository: MemoryRepository,
    schemas_dict: dict[str, ModelSchema],
    sample_user_data: dict[str, Any],
) -> None:
    """Integration test for complete CRUD flow."""
    # Arrange
    create_use_case = CreateEntityUseCase(memory_repository, schemas_dict)
    get_use_case = GetEntityUseCase(memory_repository, schemas_dict)
    update_use_case = UpdateEntityUseCase(memory_repository, schemas_dict)
    delete_use_case = DeleteEntityUseCase(memory_repository, schemas_dict)

    # Act 1: Create entity
    create_request = CreateEntityRequest(model_name="User", data=sample_user_data)
    create_response = create_use_case.execute(create_request)
    entity_id = create_response.data["id"]

    # Assert 1: Entity created
    assert entity_id == 1
    assert create_response.data["name"] == "Alice"

    # Act 2: Get entity
    get_request = GetEntityRequest(model_name="User", entity_id=entity_id)
    get_response = get_use_case.execute(get_request)

    # Assert 2: Entity retrieved
    assert get_response.data["id"] == entity_id
    assert get_response.data["name"] == "Alice"

    # Act 3: Update entity
    update_request = UpdateEntityRequest(
        model_name="User", entity_id=entity_id, data={"age": 31}
    )
    update_response = update_use_case.execute(update_request)

    # Assert 3: Entity updated
    assert update_response.data["age"] == 31
    assert update_response.data["name"] == "Alice"  # Unchanged

    # Act 4: Delete entity
    delete_request = DeleteEntityRequest(model_name="User", entity_id=entity_id)
    delete_use_case.execute(delete_request)

    # Assert 4: Entity deleted
    with pytest.raises(EntityNotFoundError):
        get_use_case.execute(get_request)


def test_integration_list_with_filtering_sorting_pagination(
    memory_repository: MemoryRepository,
    schemas_dict: dict[str, ModelSchema],
    sample_user_data: dict[str, Any],
    user_schema: ModelSchema,
) -> None:
    """Integration test for list with filtering, sorting, and pagination."""
    # Arrange
    create_use_case = CreateEntityUseCase(memory_repository, schemas_dict)
    list_use_case = ListEntitiesUseCase(
        memory_repository,
        FilterService(),
        SortService(),
        schemas_dict,
    )

    # Create multiple entities
    for name, age in [("Alice", 30), ("Bob", 25), ("Charlie", 35), ("Diana", 28)]:
        data = {**sample_user_data, "name": name, "age": age}
        create_request = CreateEntityRequest(model_name="User", data=data)
        create_use_case.execute(create_request)

    # Act 1: List with filter (age >= 30)
    list_request = ListEntitiesRequest(
        model_name="User",
        page=1,
        page_size=20,
        query_params={"age__gte": "30"},
    )
    list_response = list_use_case.execute(list_request)

    # Assert 1: Filtered results
    assert list_response.total == 2
    assert all(item["age"] >= 30 for item in list_response.items)

    # Act 2: List with sorting (by name ascending)
    list_request = ListEntitiesRequest(
        model_name="User",
        page=1,
        page_size=20,
        query_params={"sort": "name"},
    )
    list_response = list_use_case.execute(list_request)

    # Assert 2: Sorted results
    assert list_response.items[0]["name"] == "Alice"
    assert list_response.items[1]["name"] == "Bob"
    assert list_response.items[2]["name"] == "Charlie"
    assert list_response.items[3]["name"] == "Diana"

    # Act 3: List with pagination (page 2, size 2)
    list_request = ListEntitiesRequest(
        model_name="User",
        page=2,
        page_size=2,
        query_params={"sort": "name"},
    )
    list_response = list_use_case.execute(list_request)

    # Assert 3: Paginated results
    assert list_response.page == 2
    assert list_response.page_size == 2
    assert len(list_response.items) == 2
    assert list_response.total == 4
    assert list_response.items[0]["name"] == "Charlie"


def test_integration_query_parsing_flow(
    memory_repository: MemoryRepository,
    schemas_dict: dict[str, ModelSchema],
    user_schema: ModelSchema,
) -> None:
    """Integration test for query parameter parsing flow."""
    # Arrange
    filter_service = FilterService()
    sort_service = SortService()

    # Act 1: Parse filters
    query_params = {"age__gte": "30", "name": "Alice"}
    filters = filter_service.parse(query_params, user_schema)

    # Assert 1: Filters parsed
    assert len(filters) == 2
    assert filters[0].field == "age"
    assert filters[0].operator == "gte"
    assert filters[0].value == 30  # Type converted

    # Act 2: Parse sorts
    sort_param = "name,-age"
    sorts = sort_service.parse(sort_param, user_schema)

    # Assert 2: Sorts parsed
    assert len(sorts) == 2
    assert sorts[0].field == "name"
    assert sorts[0].direction == "asc"
    assert sorts[1].field == "age"
    assert sorts[1].direction == "desc"
