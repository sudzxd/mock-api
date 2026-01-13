"""Tests for FastAPI router generation."""

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
from mock_api.core.constants import PRIMARY_KEY_FIELD, HTTPStatus
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
def router_generator(
    schemas: dict[str, ModelSchema], store: DataStore
) -> RouterGenerator:
    """Create a RouterGenerator instance."""
    return RouterGenerator(schemas, store)


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
# TESTS: Initialization
# =============================================================================


def test_router_generator_initialization(
    schemas: dict[str, ModelSchema], store: DataStore
) -> None:
    """Test RouterGenerator initializes correctly."""
    router_gen = RouterGenerator(schemas, store)

    assert router_gen.schemas == schemas
    assert router_gen.store == store
    assert router_gen.prefix == "/api/v1"


def test_router_generator_custom_prefix(
    schemas: dict[str, ModelSchema], store: DataStore
) -> None:
    """Test RouterGenerator with custom prefix."""
    router_gen = RouterGenerator(schemas, store, prefix="/api/v2")

    assert router_gen.prefix == "/api/v2"


def test_generate_routes_returns_router(router_generator: RouterGenerator) -> None:
    """Test generate_routes returns FastAPI router."""
    router = router_generator.generate_routes()

    assert router is not None
    assert len(router.routes) > 0


def test_generate_routes_creates_crud_endpoints(
    router_generator: RouterGenerator,
) -> None:
    """Test that 5 CRUD routes are created per model."""
    router = router_generator.generate_routes()

    # Each model gets 5 routes: LIST, CREATE, READ, UPDATE, DELETE
    # We have multiple models in the fixtures
    total_models = len(router_generator.schemas)
    expected_routes = total_models * 5

    assert len(router.routes) == expected_routes


# =============================================================================
# TESTS: LIST Endpoint
# =============================================================================


def test_list_empty_collection(client: TestClient) -> None:
    """Test listing when collection is empty."""
    response = client.get("/api/v1/contacts")

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["items"] == []
    assert data["pagination"]["total_items"] == 0
    assert data["pagination"]["page"] == 1


def test_list_with_data(client: TestClient, store: DataStore) -> None:
    """Test listing with data in store."""
    # Add test data
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

    response = client.get("/api/v1/contacts")

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data["items"]) == 2
    assert data["pagination"]["total_items"] == 2


def test_list_pagination(client: TestClient, store: DataStore) -> None:
    """Test list endpoint pagination."""
    # Create 25 contacts
    for i in range(1, 26):
        store.create(
            "Contact",
            {
                "name": f"User {i}",
                "email": f"user{i}@example.com",
                "phone": f"555-{i:04d}",
                "username": f"user{i}",
                "first_name": "User",
                "last_name": f"{i}",
            },
        )

    # Get first page
    response = client.get("/api/v1/contacts?page=1&page_size=10")

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data["items"]) == 10
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 10
    assert data["pagination"]["total_items"] == 25
    assert data["pagination"]["total_pages"] == 3


def test_list_second_page(client: TestClient, store: DataStore) -> None:
    """Test getting second page of results."""
    for i in range(1, 26):
        store.create(
            "Contact",
            {
                "name": f"User {i}",
                "email": f"user{i}@example.com",
                "phone": f"555-{i:04d}",
                "username": f"user{i}",
                "first_name": "User",
                "last_name": f"{i}",
            },
        )

    response = client.get("/api/v1/contacts?page=2&page_size=10")

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data["items"]) == 10
    assert data["items"][0]["id"] == 11


def test_list_invalid_page_number(client: TestClient) -> None:
    """Test list with invalid page number."""
    response = client.get("/api/v1/contacts?page=0")

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_list_invalid_page_size(client: TestClient) -> None:
    """Test list with invalid page size."""
    response = client.get("/api/v1/contacts?page_size=1000")

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


# =============================================================================
# TESTS: CREATE Endpoint
# =============================================================================


def test_create_valid_instance(client: TestClient) -> None:
    """Test creating a valid instance."""
    payload = {
        "name": "Alice",
        "email": "alice@example.com",
        "phone": "555-1234",
        "username": "alice",
        "first_name": "Alice",
        "last_name": "Smith",
    }

    response = client.post("/api/v1/contacts", json=payload)

    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data["name"] == "Alice"
    assert data["email"] == "alice@example.com"
    assert PRIMARY_KEY_FIELD in data


def test_create_assigns_id(client: TestClient) -> None:
    """Test that create assigns an ID."""
    payload = {
        "name": "Bob",
        "email": "bob@example.com",
        "phone": "555-5678",
        "username": "bob",
        "first_name": "Bob",
        "last_name": "Jones",
    }

    response = client.post("/api/v1/contacts", json=payload)

    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data["id"] == 1


def test_create_validation_error(client: TestClient) -> None:
    """Test create with invalid data returns 422."""
    payload = {"invalid_field": "value"}

    response = client.post("/api/v1/contacts", json=payload)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    data = response.json()
    assert "detail" in data


def test_create_missing_required_fields(client: TestClient) -> None:
    """Test create with missing required fields."""
    payload = {"name": "Alice"}  # Missing other required fields

    response = client.post("/api/v1/contacts", json=payload)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


# =============================================================================
# TESTS: READ Endpoint
# =============================================================================


def test_read_existing_instance(client: TestClient, store: DataStore) -> None:
    """Test reading an existing instance."""
    created = store.create(
        "Contact",
        {
            "name": "Alice",
            "email": "alice@example.com",
            "phone": "555-1234",
            "username": "alice",
            "first_name": "Alice",
            "last_name": "Smith",
        },
    )
    instance_id = created["id"]

    response = client.get(f"/api/v1/contacts/{instance_id}")

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["id"] == instance_id
    assert data["name"] == "Alice"


def test_read_nonexistent_instance(client: TestClient) -> None:
    """Test reading non-existent instance returns 404."""
    response = client.get("/api/v1/contacts/999")

    assert response.status_code == HTTPStatus.NOT_FOUND
    data = response.json()
    assert "detail" in data


# =============================================================================
# TESTS: UPDATE Endpoint
# =============================================================================


def test_update_existing_instance(client: TestClient, store: DataStore) -> None:
    """Test updating an existing instance."""
    created = store.create(
        "Contact",
        {
            "name": "Alice",
            "email": "alice@example.com",
            "phone": "555-0000",
            "username": "alice",
            "first_name": "Alice",
            "last_name": "Jones",
        },
    )
    instance_id = created["id"]

    payload = {
        "name": "Alice Smith",
        "email": "alice.smith@example.com",
        "phone": "555-0000",
        "username": "asmith",
        "first_name": "Alice",
        "last_name": "Smith",
    }

    response = client.put(f"/api/v1/contacts/{instance_id}", json=payload)

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["id"] == instance_id
    assert data["name"] == "Alice Smith"
    assert data["email"] == "alice.smith@example.com"


def test_update_nonexistent_instance(client: TestClient) -> None:
    """Test updating non-existent instance returns 404."""
    payload = {
        "name": "Ghost",
        "email": "ghost@example.com",
        "phone": "555-9999",
        "username": "ghost",
        "first_name": "Ghost",
        "last_name": "User",
    }

    response = client.put("/api/v1/contacts/999", json=payload)

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_update_validation_error(client: TestClient, store: DataStore) -> None:
    """Test update with invalid data returns 422."""
    created = store.create(
        "Contact",
        {
            "name": "Alice",
            "email": "alice@example.com",
            "phone": "555-1234",
            "username": "alice",
            "first_name": "Alice",
            "last_name": "Smith",
        },
    )
    instance_id = created["id"]

    payload = {"invalid_field": "value"}

    response = client.put(f"/api/v1/contacts/{instance_id}", json=payload)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


# =============================================================================
# TESTS: DELETE Endpoint
# =============================================================================


def test_delete_existing_instance(client: TestClient, store: DataStore) -> None:
    """Test deleting an existing instance."""
    created = store.create(
        "Contact",
        {
            "name": "Alice",
            "email": "alice@example.com",
            "phone": "555-1234",
            "username": "alice",
            "first_name": "Alice",
            "last_name": "Smith",
        },
    )
    instance_id = created["id"]

    response = client.delete(f"/api/v1/contacts/{instance_id}")

    assert response.status_code == HTTPStatus.NO_CONTENT

    # Verify deletion
    get_response = client.get(f"/api/v1/contacts/{instance_id}")
    assert get_response.status_code == HTTPStatus.NOT_FOUND


def test_delete_nonexistent_instance(client: TestClient) -> None:
    """Test deleting non-existent instance returns 404."""
    response = client.delete("/api/v1/contacts/999")

    assert response.status_code == HTTPStatus.NOT_FOUND


# =============================================================================
# TESTS: Multiple Models
# =============================================================================


def test_multiple_models_have_separate_endpoints(client: TestClient) -> None:
    """Test that different models have separate endpoints."""
    contact_response = client.get("/api/v1/contacts")
    author_response = client.get("/api/v1/authors")

    assert contact_response.status_code == HTTPStatus.OK
    assert author_response.status_code == HTTPStatus.OK


def test_models_dont_share_data(client: TestClient, store: DataStore) -> None:
    """Test that different models don't share data."""
    store.create(
        "Contact",
        {
            "name": "Alice",
            "email": "alice@example.com",
            "phone": "555-1234",
            "username": "alice",
            "first_name": "Alice",
            "last_name": "Smith",
        },
    )
    store.create("Author", {"name": "Bob"})

    contact_response = client.get("/api/v1/contacts")
    author_response = client.get("/api/v1/authors")

    contact_data = contact_response.json()
    author_data = author_response.json()

    assert len(contact_data["items"]) == 1
    assert len(author_data["items"]) == 1
    assert contact_data["items"][0]["name"] == "Alice"
    assert author_data["items"][0]["name"] == "Bob"


# =============================================================================
# TESTS: Model Registry
# =============================================================================


def test_model_registry_stores_models(router_generator: RouterGenerator) -> None:
    """Test that model registry stores all model types."""
    # Registry should be built during __init__
    for model_name in router_generator.schemas:
        # Should not raise KeyError
        response_model = router_generator.registry.get_response_model(model_name)
        input_model = router_generator.registry.get_input_model(model_name)
        list_model = router_generator.registry.get_list_response_model(model_name)

        assert response_model is not None
        assert input_model is not None
        assert list_model is not None


# =============================================================================
# TESTS: Edge Cases
# =============================================================================


def test_create_with_optional_fields(client: TestClient) -> None:
    """Test creating instance with optional fields as None."""
    payload = {
        "name": "Test Product",
        "priority": 1,
        "status": None,  # Optional field
        "description": None,  # Optional field
    }

    response = client.post("/api/v1/products", json=payload)

    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data["status"] is None
    assert data["description"] is None


def test_update_preserves_id(client: TestClient, store: DataStore) -> None:
    """Test that update preserves the instance ID."""
    created = store.create(
        "Contact",
        {
            "name": "Alice",
            "email": "alice@example.com",
            "phone": "555-0000",
            "username": "alice",
            "first_name": "Alice",
            "last_name": "Jones",
        },
    )
    original_id = created["id"]

    payload = {
        "name": "Updated",
        "email": "updated@example.com",
        "phone": "555-0000",
        "username": "updated",
        "first_name": "Updated",
        "last_name": "User",
    }

    response = client.put(f"/api/v1/contacts/{original_id}", json=payload)

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["id"] == original_id


def test_routes_use_correct_http_methods(app: FastAPI) -> None:
    """Test that routes use correct HTTP methods."""
    # Collect all methods for each path
    # (FastAPI creates separate routes for each method)
    route_methods: dict[str, set[str]] = {}
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            if route.path not in route_methods:  # type: ignore[attr-defined]
                route_methods[route.path] = set()  # type: ignore[attr-defined]
            route_methods[route.path].update(route.methods)  # type: ignore[attr-defined]

    # Check Contact routes
    assert "GET" in route_methods["/api/v1/contacts"]
    assert "POST" in route_methods["/api/v1/contacts"]
    assert "GET" in route_methods["/api/v1/contacts/{instance_id}"]
    assert "PUT" in route_methods["/api/v1/contacts/{instance_id}"]
    assert "DELETE" in route_methods["/api/v1/contacts/{instance_id}"]


# =============================================================================
# TESTS: Filtering Integration
# =============================================================================


def test_list_with_equality_filter_query_param(app: FastAPI, store: DataStore) -> None:
    """Test list with equality filter via query parameter."""
    client = TestClient(app)

    products = [
        {"id": 1, "name": "Widget", "priority": 1, "status": "active"},
        {"id": 2, "name": "Gadget", "priority": 2, "status": "active"},
        {"id": 3, "name": "Gizmo", "priority": 1, "status": "inactive"},
    ]
    store.load({"Product": products})

    response = client.get("/api/v1/products?status=active")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data["items"]) == 2
    assert all(item["status"] == "active" for item in data["items"])


def test_list_with_comparison_filter_gte(app: FastAPI, store: DataStore) -> None:
    """Test list with gte comparison filter."""
    client = TestClient(app)

    products = [
        {"id": 1, "name": "Widget", "priority": 1, "status": "active"},
        {"id": 2, "name": "Gadget", "priority": 2, "status": "active"},
        {"id": 3, "name": "Gizmo", "priority": 3, "status": "inactive"},
    ]
    store.load({"Product": products})

    response = client.get("/api/v1/products?priority__gte=2")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data["items"]) == 2
    assert all(item["priority"] >= 2 for item in data["items"])


def test_list_filter_invalid_field_returns_400(app: FastAPI, store: DataStore) -> None:
    """Test that invalid filter field returns 400 error."""
    client = TestClient(app)

    products = [{"id": 1, "name": "Widget", "priority": 1, "status": "active"}]
    store.load({"Product": products})

    response = client.get("/api/v1/products?invalid_field=test")
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "invalid_field" in response.json()["detail"].lower()


# =============================================================================
# TESTS: Sorting Integration
# =============================================================================


def test_list_with_sort_ascending(app: FastAPI, store: DataStore) -> None:
    """Test list with ascending sort."""
    client = TestClient(app)

    products = [
        {"id": 1, "name": "Zebra", "priority": 1, "status": "active"},
        {"id": 2, "name": "Apple", "priority": 2, "status": "active"},
        {"id": 3, "name": "Mango", "priority": 3, "status": "inactive"},
    ]
    store.load({"Product": products})

    response = client.get("/api/v1/products?sort=name")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    names = [item["name"] for item in data["items"]]
    assert names == ["Apple", "Mango", "Zebra"]


def test_list_with_sort_descending(app: FastAPI, store: DataStore) -> None:
    """Test list with descending sort."""
    client = TestClient(app)

    products = [
        {"id": 1, "name": "Widget", "priority": 1, "status": "active"},
        {"id": 2, "name": "Gadget", "priority": 2, "status": "active"},
        {"id": 3, "name": "Gizmo", "priority": 3, "status": "inactive"},
    ]
    store.load({"Product": products})

    response = client.get("/api/v1/products?sort=-priority")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    priorities = [item["priority"] for item in data["items"]]
    assert priorities == [3, 2, 1]


def test_list_sort_invalid_field_returns_400(app: FastAPI, store: DataStore) -> None:
    """Test that invalid sort field returns 400 error."""
    client = TestClient(app)

    products = [{"id": 1, "name": "Widget", "priority": 1, "status": "active"}]
    store.load({"Product": products})

    response = client.get("/api/v1/products?sort=invalid_field")
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "invalid_field" in response.json()["detail"].lower()


# =============================================================================
# TESTS: Combined Filtering, Sorting, and Pagination
# =============================================================================


def test_list_with_filter_sort_and_page_pagination(
    app: FastAPI, store: DataStore
) -> None:
    """Test list with filter, sort, and page-based pagination."""
    client = TestClient(app)

    products = [
        {"id": 1, "name": "Widget", "priority": 1, "status": "active"},
        {"id": 2, "name": "Gadget", "priority": 2, "status": "active"},
        {"id": 3, "name": "Gizmo", "priority": 3, "status": "active"},
        {"id": 4, "name": "Thing", "priority": 1, "status": "inactive"},
    ]
    store.load({"Product": products})

    response = client.get(
        "/api/v1/products?status=active&sort=-priority&page=1&page_size=2"
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()

    assert len(data["items"]) == 2
    assert data["items"][0]["priority"] == 3  # Gizmo
    assert data["items"][1]["priority"] == 2  # Gadget
    assert data["pagination"]["total_items"] == 3
    assert data["pagination"]["total_pages"] == 2
    assert data["pagination"]["has_next"] is True
