"""Benchmark tests for RouterGenerator performance.

Tests router generation performance across various scenarios:
- Router initialization and model registry building
- Single model route generation
- Router scaling with multiple models
- Model registry lookup operations
- Complete router generation (end-to-end)

Performance targets:
- Router initialization: < 100ms for 5 models
- Route generation: < 50ms per model
- Model registry lookup: < 1ms (O(1))
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Third-party
import pytest

# Project/Local
from mock_api.core.parser import SchemaParser
from mock_api.core.router import RouterGenerator
from mock_api.core.store import DataStore
from mock_api.core.types import ModelSchema
from pytest_benchmark.fixture import BenchmarkFixture

# =============================================================================
# TESTS: Router Initialization
# =============================================================================


@pytest.mark.benchmark(group="router-init")
def test_router_initialization(
    benchmark: BenchmarkFixture,
    parsed_benchmark_schema: dict[str, ModelSchema],
) -> None:
    """Benchmark router initialization with model registry building.

    Performance target: < 100ms for 8 models
    Tests model registry building overhead (O(n*m) where n=models, m=fields).
    """
    store = DataStore()

    def init_router() -> None:
        RouterGenerator(schemas=parsed_benchmark_schema, store=store)

    benchmark(init_router)


# =============================================================================
# TESTS: Route Generation
# =============================================================================


@pytest.mark.benchmark(group="router-generation")
def test_route_generation_small(
    benchmark: BenchmarkFixture,
    parsed_benchmark_schema: dict[str, ModelSchema],
) -> None:
    """Benchmark complete route generation for all models.

    Performance target: < 200ms for 8 models (8 * 5 routes = 40 routes)
    Tests FastAPI route registration overhead.
    """
    store = DataStore()

    def generate_routes() -> None:
        router_gen = RouterGenerator(schemas=parsed_benchmark_schema, store=store)
        router = router_gen.generate_routes()
        # Each model gets 5 routes (list, create, read, update, delete)
        assert len(router.routes) > 0

    benchmark(generate_routes)


@pytest.mark.benchmark(group="router-generation")
def test_route_generation_single_model(
    benchmark: BenchmarkFixture,
    benchmark_models_path: str,
) -> None:
    """Benchmark route generation for single simple model.

    Performance target: < 30ms for 1 model (5 routes)
    Tests per-model route generation overhead.
    """
    parser = SchemaParser()
    schemas = parser.parse_file(benchmark_models_path)
    # Use only Contact model
    contact_schema = {"Contact": schemas["Contact"]}
    store = DataStore()

    def generate_single() -> None:
        router_gen = RouterGenerator(schemas=contact_schema, store=store)
        router = router_gen.generate_routes()
        assert len(router.routes) == 5  # list, create, read, update, delete

    benchmark(generate_single)


# =============================================================================
# TESTS: Router Scaling
# =============================================================================


@pytest.mark.benchmark(group="router-scaling")
def test_router_scaling_small(
    benchmark: BenchmarkFixture,
    benchmark_models_path: str,
) -> None:
    """Benchmark router generation with 3 models.

    Performance target: < 100ms
    Tests O(n) scaling with model count.
    """
    parser = SchemaParser()
    schemas = parser.parse_file(benchmark_models_path)
    # Use Contact, Author, Book (3 models)
    subset_schemas = {
        "Contact": schemas["Contact"],
        "Author": schemas["Author"],
        "Book": schemas["Book"],
    }
    store = DataStore()

    def generate_small() -> None:
        router_gen = RouterGenerator(schemas=subset_schemas, store=store)
        router = router_gen.generate_routes()
        assert len(router.routes) == 15  # 3 models * 5 routes

    benchmark(generate_small)


@pytest.mark.benchmark(group="router-scaling")
def test_router_scaling_medium(
    benchmark: BenchmarkFixture,
    benchmark_models_path: str,
) -> None:
    """Benchmark router generation with 6 models.

    Performance target: < 200ms
    Tests linear scaling with increased model count.
    """
    parser = SchemaParser()
    schemas = parser.parse_file(benchmark_models_path)
    # Use 6 models
    subset_schemas = {
        "Contact": schemas["Contact"],
        "ComplexModel": schemas["ComplexModel"],
        "Author": schemas["Author"],
        "Book": schemas["Book"],
        "Review": schemas["Review"],
        "LargeModel": schemas["LargeModel"],
    }
    store = DataStore()

    def generate_medium() -> None:
        router_gen = RouterGenerator(schemas=subset_schemas, store=store)
        router = router_gen.generate_routes()
        assert len(router.routes) == 30  # 6 models * 5 routes

    benchmark(generate_medium)


# =============================================================================
# TESTS: Model Registry Operations
# =============================================================================


@pytest.mark.benchmark(group="router-registry")
def test_model_registry_lookup(
    benchmark: BenchmarkFixture,
    parsed_benchmark_schema: dict[str, ModelSchema],
) -> None:
    """Benchmark model registry lookup operations.

    Performance target: < 1ms (O(1) dictionary lookup)
    Tests hash map lookup performance.
    """
    store = DataStore()
    router_gen = RouterGenerator(schemas=parsed_benchmark_schema, store=store)
    registry = router_gen.registry

    def lookup_models() -> None:
        # O(1) lookups for each model type
        response = registry.get_response_model("Contact")
        input_model = registry.get_input_model("Contact")
        list_response = registry.get_list_response_model("Contact")
        assert response is not None
        assert input_model is not None
        assert list_response is not None

    benchmark(lookup_models)
