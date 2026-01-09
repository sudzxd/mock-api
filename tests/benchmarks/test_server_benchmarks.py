"""Benchmark tests for Server performance.

Tests server initialization and API endpoint performance:
- Server initialization overhead
- FastAPI app creation
- Data pre-population
- API endpoint throughput (GET, POST, LIST)
- End-to-end server startup time

Performance targets:
- Server initialization: < 500ms
- App creation: < 100ms
- Data pre-population (100 items): < 2s
- GET request: < 50ms
- POST request: < 100ms
- LIST request: < 100ms
"""

# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Third-party
import pytest
from fastapi.testclient import TestClient

# Project/Local
from mock_api.core.server import Server
from pytest_benchmark.fixture import BenchmarkFixture

# =============================================================================
# TESTS: Server Initialization
# =============================================================================


@pytest.mark.benchmark(group="server-init")
def test_server_initialization(
    benchmark: BenchmarkFixture,
    benchmark_models_path: str,
) -> None:
    """Benchmark server initialization without app creation.

    Performance target: < 500ms
    Tests parser, store, router initialization overhead.
    """

    def init_server() -> None:
        Server(
            models_file=str(benchmark_models_path),
            generate_data=False,
        )

    benchmark(init_server)


@pytest.mark.benchmark(group="server-init")
def test_app_creation(
    benchmark: BenchmarkFixture,
    benchmark_models_path: str,
) -> None:
    """Benchmark FastAPI app creation without data.

    Performance target: < 100ms
    Tests FastAPI app initialization and route registration.
    """
    server = Server(
        models_file=str(benchmark_models_path),
        generate_data=False,
    )

    def create_app() -> None:
        server.create_app()

    benchmark.pedantic(create_app, iterations=1, rounds=10)


@pytest.mark.benchmark(group="server-init")
def test_app_creation_with_data(
    benchmark: BenchmarkFixture,
    benchmark_models_path: str,
) -> None:
    """Benchmark FastAPI app creation with data pre-population.

    Performance target: < 2s for 10 items per model
    Tests complete server initialization including data generation.
    """

    def create_with_data() -> None:
        server = Server(
            models_file=str(benchmark_models_path),
            generate_data=True,
            data_count=10,
        )
        server.create_app()

    benchmark.pedantic(create_with_data, iterations=1, rounds=5)


# =============================================================================
# TESTS: Data Population
# =============================================================================


@pytest.mark.benchmark(group="server-data-population")
def test_data_prepopulation_small(
    benchmark: BenchmarkFixture,
    benchmark_models_path: str,
) -> None:
    """Benchmark pre-populating 10 items per model.

    Performance target: < 500ms
    Tests DataGenerator + Store overhead for small batches.
    """

    def populate() -> None:
        # Create fresh server each time to avoid duplicate ID errors
        server = Server(
            models_file=str(benchmark_models_path),
            generate_data=False,
        )
        server.populate_data()

    benchmark(populate)


@pytest.mark.benchmark(group="server-data-population")
def test_data_prepopulation_medium(
    benchmark: BenchmarkFixture,
    benchmark_models_path: str,
) -> None:
    """Benchmark pre-populating 50 items per model.

    Performance target: < 2s
    Tests scaling of data generation and store operations.
    """

    def populate() -> None:
        # Create fresh server each time to avoid duplicate ID errors
        server = Server(
            models_file=str(benchmark_models_path),
            generate_data=False,
        )
        # Manually set data_count and populate
        server.data_count = 50
        server.populate_data()

    benchmark(populate)


# =============================================================================
# TESTS: API Endpoint Throughput
# =============================================================================


@pytest.mark.benchmark(group="server-api-throughput")
def test_api_get_throughput(
    benchmark: BenchmarkFixture,
    benchmark_models_path: str,
) -> None:
    """Benchmark GET /api/v1/{model}/{id} endpoint.

    Performance target: < 50ms
    Tests FastAPI + Store read overhead.
    """
    server = Server(
        models_file=str(benchmark_models_path),
        generate_data=True,
        data_count=10,
    )
    app = server.create_app()
    client = TestClient(app)

    def get_request() -> None:
        response = client.get("/api/v1/contacts/5")
        assert response.status_code == 200

    benchmark(get_request)


@pytest.mark.benchmark(group="server-api-throughput")
def test_api_post_throughput(
    benchmark: BenchmarkFixture,
    benchmark_models_path: str,
) -> None:
    """Benchmark POST /api/v1/{model} endpoint.

    Performance target: < 100ms
    Tests FastAPI + Pydantic validation + Store create overhead.
    """
    server = Server(
        models_file=str(benchmark_models_path),
        generate_data=False,
    )
    app = server.create_app()
    client = TestClient(app)

    counter = {"value": 0}

    def post_request() -> None:
        counter["value"] += 1
        response = client.post(
            "/api/v1/contacts",
            json={
                "name": f"Test {counter['value']}",
                "email": f"test{counter['value']}@example.com",
                "phone": "+1-555-0000",
            },
        )
        assert response.status_code == 201

    benchmark(post_request)


@pytest.mark.benchmark(group="server-api-throughput")
def test_api_list_throughput(
    benchmark: BenchmarkFixture,
    benchmark_models_path: str,
) -> None:
    """Benchmark GET /api/v1/{model}?page=1&page_size=20 endpoint.

    Performance target: < 100ms
    Tests FastAPI + Store list + pagination overhead.
    """
    server = Server(
        models_file=str(benchmark_models_path),
        generate_data=True,
        data_count=100,
    )
    app = server.create_app()
    client = TestClient(app)

    def list_request() -> None:
        response = client.get("/api/v1/contacts?page=1&page_size=20")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 20

    benchmark(list_request)


@pytest.mark.benchmark(group="server-api-throughput")
def test_api_update_throughput(
    benchmark: BenchmarkFixture,
    benchmark_models_path: str,
) -> None:
    """Benchmark PUT /api/v1/{model}/{id} endpoint.

    Performance target: < 100ms
    Tests FastAPI + Pydantic validation + Store update overhead.
    """
    server = Server(
        models_file=str(benchmark_models_path),
        generate_data=True,
        data_count=10,
    )
    app = server.create_app()
    client = TestClient(app)

    def update_request() -> None:
        response = client.put(
            "/api/v1/contacts/5",
            json={
                "name": "Updated Name",
                "email": "updated@example.com",
                "phone": "+1-555-9999",
            },
        )
        assert response.status_code == 200

    benchmark(update_request)


# =============================================================================
# TESTS: End-to-End Server Startup
# =============================================================================


@pytest.mark.benchmark(group="server-e2e")
def test_complete_server_startup(
    benchmark: BenchmarkFixture,
    benchmark_models_path: str,
) -> None:
    """Benchmark complete server startup (init + app + data).

    Performance target: < 3s for 20 items per model
    Tests full cold start time from file to running server.
    """

    def full_startup() -> None:
        server = Server(
            models_file=str(benchmark_models_path),
            generate_data=True,
            data_count=20,
        )
        app = server.create_app()
        assert app is not None
        assert server.has_app

    benchmark.pedantic(full_startup, iterations=1, rounds=5)
