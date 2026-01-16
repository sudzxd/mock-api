"""Pytest fixtures for benchmark tests.

This module provides shared fixtures for all benchmark tests including:
- Pre-populated data stores
- Parsed schema instances
- Test clients
- Benchmark models
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from pathlib import Path

# Third-party
import pytest
from fastapi.testclient import TestClient
from mock_api.core.generator import DataGenerator
from mock_api.core.parser import SchemaParser
from mock_api.core.router import RouterGenerator
from mock_api.core.server import Server
from mock_api.core.services import FilterParser, ModelFactory, SortParser
from mock_api.core.store import DataStore

# Project/Local
from mock_api.core.types import ModelSchema
from pydantic import BaseModel

# =============================================================================
# PATH FIXTURES
# =============================================================================


@pytest.fixture(scope="session")
def benchmark_fixtures_dir() -> Path:
    """Path to benchmark fixture models directory."""
    return Path(__file__).parent.parent / "fixtures"


@pytest.fixture(scope="session")
def benchmark_models_path(benchmark_fixtures_dir: Path) -> Path:
    """Path to benchmark_models.py file."""
    return benchmark_fixtures_dir / "benchmark_models.py"


@pytest.fixture
def filter_parser() -> FilterParser:
    """Fixture for FilterParser instance."""
    return FilterParser()


@pytest.fixture
def sort_parser() -> SortParser:
    """Fixture for SortParser instance."""
    return SortParser()


# =============================================================================
# PARSER FIXTURES
# =============================================================================


@pytest.fixture
def parser() -> SchemaParser:
    """Create a fresh SchemaParser instance."""
    return SchemaParser()


@pytest.fixture(scope="session")
def parsed_benchmark_schema(benchmark_models_path: str) -> dict[str, ModelSchema]:
    """Parse benchmark models once per session."""
    parser = SchemaParser()
    return parser.parse_file(benchmark_models_path)


# =============================================================================
# GENERATOR FIXTURES
# =============================================================================


@pytest.fixture
def generator(parsed_benchmark_schema: dict[str, ModelSchema]) -> DataGenerator:
    """Create a fresh DataGenerator instance."""
    return DataGenerator(schemas=parsed_benchmark_schema)


@pytest.fixture
def seeded_generator(parsed_benchmark_schema: dict[str, ModelSchema]) -> DataGenerator:
    """Create a DataGenerator with fixed seed for reproducibility."""
    return DataGenerator(schemas=parsed_benchmark_schema, seed=42)


# =============================================================================
# STORE FIXTURES
# =============================================================================


@pytest.fixture
def empty_store() -> DataStore:
    """Create an empty DataStore instance."""
    return DataStore()


@pytest.fixture
def small_populated_store() -> DataStore:
    """DataStore pre-populated with 10 simple instances."""
    store = DataStore()
    data = {
        "Contact": [
            {
                "id": i,
                "name": f"Person {i}",
                "email": f"person{i}@example.com",
                "phone": f"+1-555-000-{i:04d}",
            }
            for i in range(1, 11)
        ]
    }
    store.load(data)
    return store


@pytest.fixture
def medium_populated_store() -> DataStore:
    """DataStore pre-populated with 100 simple instances."""
    store = DataStore()
    data = {
        "Contact": [
            {
                "id": i,
                "name": f"Person {i}",
                "email": f"person{i}@example.com",
                "phone": f"+1-555-000-{i:04d}",
            }
            for i in range(1, 101)
        ]
    }
    store.load(data)
    return store


@pytest.fixture
def large_populated_store() -> DataStore:
    """DataStore pre-populated with 1000 simple instances."""
    store = DataStore()
    data = {
        "Contact": [
            {
                "id": i,
                "name": f"Person {i}",
                "email": f"person{i}@example.com",
                "phone": f"+1-555-000-{i:04d}",
            }
            for i in range(1, 1001)
        ]
    }
    store.load(data)
    return store


# =============================================================================
# ROUTER FIXTURES
# =============================================================================


@pytest.fixture
def router_generator(
    filter_parser: FilterParser, sort_parser: SortParser
) -> RouterGenerator:
    """Create a fresh RouterGenerator instance."""
    model_factory = ModelFactory()
    return RouterGenerator(
        schemas={},
        store=DataStore(),
        filter_parser=filter_parser,
        sort_parser=sort_parser,
        model_factory=model_factory,
        prefix="/api/v1",
    )


# =============================================================================
# SERVER & CLIENT FIXTURES
# =============================================================================


@pytest.fixture
def benchmark_test_client(
    parsed_benchmark_schema: dict[str, type[BaseModel]],
) -> TestClient:
    """Create a TestClient with benchmark models loaded."""
    server = Server(
        models_file="",
        generate_data=True,
        data_count=10,
    )
    app = server.create_app()
    return TestClient(app)


@pytest.fixture
def empty_test_client(
    parsed_benchmark_schema: dict[str, type[BaseModel]],
) -> TestClient:
    """Create a TestClient with benchmark models but no pre-populated data."""
    server = Server(
        models_file="",
        generate_data=False,
    )
    app = server.create_app()
    return TestClient(app)


# =============================================================================
# DATA FIXTURES
# =============================================================================


@pytest.fixture
def sample_contact_data() -> dict[str, str | int]:
    """Sample contact data for create/update operations."""
    return {
        "id": 999,
        "name": "Test Contact",
        "email": "test@example.com",
        "phone": "+1-555-999-9999",
    }


@pytest.fixture
def batch_contact_data() -> list[dict[str, str | int]]:
    """Batch of contact data for bulk operations (100 items)."""
    return [
        {
            "id": 1000 + i,
            "name": f"Batch Contact {i}",
            "email": f"batch{i}@example.com",
            "phone": f"+1-555-999-{i:04d}",
        }
        for i in range(100)
    ]
