"""Benchmark tests for SchemaParser performance.

Tests parser performance across various scenarios:
- Simple vs complex models
- Multiple model parsing
- Field extraction at different scales
- Foreign key relationship detection
- Enum handling
- Circular dependency detection

Performance targets:
- Simple model (5 fields): < 10ms
- Complex model (20 fields, 5 FKs): < 50ms
- Large file (20 models): < 200ms
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
# Third-party
import pytest

# Project/Local
from mock_api.core.parser import SchemaParser
from pytest_benchmark.fixture import BenchmarkFixture

# =============================================================================
# TESTS: Parser Basic Operations
# =============================================================================


@pytest.mark.benchmark(group="parser-basic")
def test_parser_simple_model(
    benchmark: BenchmarkFixture,
    benchmark_models_path: str,
) -> None:
    """Benchmark parsing a simple 4-field model (Contact).

    Performance target: < 10ms
    """
    parser = SchemaParser()

    def parse() -> None:
        parser.parse_file(benchmark_models_path)

    benchmark(parse)


@pytest.mark.benchmark(group="parser-basic")
def test_parser_simple_model_cached(
    benchmark: BenchmarkFixture,
    benchmark_models_path: str,
) -> None:
    """Benchmark parsing with warm caches (2nd parse of same file).

    Performance target: Should be faster than cold parse
    """
    parser = SchemaParser()
    # Warm up the cache
    parser.parse_file(benchmark_models_path)

    def parse() -> None:
        parser.parse_file(benchmark_models_path)

    benchmark(parse)


# =============================================================================
# TESTS: Parser Field Extraction
# =============================================================================


@pytest.mark.benchmark(group="parser-field-extraction")
def test_parser_field_extraction_contact(
    benchmark: BenchmarkFixture,
    parser: SchemaParser,
    benchmark_models_path: str,
) -> None:
    """Benchmark field extraction from Contact model (4 fields).

    Performance target: < 5ms
    """
    schemas = parser.parse_file(benchmark_models_path)
    contact_model = schemas["Contact"]

    def extract_fields() -> None:
        assert contact_model.pydantic_model is not None
        _ = contact_model.pydantic_model.model_fields

    benchmark(extract_fields)


@pytest.mark.benchmark(group="parser-field-extraction")
def test_parser_field_extraction_complex(
    benchmark: BenchmarkFixture,
    parser: SchemaParser,
    benchmark_models_path: str,
) -> None:
    """Benchmark field extraction from ComplexModel (9 fields with enums).

    Performance target: < 10ms
    """
    schemas = parser.parse_file(benchmark_models_path)
    complex_model = schemas["ComplexModel"]

    def extract_fields() -> None:
        assert complex_model.pydantic_model is not None
        _ = complex_model.pydantic_model.model_fields

    benchmark(extract_fields)


@pytest.mark.benchmark(group="parser-field-extraction")
def test_parser_field_extraction_large(
    benchmark: BenchmarkFixture,
    parser: SchemaParser,
    benchmark_models_path: str,
) -> None:
    """Benchmark field extraction from LargeModel (20 fields).

    Performance target: < 15ms
    """
    schemas = parser.parse_file(benchmark_models_path)
    large_model = schemas["LargeModel"]

    def extract_fields() -> None:
        assert large_model.pydantic_model is not None
        _ = large_model.pydantic_model.model_fields

    benchmark(extract_fields)


# =============================================================================
# TESTS: Parser Relationship Detection
# =============================================================================


@pytest.mark.benchmark(group="parser-relationships")
def test_parser_relationship_detection_simple(
    benchmark: BenchmarkFixture,
    benchmark_models_path: str,
) -> None:
    """Benchmark FK relationship detection for simple models (Author, Book).

    Performance target: < 30ms
    Tests the 4-pass relationship detection algorithm.
    """
    parser = SchemaParser()

    def parse_with_fks() -> None:
        schemas = parser.parse_file(benchmark_models_path)
        # Verify FK was detected
        assert "Book" in schemas
        assert schemas["Book"].pydantic_model is not None
        book_fields = schemas["Book"].pydantic_model.model_fields
        assert "author_id" in book_fields

    benchmark(parse_with_fks)


@pytest.mark.benchmark(group="parser-relationships")
def test_parser_relationship_detection_complex(
    benchmark: BenchmarkFixture,
    benchmark_models_path: str,
) -> None:
    """Benchmark FK detection for multi-FK model (Review with 2 FKs).

    Performance target: < 40ms
    Tests O(n*m) complexity of relationship detection.
    """
    parser = SchemaParser()

    def parse_multi_fk() -> None:
        schemas = parser.parse_file(benchmark_models_path)
        # Review has 2 FKs: book_id and author_id
        assert "Review" in schemas
        assert schemas["Review"].pydantic_model is not None
        review_fields = schemas["Review"].pydantic_model.model_fields
        assert "book_id" in review_fields
        assert "author_id" in review_fields

    benchmark(parse_multi_fk)


@pytest.mark.benchmark(group="parser-relationships")
def test_parser_circular_dependency_detection(
    benchmark: BenchmarkFixture,
    benchmark_models_path: str,
) -> None:
    """Benchmark circular dependency handling (Category with self-referential FK).

    Performance target: < 50ms
    Tests cycle detection in relationship graph.
    """
    parser = SchemaParser()

    def parse_circular() -> None:
        schemas = parser.parse_file(benchmark_models_path)
        # Category has parent_id which is self-referential
        assert "Category" in schemas
        assert schemas["Category"].pydantic_model is not None
        category_fields = schemas["Category"].pydantic_model.model_fields
        assert "parent_id" in category_fields

    benchmark(parse_circular)


# =============================================================================
# TESTS: Parser Enum Handling
# =============================================================================


@pytest.mark.benchmark(group="parser-enum")
def test_parser_enum_handling(
    benchmark: BenchmarkFixture,
    parser: SchemaParser,
    benchmark_models_path: str,
) -> None:
    """Benchmark enum field detection and validation.

    Performance target: < 20ms
    """
    schemas = parser.parse_file(benchmark_models_path)
    complex_model = schemas["ComplexModel"]

    def check_enums() -> None:
        assert complex_model.pydantic_model is not None
        fields = complex_model.pydantic_model.model_fields
        # ComplexModel has Status and Priority enums
        assert "status" in fields
        assert "priority" in fields

    benchmark(check_enums)


# =============================================================================
# TESTS: Parser Scaling
# =============================================================================


@pytest.mark.benchmark(group="parser-scale")
def test_parser_all_models(
    benchmark: BenchmarkFixture,
    benchmark_models_path: str,
) -> None:
    """Benchmark parsing all models in benchmark_models.py (10 models).

    Performance target: < 100ms
    Tests parser scaling with multiple models.
    """
    parser = SchemaParser()

    def parse_all() -> None:
        schemas = parser.parse_file(benchmark_models_path)
        # Verify all expected models are present
        expected_models = {
            "Contact",
            "ComplexModel",
            "Author",
            "Book",
            "Review",
            "LargeModel",
            "Category",
            "Product",
        }
        assert expected_models.issubset(set(schemas.keys()))

    benchmark(parse_all)
