"""Benchmark tests for DataStore performance.

Tests store performance across various scenarios:
- CRUD operations (Create, Read, Update, Delete)
- Pagination and filtering
- Bulk operations
- Count operations

Performance targets:
- Read (O(1)): < 1ms
- Create: < 5ms
- List (page_size=20): < 10ms
- Filtered list: < 50ms
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
import contextlib
from typing import Any

# Third-party
import pytest

# Project/Local
from mock_api.core.store import DataStore
from pytest_benchmark.fixture import BenchmarkFixture

# =============================================================================
# TESTS: Store CRUD Operations
# =============================================================================


@pytest.mark.benchmark(group="store-crud")
def test_store_create(
    benchmark: BenchmarkFixture,
    empty_store: DataStore,
) -> None:
    """Benchmark single create operation with auto-ID.

    Performance target: < 5ms
    Tests deepcopy overhead.
    """
    data = {"name": "Test Contact", "email": "test@example.com", "phone": "+1-555-9999"}

    def create() -> None:
        empty_store.create("Contact", data, auto_id=True)

    benchmark(create)


@pytest.mark.benchmark(group="store-crud")
def test_store_read(
    benchmark: BenchmarkFixture,
    small_populated_store: DataStore,
) -> None:
    """Benchmark O(1) lookup by ID.

    Performance target: < 1ms
    Tests hash map lookup performance.
    """

    def read() -> None:
        result = small_populated_store.read("Contact", 5)
        assert result is not None

    benchmark(read)


@pytest.mark.benchmark(group="store-crud")
def test_store_update(
    benchmark: BenchmarkFixture,
    small_populated_store: DataStore,
) -> None:
    """Benchmark direct update operation.

    Performance target: < 5ms
    Tests deepcopy overhead on update.
    """
    update_data = {"name": "Updated Name", "email": "updated@example.com"}

    def update() -> None:
        small_populated_store.update("Contact", 5, update_data)

    benchmark(update)


@pytest.mark.benchmark(group="store-crud")
def test_store_delete(
    benchmark: BenchmarkFixture,
    small_populated_store: DataStore,
) -> None:
    """Benchmark delete operation.

    Performance target: < 2ms
    Tests OrderedDict.pop() performance.
    """

    def delete() -> None:
        small_populated_store.delete("Contact", 5)

    benchmark(delete)


# =============================================================================
# TESTS: Store List Operations
# =============================================================================


@pytest.mark.benchmark(group="store-list")
def test_store_list_simple(
    benchmark: BenchmarkFixture,
    medium_populated_store: DataStore,
) -> None:
    """Benchmark pagination without filtering.

    Performance target: < 10ms
    Tests slicing performance.
    """

    def list_simple() -> None:
        result = medium_populated_store.list("Contact", page=1, page_size=20)
        assert len(result.items) == 20

    benchmark(list_simple)


@pytest.mark.benchmark(group="store-list")
def test_store_list_filtered(
    benchmark: BenchmarkFixture,
    medium_populated_store: DataStore,
) -> None:
    """Benchmark filtered list operation.

    Performance target: < 50ms
    Tests O(n) full scan with filter function.
    """

    def filter_func(item: dict[str, Any]) -> bool:
        return item.get("name") == "Person 50"

    def list_filtered() -> None:
        result = medium_populated_store.list(
            "Contact", page=1, page_size=20, filter_func=filter_func
        )
        assert len(result.items) <= 20

    benchmark(list_filtered)


@pytest.mark.benchmark(group="store-list")
def test_store_list_large_page(
    benchmark: BenchmarkFixture,
    large_populated_store: DataStore,
) -> None:
    """Benchmark pagination with large page size.

    Performance target: < 30ms
    Tests slicing with max page size.
    """

    def list_large() -> None:
        result = large_populated_store.list("Contact", page=1, page_size=100)
        assert len(result.items) == 100

    benchmark(list_large)


# =============================================================================
# TESTS: Store Count Operations
# =============================================================================


@pytest.mark.benchmark(group="store-count")
def test_store_count_simple(
    benchmark: BenchmarkFixture,
    medium_populated_store: DataStore,
) -> None:
    """Benchmark simple count operation.

    Performance target: < 5ms
    Tests len() call performance.
    """

    def count() -> None:
        result = medium_populated_store.count("Contact")
        assert result == 100

    benchmark(count)


@pytest.mark.benchmark(group="store-count")
def test_store_count_filtered(
    benchmark: BenchmarkFixture,
    medium_populated_store: DataStore,
) -> None:
    """Benchmark filtered count operation.

    Performance target: < 50ms
    Tests O(n) scan for counting with filters.
    """

    def filter_func(item: dict[str, Any]) -> bool:
        return item.get("name") == "Person 50"

    def count_filtered() -> None:
        result = medium_populated_store.count("Contact", filter_func=filter_func)
        assert result >= 0

    benchmark(count_filtered)


# =============================================================================
# TESTS: Store Bulk Operations
# =============================================================================


@pytest.mark.benchmark(group="store-bulk")
def test_store_bulk_load_small(
    benchmark: BenchmarkFixture,
    empty_store: DataStore,
) -> None:
    """Benchmark loading 100 items at once.

    Performance target: < 50ms
    Tests bulk initialization performance.
    """
    data = {
        "Contact": [
            {
                "id": i,
                "name": f"Person {i}",
                "email": f"person{i}@example.com",
                "phone": f"+1-555-{i:04d}",
            }
            for i in range(1, 101)
        ]
    }

    def bulk_load() -> None:
        empty_store.load(data)

    benchmark(bulk_load)


@pytest.mark.benchmark(group="store-bulk")
def test_store_bulk_load_medium(
    benchmark: BenchmarkFixture,
    empty_store: DataStore,
) -> None:
    """Benchmark loading 500 items at once.

    Performance target: < 250ms
    Tests bulk initialization scaling.
    """
    data = {
        "Contact": [
            {
                "id": i,
                "name": f"Person {i}",
                "email": f"person{i}@example.com",
                "phone": f"+1-555-{i:04d}",
            }
            for i in range(1, 501)
        ]
    }

    def bulk_load() -> None:
        empty_store.load(data)

    benchmark(bulk_load)


@pytest.mark.benchmark(group="store-bulk")
def test_store_bulk_load_large(
    benchmark: BenchmarkFixture,
    empty_store: DataStore,
) -> None:
    """Benchmark loading 1000 items at once.

    Performance target: < 500ms
    Tests bulk initialization at scale.
    """
    data = {
        "Contact": [
            {
                "id": i,
                "name": f"Person {i}",
                "email": f"person{i}@example.com",
                "phone": f"+1-555-{i:04d}",
            }
            for i in range(1, 1001)
        ]
    }

    def bulk_load() -> None:
        empty_store.load(data)

    benchmark(bulk_load)


@pytest.mark.benchmark(group="store-bulk")
def test_store_bulk_create_sequential(
    benchmark: BenchmarkFixture,
    empty_store: DataStore,
) -> None:
    """Benchmark 100 sequential create operations.

    Performance target: < 500ms
    Tests sequential create overhead with deepcopy.
    """
    batch_data = [
        {
            "name": f"Batch Contact {i}",
            "email": f"batch{i}@example.com",
            "phone": f"+1-555-{i:04d}",
        }
        for i in range(100)
    ]

    def bulk_create() -> None:
        for contact in batch_data:
            empty_store.create("Contact", contact, auto_id=True)

    benchmark(bulk_create)


# =============================================================================
# TESTS: Store Edge Cases
# =============================================================================


@pytest.mark.benchmark(group="store-edge")
def test_store_read_missing(
    benchmark: BenchmarkFixture,
    small_populated_store: DataStore,
) -> None:
    """Benchmark read for non-existent ID.

    Performance target: < 1ms
    Tests exception handling overhead.
    """

    def read_missing() -> None:
        with contextlib.suppress(Exception):
            small_populated_store.read("Contact", 99999)

    benchmark(read_missing)


@pytest.mark.benchmark(group="store-edge")
def test_store_list_empty_result(
    benchmark: BenchmarkFixture,
    medium_populated_store: DataStore,
) -> None:
    """Benchmark list with filters that match nothing.

    Performance target: < 50ms
    Tests O(n) scan with no matches.
    """

    def filter_func(item: dict[str, Any]) -> bool:
        return item.get("name") == "NonExistentPerson"

    def list_empty() -> None:
        result = medium_populated_store.list(
            "Contact", page=1, page_size=20, filter_func=filter_func
        )
        assert len(result.items) == 0

    benchmark(list_empty)
