"""Benchmark tests for DataGenerator performance.

Tests generator performance across various scenarios:
- Different batch sizes (10, 100, 1000)
- Different field types and complexities
- Foreign key resolution and caching
- Reproducible seeded generation
- Dependency ordering for FK models

Performance targets:
- 10 instances: < 50ms
- 100 instances: < 200ms
- 1000 instances: < 2s
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from pathlib import Path

# Third-party
import pytest
from mock_api.core.generator import DataGenerator
from pytest_benchmark.fixture import BenchmarkFixture

# =============================================================================
# TESTS: Generator Scaling
# =============================================================================


@pytest.mark.benchmark(group="generator-scale")
def test_generator_small_batch(
    benchmark: BenchmarkFixture,
    generator: DataGenerator,
) -> None:
    """Benchmark generating 10 Contact instances.

    Performance target: < 50ms
    Baseline for simple 4-field model.
    """

    def generate() -> None:
        generator.generate("Contact", count=10)

    benchmark(generate)


@pytest.mark.benchmark(group="generator-scale")
def test_generator_medium_batch(
    benchmark: BenchmarkFixture,
    generator: DataGenerator,
) -> None:
    """Benchmark generating 100 Contact instances.

    Performance target: < 200ms
    Tests linear scaling with count.

    Args:
        benchmark: Benchmark fixture.
        generator: DataGenerator instance.
        parsed_benchmark_schema: Parsed model schemas.
    """

    def generate() -> None:
        generator.generate("Contact", count=100)

    benchmark(generate)


@pytest.mark.benchmark(group="generator-scale")
def test_generator_large_batch(
    benchmark: BenchmarkFixture,
    generator: DataGenerator,
) -> None:
    """Benchmark generating 1000 Contact instances.

    Performance target: < 2s
    Tests Faker and deepcopy overhead at scale.
    """

    def generate() -> None:
        generator.generate("Contact", count=1000)

    benchmark(generate)


# =============================================================================
# TESTS: Generator Field Types
# =============================================================================


@pytest.mark.benchmark(group="generator-field-types")
def test_generator_simple_fields(
    benchmark: BenchmarkFixture,
    generator: DataGenerator,
) -> None:
    """Benchmark generating Contact (str, int fields).

    Performance target: < 30ms for 10 instances
    """

    def generate() -> None:
        generator.generate("Contact", count=10)

    benchmark(generate)


@pytest.mark.benchmark(group="generator-field-types")
def test_generator_complex_fields(
    benchmark: BenchmarkFixture,
    generator: DataGenerator,
) -> None:
    """Benchmark generating ComplexModel (enums, datetime, optional fields).

    Performance target: < 80ms for 10 instances
    Tests overhead of complex field types.
    """

    def generate() -> None:
        generator.generate("ComplexModel", count=10)

    benchmark(generate)


@pytest.mark.benchmark(group="generator-field-types")
def test_generator_large_field_count(
    benchmark: BenchmarkFixture,
    generator: DataGenerator,
) -> None:
    """Benchmark generating LargeModel (20 fields).

    Performance target: < 150ms for 10 instances
    Tests O(fields) scaling.
    """

    def generate() -> None:
        generator.generate("LargeModel", count=10)

    benchmark(generate)


# =============================================================================
# TESTS: Generator Foreign Key Resolution
# =============================================================================


@pytest.mark.benchmark(group="generator-fk")
def test_generator_foreign_key_simple(
    benchmark: BenchmarkFixture,
    generator: DataGenerator,
) -> None:
    """Benchmark generating Book (1 FK to Author).

    Performance target: < 60ms for 10 instances
    Tests FK resolution overhead.
    """
    # First generate authors so FK references are valid
    generator.generate("Author", count=20)

    def generate() -> None:
        generator.generate("Book", count=10)

    benchmark(generate)


@pytest.mark.benchmark(group="generator-fk")
def test_generator_foreign_key_multiple(
    benchmark: BenchmarkFixture,
    generator: DataGenerator,
) -> None:
    """Benchmark generating Review (2 FKs: book_id, author_id).

    Performance target: < 80ms for 10 instances
    Tests multi-FK overhead.
    """
    # Generate related data so FK references are valid
    generator.generate("Author", count=20)
    generator.generate("Book", count=50)

    def generate() -> None:
        generator.generate("Review", count=10)

    benchmark(generate)


# =============================================================================
# TESTS: Generator Reproducibility
# =============================================================================


@pytest.mark.benchmark(group="generator-reproducibility")
def test_generator_seeded_generation(
    benchmark: BenchmarkFixture,
    seeded_generator: DataGenerator,
) -> None:
    """Benchmark seeded generation for reproducibility.

    Performance target: < 60ms for 10 instances
    Should be comparable to non-seeded generation.
    """

    def generate() -> None:
        seeded_generator.generate("Contact", count=10)

    benchmark(generate)


# =============================================================================
# TESTS: Generator Dependency Ordering
# =============================================================================


@pytest.mark.benchmark(group="generator-dependency")
def test_generator_dependency_ordering(
    benchmark: BenchmarkFixture,
    generator: DataGenerator,
    benchmark_models_path: Path,
) -> None:
    """Benchmark generation with dependency ordering (Author -> Book -> Review).

    Performance target: < 300ms for 10 of each model
    Tests topological sort and cascading generation.
    """

    def generate_all() -> None:
        generator.generate("Author", count=10)
        generator.generate("Book", count=10)
        generator.generate("Review", count=10)

    benchmark(generate_all)


# =============================================================================
# TESTS: Generator Mixed Models
# =============================================================================


@pytest.mark.benchmark(group="generator-batch-mixed")
def test_generator_mixed_models_batch(
    benchmark: BenchmarkFixture,
    generator: DataGenerator,
) -> None:
    """Benchmark generating batches of different model types.

    Performance target: < 400ms
    Tests generator reuse across different models.
    """

    def generate_mixed() -> None:
        generator.generate("Contact", count=50)
        generator.generate("ComplexModel", count=50)
        generator.generate("Author", count=50)

    benchmark(generate_mixed)


# =============================================================================
# TESTS: Generator Optional Fields
# =============================================================================


@pytest.mark.benchmark(group="generator-optional-fields")
def test_generator_optional_fields(
    benchmark: BenchmarkFixture,
    generator: DataGenerator,
) -> None:
    """Benchmark generating models with optional fields (Author with bio).

    Performance target: < 70ms for 10 instances
    Tests 20% null probability logic overhead.
    """

    def generate() -> None:
        generator.generate("Author", count=10)

    benchmark(generate)
