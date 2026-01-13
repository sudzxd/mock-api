"""Tests for bulk operation API endpoints."""

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

# Project/Local
from mock_api.core.config import Config
from mock_api.core.constants import PRIMARY_KEY_FIELD, BulkResponseKey, HTTPStatus
from mock_api.core.parser import SchemaParser
from mock_api.core.router import RouterGenerator
from mock_api.core.store import DataStore
from mock_api.core.types import ModelSchema

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def parser() -> SchemaParser:
    """Create a SchemaParser instance."""
    return SchemaParser()


@pytest.fixture
def router_models_file() -> str:
    """Path to router test models fixture file."""
    return str(Path(__file__).parent / "fixtures" / "generator_models.py")


@pytest.fixture
def schemas(parser: SchemaParser, router_models_file: str) -> dict[str, ModelSchema]:
    """Parse all test schemas."""
    return parser.parse_file(router_models_file)


@pytest.fixture
def store() -> DataStore:
    """Create a fresh data store instance."""
    return DataStore()


@pytest.fixture
def config() -> Config:
    """Create a config instance with default bulk operations settings."""
    return Config()


@pytest.fixture
def router_generator(
    schemas: dict[str, ModelSchema], store: DataStore, config: Config
) -> RouterGenerator:
    """Create a RouterGenerator instance."""
    return RouterGenerator(schemas, store, config=config)


@pytest.fixture
def app(router_generator: RouterGenerator) -> FastAPI:
    """Create FastAPI app with generated routes."""
    app = FastAPI()
    router = router_generator.generate_routes()
    app.include_router(router)
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create TestClient for API testing."""
    return TestClient(app)


# =============================================================================
# TESTS: Bulk Create Endpoint
# =============================================================================


def test_bulk_create_success(client: TestClient) -> None:
    """Test bulk create endpoint with valid data."""
    data = {
        "data": [
            {
                "name": "Alice",
                "email": "alice@example.com",
                "phone": "555-1111",
                "username": "alice",
                "first_name": "Alice",
                "last_name": "Smith",
            },
            {
                "name": "Bob",
                "email": "bob@example.com",
                "phone": "555-2222",
                "username": "bob",
                "first_name": "Bob",
                "last_name": "Jones",
            },
        ]
    }

    response = client.post("/api/v1/contacts/bulk", json=data)

    assert response.status_code == HTTPStatus.CREATED
    result = response.json()
    assert result[BulkResponseKey.CREATED] == 2
    assert len(result[BulkResponseKey.DATA]) == 2
    assert BulkResponseKey.ERRORS not in result


def test_bulk_create_empty_array(client: TestClient) -> None:
    """Test bulk create with empty array."""
    response = client.post("/api/v1/contacts/bulk", json={"data": []})

    assert response.status_code == HTTPStatus.CREATED
    result = response.json()
    assert result[BulkResponseKey.CREATED] == 0


def test_bulk_create_missing_data_field(client: TestClient) -> None:
    """Test bulk create without data field."""
    response = client.post("/api/v1/contacts/bulk", json={})

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "data" in response.json()["detail"].lower()


def test_bulk_create_validation_error(client: TestClient) -> None:
    """Test bulk create with invalid item."""
    data = {
        "data": [
            {
                "name": "Alice",
                # Missing required fields: email, phone, username, first_name, last_name
            }
        ]
    }

    response = client.post("/api/v1/contacts/bulk", json=data)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    detail = response.json()["detail"]
    assert "Validation failed" in detail["message"]
    assert detail["errors"] is not None


def test_bulk_create_exceeds_batch_size(client: TestClient, config: Config) -> None:
    """Test bulk create exceeding max batch size."""
    max_size = config.bulk_operations.max_batch_size
    data = {
        "data": [
            {
                "name": f"User{i}",
                "email": f"user{i}@example.com",
                "phone": f"555-{i:04d}",
                "username": f"user{i}",
                "first_name": "User",
                "last_name": str(i),
            }
            for i in range(max_size + 1)
        ]
    }

    response = client.post("/api/v1/contacts/bulk", json=data)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "exceeds maximum" in response.json()["detail"]


# =============================================================================
# TESTS: Bulk Update Endpoint
# =============================================================================


def test_bulk_update_success(client: TestClient, store: DataStore) -> None:
    """Test bulk update endpoint with valid data."""
    # Create initial data
    store.create(
        "Contact",
        {
            "name": "Alice",
            "email": "alice@example.com",
            "phone": "555-1111",
            "username": "alice",
            "first_name": "Alice",
            "last_name": "Smith",
        },
    )
    store.create(
        "Contact",
        {
            "name": "Bob",
            "email": "bob@example.com",
            "phone": "555-2222",
            "username": "bob",
            "first_name": "Bob",
            "last_name": "Jones",
        },
    )

    # Update via bulk endpoint (need all required fields for Contact model)
    data = {
        "data": [
            {
                PRIMARY_KEY_FIELD: 1,
                "name": "Alice Updated",
                "email": "alice@example.com",
                "phone": "555-1111",
                "username": "alice",
                "first_name": "Alice",
                "last_name": "Smith",
            },
            {
                PRIMARY_KEY_FIELD: 2,
                "name": "Bob Updated",
                "email": "bob@example.com",
                "phone": "555-2222",
                "username": "bob",
                "first_name": "Bob",
                "last_name": "Jones",
            },
        ]
    }

    response = client.put("/api/v1/contacts/bulk", json=data)

    assert response.status_code == HTTPStatus.OK
    result = response.json()
    assert result[BulkResponseKey.UPDATED] == 2
    assert len(result[BulkResponseKey.DATA]) == 2

    # Verify updates
    get_response = client.get("/api/v1/contacts/1")
    assert get_response.json()["name"] == "Alice Updated"


def test_bulk_update_empty_array(client: TestClient) -> None:
    """Test bulk update with empty array."""
    response = client.put("/api/v1/contacts/bulk", json={"data": []})

    assert response.status_code == HTTPStatus.OK
    result = response.json()
    assert result[BulkResponseKey.UPDATED] == 0


def test_bulk_update_missing_id(client: TestClient) -> None:
    """Test bulk update with missing ID field."""
    data = {"data": [{"name": "Missing ID"}]}

    response = client.put("/api/v1/contacts/bulk", json=data)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "id" in response.json()["detail"].lower()


def test_bulk_update_not_found(client: TestClient, store: DataStore) -> None:
    """Test bulk update with non-existent ID."""
    store.create(
        "Contact",
        {
            "name": "Alice",
            "email": "alice@example.com",
            "phone": "555-1111",
            "username": "alice",
            "first_name": "Alice",
            "last_name": "Smith",
        },
    )

    data = {
        "data": [
            {
                PRIMARY_KEY_FIELD: 1,
                "name": "Alice Updated",
                "email": "alice@example.com",
                "phone": "555-1111",
                "username": "alice",
                "first_name": "Alice",
                "last_name": "Smith",
            },
            {
                PRIMARY_KEY_FIELD: 999,
                "name": "Not Found",
                "email": "notfound@example.com",
                "phone": "555-9999",
                "username": "notfound",
                "first_name": "Not",
                "last_name": "Found",
            },
        ]
    }

    response = client.put("/api/v1/contacts/bulk", json=data)

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_bulk_update_validation_error(client: TestClient, store: DataStore) -> None:
    """Test bulk update with invalid data."""
    store.create(
        "Contact",
        {
            "name": "Alice",
            "email": "alice@example.com",
            "phone": "555-1111",
            "username": "alice",
            "first_name": "Alice",
            "last_name": "Smith",
        },
    )

    data = {
        "data": [
            {
                PRIMARY_KEY_FIELD: 1,
                # Missing required fields to pass validation
                "invalid_field": "not_allowed",
            }
        ]
    }

    response = client.put("/api/v1/contacts/bulk", json=data)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_bulk_update_exceeds_batch_size(client: TestClient, config: Config) -> None:
    """Test bulk update exceeding max batch size."""
    max_size = config.bulk_operations.max_batch_size
    data = {
        "data": [
            {
                PRIMARY_KEY_FIELD: i,
                "name": f"User{i}",
                "email": f"user{i}@example.com",
                "phone": f"555-{i:04d}",
                "username": f"user{i}",
                "first_name": "User",
                "last_name": str(i),
            }
            for i in range(1, max_size + 2)
        ]
    }

    response = client.put("/api/v1/contacts/bulk", json=data)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "exceeds maximum" in response.json()["detail"]


# =============================================================================
# TESTS: Bulk Delete Endpoint
# =============================================================================


def test_bulk_delete_success(client: TestClient, store: DataStore) -> None:
    """Test bulk delete endpoint with valid IDs."""
    # Create test data
    for i in range(5):
        store.create(
            "Contact",
            {
                "name": f"User{i}",
                "email": f"user{i}@example.com",
                "phone": f"555-{i:04d}",
                "username": f"user{i}",
                "first_name": "User",
                "last_name": str(i),
            },
        )

    response = client.delete("/api/v1/contacts/bulk?ids=1,2,3")

    assert response.status_code == HTTPStatus.OK
    result = response.json()
    assert result[BulkResponseKey.DELETED] == 3
    assert result[BulkResponseKey.IDS] == [1, 2, 3]
    assert BulkResponseKey.ERRORS not in result

    # Verify deletions
    assert store.count("Contact") == 2


def test_bulk_delete_single_id(client: TestClient, store: DataStore) -> None:
    """Test bulk delete with single ID."""
    store.create("Contact", {"name": "Alice", "email": "alice@example.com"})

    response = client.delete("/api/v1/contacts/bulk?ids=1")

    assert response.status_code == HTTPStatus.OK
    result = response.json()
    assert result[BulkResponseKey.DELETED] == 1


def test_bulk_delete_missing_ids_param(client: TestClient) -> None:
    """Test bulk delete without IDs parameter."""
    response = client.delete("/api/v1/contacts/bulk")

    assert response.status_code == 422  # FastAPI validation error


def test_bulk_delete_invalid_id_format(client: TestClient) -> None:
    """Test bulk delete with invalid ID format."""
    response = client.delete("/api/v1/contacts/bulk?ids=1,abc,3")

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "Invalid ID format" in response.json()["detail"]


def test_bulk_delete_not_found(client: TestClient, store: DataStore) -> None:
    """Test bulk delete with non-existent IDs."""
    store.create("Contact", {"name": "Alice", "email": "alice@example.com"})

    response = client.delete("/api/v1/contacts/bulk?ids=1,999")

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_bulk_delete_exceeds_batch_size(client: TestClient, config: Config) -> None:
    """Test bulk delete exceeding max batch size."""
    max_size = config.bulk_operations.max_batch_size
    ids = ",".join(str(i) for i in range(1, max_size + 2))

    response = client.delete(f"/api/v1/contacts/bulk?ids={ids}")

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "exceeds maximum" in response.json()["detail"]


def test_bulk_delete_with_spaces_in_ids(client: TestClient, store: DataStore) -> None:
    """Test bulk delete handles spaces in ID list."""
    for i in range(3):
        store.create("Contact", {"name": f"User{i}", "email": f"user{i}@example.com"})

    # IDs with spaces
    response = client.delete("/api/v1/contacts/bulk?ids=1, 2, 3")

    assert response.status_code == HTTPStatus.OK
    result = response.json()
    assert result[BulkResponseKey.DELETED] == 3


# =============================================================================
# TESTS: Integration with Regular CRUD
# =============================================================================


def test_bulk_create_then_regular_read(client: TestClient, store: DataStore) -> None:
    """Test that bulk created items can be read via regular endpoint."""
    data = {
        "data": [
            {
                "name": "Alice",
                "email": "alice@example.com",
                "phone": "555-1111",
                "username": "alice",
                "first_name": "Alice",
                "last_name": "Smith",
            }
        ]
    }

    create_response = client.post("/api/v1/contacts/bulk", json=data)
    assert create_response.status_code == HTTPStatus.CREATED

    # Read via regular endpoint
    read_response = client.get("/api/v1/contacts/1")
    assert read_response.status_code == HTTPStatus.OK
    assert read_response.json()["name"] == "Alice"


def test_regular_create_then_bulk_update(client: TestClient, store: DataStore) -> None:
    """Test that regularly created items can be bulk updated."""
    # Create via regular endpoint
    create_data = {
        "name": "Alice",
        "email": "alice@example.com",
        "phone": "555-1111",
        "username": "alice",
        "first_name": "Alice",
        "last_name": "Smith",
    }
    client.post("/api/v1/contacts", json=create_data)

    # Update via bulk endpoint (need all required fields)
    update_data = {
        "data": [
            {
                PRIMARY_KEY_FIELD: 1,
                "name": "Alice Updated",
                "email": "alice@example.com",
                "phone": "555-1111",
                "username": "alice",
                "first_name": "Alice",
                "last_name": "Smith",
            }
        ]
    }
    update_response = client.put("/api/v1/contacts/bulk", json=update_data)

    assert update_response.status_code == HTTPStatus.OK
    result = update_response.json()
    assert result[BulkResponseKey.UPDATED] == 1


def test_bulk_operations_respect_model_schema(client: TestClient) -> None:
    """Test that bulk operations validate against model schema."""
    # Try to create with missing required fields
    data = {
        "data": [
            {"name": "Missing Fields"}  # Missing required email, phone, etc
        ]
    }

    response = client.post("/api/v1/contacts/bulk", json=data)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
