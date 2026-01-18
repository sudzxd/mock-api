"""E2E tests for API endpoints."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from pathlib import Path

# Third-party
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Project/local
from mock_api.infrastructure.parsers.pydantic_parser import PydanticSchemaParser
from mock_api.presentation.api.v1.router import create_router
from mock_api.presentation.dependencies import injection
from mock_api.presentation.middleware import setup_exception_handlers


# =============================================================================
# FIXTURES
# =============================================================================
@pytest.fixture
def test_app() -> FastAPI:
    """Create FastAPI test application."""
    # Reset dependencies for clean test state
    injection.reset_dependencies()

    # Parse schemas
    parser = PydanticSchemaParser()
    test_models_path = str(Path(__file__).parent.parent / "fixtures" / "test_models.py")
    schemas = parser.parse_file(test_models_path)

    # Initialize dependencies
    injection.initialize_dependencies(schemas, "memory://")

    # Create app
    app = FastAPI()

    # Setup exception handlers
    setup_exception_handlers(app)

    # Create and include router
    router = create_router(schemas, prefix="/api/v1")
    app.include_router(router)

    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(test_app)


# =============================================================================
# TESTS - CREATE
# =============================================================================
def test_e2e_create_user_returns_201(client: TestClient) -> None:
    """POST /api/v1/User should create user and return 201."""
    # Arrange
    user_data = {
        "name": "Alice",
        "email": "alice@example.com",
        "age": 30,
        "created_at": "2026-01-17T00:00:00",
    }

    # Act
    response = client.post("/api/v1/User", json=user_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Alice"
    assert data["email"] == "alice@example.com"


def test_e2e_create_user_without_optional_fields(client: TestClient) -> None:
    """POST /api/v1/User should create user without optional age."""
    # Arrange
    user_data = {
        "name": "Bob",
        "email": "bob@example.com",
        "created_at": "2026-01-17T00:00:00",
    }

    # Act
    response = client.post("/api/v1/User", json=user_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["age"] is None


# =============================================================================
# TESTS - GET
# =============================================================================
def test_e2e_get_user_returns_entity(client: TestClient) -> None:
    """GET /api/v1/User/{id} should return user."""
    # Arrange - Create user first
    user_data = {
        "name": "Alice",
        "email": "alice@example.com",
        "created_at": "2026-01-17T00:00:00",
    }
    create_response = client.post("/api/v1/User", json=user_data)
    user_id = create_response.json()["id"]

    # Act
    response = client.get(f"/api/v1/User/{user_id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["name"] == "Alice"


def test_e2e_get_nonexistent_user_returns_404(client: TestClient) -> None:
    """GET /api/v1/User/999 should return 404."""
    # Act
    response = client.get("/api/v1/User/999")

    # Assert
    assert response.status_code == 404


# =============================================================================
# TESTS - LIST
# =============================================================================
def test_e2e_list_users_returns_all_users(client: TestClient) -> None:
    """GET /api/v1/User should list all users."""
    # Arrange - Create multiple users
    for name in ["Alice", "Bob", "Charlie"]:
        user_data = {
            "name": name,
            "email": f"{name.lower()}@example.com",
            "created_at": "2026-01-17T00:00:00",
        }
        client.post("/api/v1/User", json=user_data)

    # Act
    response = client.get("/api/v1/User")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


def test_e2e_list_users_with_filter(client: TestClient) -> None:
    """GET /api/v1/User?age__gte=30 should filter users."""
    # Arrange - Create users with different ages
    for name, age in [("Alice", 25), ("Bob", 30), ("Charlie", 35)]:
        user_data = {
            "name": name,
            "email": f"{name.lower()}@example.com",
            "age": age,
            "created_at": "2026-01-17T00:00:00",
        }
        client.post("/api/v1/User", json=user_data)

    # Act
    response = client.get("/api/v1/User?age__gte=30")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(item["age"] >= 30 for item in data["items"])


def test_e2e_list_users_with_sort(client: TestClient) -> None:
    """GET /api/v1/User?sort=name should sort users."""
    # Arrange - Create users in random order
    for name in ["Charlie", "Alice", "Bob"]:
        user_data = {
            "name": name,
            "email": f"{name.lower()}@example.com",
            "created_at": "2026-01-17T00:00:00",
        }
        client.post("/api/v1/User", json=user_data)

    # Act
    response = client.get("/api/v1/User?sort=name")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["name"] == "Alice"
    assert data["items"][1]["name"] == "Bob"
    assert data["items"][2]["name"] == "Charlie"


def test_e2e_list_users_with_pagination(client: TestClient) -> None:
    """GET /api/v1/User?page=2&page_size=2 should paginate users."""
    # Arrange - Create multiple users
    for i in range(5):
        user_data = {
            "name": f"User{i}",
            "email": f"user{i}@example.com",
            "created_at": "2026-01-17T00:00:00",
        }
        client.post("/api/v1/User", json=user_data)

    # Act
    response = client.get("/api/v1/User?page=2&page_size=2")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert data["page_size"] == 2
    assert len(data["items"]) == 2
    assert data["total"] == 5


# =============================================================================
# TESTS - UPDATE
# =============================================================================
def test_e2e_update_user_returns_updated_entity(client: TestClient) -> None:
    """PUT /api/v1/User/{id} should update user."""
    # Arrange - Create user first
    user_data = {
        "name": "Alice",
        "email": "alice@example.com",
        "age": 30,
        "created_at": "2026-01-17T00:00:00",
    }
    create_response = client.post("/api/v1/User", json=user_data)
    user_id = create_response.json()["id"]

    # Act
    response = client.put(f"/api/v1/User/{user_id}", json={"age": 31})

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["age"] == 31
    assert data["name"] == "Alice"  # Unchanged


def test_e2e_update_nonexistent_user_returns_404(client: TestClient) -> None:
    """PUT /api/v1/User/999 should return 404."""
    # Act
    response = client.put("/api/v1/User/999", json={"age": 31})

    # Assert
    assert response.status_code == 404


# =============================================================================
# TESTS - DELETE
# =============================================================================
def test_e2e_delete_user_returns_204(client: TestClient) -> None:
    """DELETE /api/v1/User/{id} should delete user."""
    # Arrange - Create user first
    user_data = {
        "name": "Alice",
        "email": "alice@example.com",
        "created_at": "2026-01-17T00:00:00",
    }
    create_response = client.post("/api/v1/User", json=user_data)
    user_id = create_response.json()["id"]

    # Act
    response = client.delete(f"/api/v1/User/{user_id}")

    # Assert
    assert response.status_code == 204

    # Verify deletion
    get_response = client.get(f"/api/v1/User/{user_id}")
    assert get_response.status_code == 404


def test_e2e_delete_nonexistent_user_returns_404(client: TestClient) -> None:
    """DELETE /api/v1/User/999 should return 404."""
    # Act
    response = client.delete("/api/v1/User/999")

    # Assert
    assert response.status_code == 404


# =============================================================================
# TESTS - BULK UPDATE
# =============================================================================
def test_e2e_bulk_update_users_returns_200(client: TestClient) -> None:
    """PUT /api/v1/User/bulk should update multiple users."""
    # Arrange - Create users first
    user1 = client.post(
        "/api/v1/User",
        json={
            "name": "Alice",
            "email": "alice@example.com",
            "age": 30,
            "created_at": "2026-01-17T00:00:00",
        },
    ).json()
    user2 = client.post(
        "/api/v1/User",
        json={
            "name": "Bob",
            "email": "bob@example.com",
            "age": 25,
            "created_at": "2026-01-17T00:00:00",
        },
    ).json()

    # Act - Bulk update
    update_data = [
        {"id": user1["id"], "name": "Updated Alice", "age": 31},
        {"id": user2["id"], "email": "updated_bob@example.com"},
    ]
    response = client.put("/api/v1/User/bulk", json=update_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Updated Alice"
    assert data[0]["age"] == 31
    assert data[1]["email"] == "updated_bob@example.com"


def test_e2e_bulk_update_users_missing_id_returns_422(client: TestClient) -> None:
    """PUT /api/v1/User/bulk should return 422 if 'id' is missing."""
    # Arrange
    update_data = [{"name": "Alice"}]  # Missing 'id'

    # Act
    response = client.put("/api/v1/User/bulk", json=update_data)

    # Assert
    assert response.status_code == 422


def test_e2e_bulk_update_users_nonexistent_id_returns_404(client: TestClient) -> None:
    """PUT /api/v1/User/bulk should return 404 if any ID doesn't exist."""
    # Arrange
    update_data = [{"id": 999, "name": "Test"}]

    # Act
    response = client.put("/api/v1/User/bulk", json=update_data)

    # Assert
    assert response.status_code == 404


def test_e2e_bulk_update_users_empty_list_returns_empty(client: TestClient) -> None:
    """PUT /api/v1/User/bulk with empty list should return empty list."""
    # Act
    response = client.put("/api/v1/User/bulk", json=[])

    # Assert
    assert response.status_code == 200
    assert response.json() == []


# =============================================================================
# TESTS - BULK DELETE
# =============================================================================
def test_e2e_bulk_delete_users_returns_200(client: TestClient) -> None:
    """DELETE /api/v1/User/bulk should delete multiple users."""
    # Arrange - Create users first
    user1 = client.post(
        "/api/v1/User",
        json={
            "name": "Alice",
            "email": "alice@example.com",
            "created_at": "2026-01-17T00:00:00",
        },
    ).json()
    user2 = client.post(
        "/api/v1/User",
        json={
            "name": "Bob",
            "email": "bob@example.com",
            "created_at": "2026-01-17T00:00:00",
        },
    ).json()
    user3 = client.post(
        "/api/v1/User",
        json={
            "name": "Charlie",
            "email": "charlie@example.com",
            "created_at": "2026-01-17T00:00:00",
        },
    ).json()

    # Act - Bulk delete
    entity_ids = [user1["id"], user2["id"]]
    response = client.request("DELETE", "/api/v1/User/bulk", json=entity_ids)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert data["model_name"] == "User"

    # Verify users are deleted
    assert client.get(f"/api/v1/User/{user1['id']}").status_code == 404
    assert client.get(f"/api/v1/User/{user2['id']}").status_code == 404

    # Verify user3 still exists
    assert client.get(f"/api/v1/User/{user3['id']}").status_code == 200


def test_e2e_bulk_delete_users_nonexistent_id_returns_404(client: TestClient) -> None:
    """DELETE /api/v1/User/bulk should return 404 if any ID doesn't exist."""
    # Arrange
    entity_ids = [999, 1000]

    # Act
    response = client.request("DELETE", "/api/v1/User/bulk", json=entity_ids)

    # Assert
    assert response.status_code == 404


def test_e2e_bulk_delete_users_empty_list_returns_zero(client: TestClient) -> None:
    """DELETE /api/v1/User/bulk with empty list should return count 0."""
    # Act
    response = client.request("DELETE", "/api/v1/User/bulk", json=[])

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["model_name"] == "User"
