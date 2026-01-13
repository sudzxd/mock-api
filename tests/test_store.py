"""Tests for data store."""

from __future__ import annotations

# ============================================================================
# IMPORTS
# ============================================================================
# Standard library
import threading

# Third-party
import pytest

# Project/Local
from mock_api.core.constants import (
    DEFAULT_PAGE_NUMBER,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    PRIMARY_KEY_FIELD,
    FilterOperator,
    SortDirection,
)
from mock_api.core.exceptions import (
    DuplicateInstanceError,
    InstanceNotFoundError,
    StoreError,
)
from mock_api.core.store import DataStore
from mock_api.core.types import FilterSpec, PaginationInfo, QueryResult, SortSpec

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def store() -> DataStore:
    """Create a fresh data store instance."""
    return DataStore()


@pytest.fixture
def sample_users() -> list[dict[str, str | int]]:
    """Sample user data for testing."""
    return [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"},
        {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
    ]


@pytest.fixture
def loaded_store(
    store: DataStore, sample_users: list[dict[str, str | int]]
) -> DataStore:
    """Store pre-loaded with sample data."""
    store.load({"User": sample_users})
    return store


# =============================================================================
# TESTS: Initialization
# =============================================================================


def test_store_initialization() -> None:
    """Test store initializes empty."""
    store = DataStore()
    assert store.get_models() == []


def test_store_load_data(
    store: DataStore, sample_users: list[dict[str, str | int]]
) -> None:
    """Test loading bulk data into store."""
    store.load({"User": sample_users})

    assert "User" in store.get_models()
    assert store.count("User") == 3


def test_store_load_multiple_models(store: DataStore) -> None:
    """Test loading multiple models at once."""
    data = {
        "User": [{"id": 1, "name": "Alice"}],
        "Post": [{"id": 1, "title": "First Post"}],
    }

    store.load(data)

    assert len(store.get_models()) == 2
    assert "User" in store.get_models()
    assert "Post" in store.get_models()


def test_store_load_updates_id_counter(store: DataStore) -> None:
    """Test that load() updates ID counter based on max ID."""
    store.load({"User": [{"id": 5, "name": "Alice"}]})

    # Next created item should have ID > 5
    new_user = store.create("User", {"name": "Bob"})
    assert new_user["id"] == 6


# =============================================================================
# TESTS: Create Operation
# =============================================================================


def test_create_with_auto_id(store: DataStore) -> None:
    """Test creating instance with auto-assigned ID."""
    user = store.create("User", {"name": "Alice"})

    assert PRIMARY_KEY_FIELD in user
    assert user["id"] == 1
    assert user["name"] == "Alice"


def test_create_with_manual_id(store: DataStore) -> None:
    """Test creating instance with manually specified ID."""
    user = store.create("User", {"id": 42, "name": "Alice"}, auto_id=False)

    assert user["id"] == 42


def test_create_increments_id_counter(store: DataStore) -> None:
    """Test that create increments ID counter."""
    user1 = store.create("User", {"name": "Alice"})
    user2 = store.create("User", {"name": "Bob"})

    assert user1["id"] == 1
    assert user2["id"] == 2


def test_create_duplicate_id_raises_error(store: DataStore) -> None:
    """Test that creating duplicate ID raises error."""
    store.create("User", {"id": 1, "name": "Alice"})

    with pytest.raises(DuplicateInstanceError, match="already exists"):
        store.create("User", {"id": 1, "name": "Bob"})


def test_create_new_model_initializes_storage(store: DataStore) -> None:
    """Test creating instance for new model initializes storage."""
    assert "User" not in store.get_models()

    store.create("User", {"name": "Alice"})

    assert "User" in store.get_models()


def test_create_returns_copy(store: DataStore) -> None:
    """Test that create returns a copy, not reference."""
    original = {"name": "Alice"}
    created = store.create("User", original)

    created["name"] = "Modified"

    assert original["name"] == "Alice"


# =============================================================================
# TESTS: Read Operation
# =============================================================================


def test_read_existing_instance(loaded_store: DataStore) -> None:
    """Test reading an existing instance."""
    user = loaded_store.read("User", 1)

    assert user is not None
    assert user["id"] == 1
    assert user["name"] == "Alice"


def test_read_nonexistent_instance(loaded_store: DataStore) -> None:
    """Test reading non-existent instance returns None."""
    user = loaded_store.read("User", 999)

    assert user is None


def test_read_nonexistent_model(loaded_store: DataStore) -> None:
    """Test reading from non-existent model returns None."""
    instance = loaded_store.read("NonExistent", 1)

    assert instance is None


def test_read_returns_copy(loaded_store: DataStore) -> None:
    """Test that read returns a copy, not reference."""
    user1 = loaded_store.read("User", 1)
    assert user1 is not None
    user1["name"] = "Modified"

    user2 = loaded_store.read("User", 1)
    assert user2 is not None
    assert user2["name"] == "Alice"


# =============================================================================
# TESTS: Update Operation
# =============================================================================


def test_update_existing_instance(loaded_store: DataStore) -> None:
    """Test updating an existing instance."""
    updated = loaded_store.update("User", 1, {"name": "Alice Smith"})

    assert updated["id"] == 1
    assert updated["name"] == "Alice Smith"

    # Verify persistence
    user = loaded_store.read("User", 1)
    assert user is not None
    assert user["name"] == "Alice Smith"


def test_update_preserves_id(loaded_store: DataStore) -> None:
    """Test that update preserves ID even if data contains different ID."""
    updated = loaded_store.update("User", 1, {"id": 999, "name": "Modified"})

    assert updated["id"] == 1


def test_update_nonexistent_instance_raises_error(loaded_store: DataStore) -> None:
    """Test updating non-existent instance raises error."""
    with pytest.raises(InstanceNotFoundError, match="not found"):
        loaded_store.update("User", 999, {"name": "Ghost"})


def test_update_nonexistent_model_raises_error(loaded_store: DataStore) -> None:
    """Test updating non-existent model raises error."""
    with pytest.raises(InstanceNotFoundError, match="not found"):
        loaded_store.update("NonExistent", 1, {"name": "Ghost"})


def test_update_partial_fields(loaded_store: DataStore) -> None:
    """Test updating only some fields."""
    original = loaded_store.read("User", 1)
    assert original is not None
    original_email = original["email"]

    loaded_store.update("User", 1, {"name": "Alice Smith"})

    updated = loaded_store.read("User", 1)
    assert updated is not None
    assert updated["name"] == "Alice Smith"
    assert updated["email"] == original_email


# =============================================================================
# TESTS: Delete Operation
# =============================================================================


def test_delete_existing_instance(loaded_store: DataStore) -> None:
    """Test deleting an existing instance."""
    result = loaded_store.delete("User", 1)

    assert result is True
    assert loaded_store.read("User", 1) is None
    assert loaded_store.count("User") == 2


def test_delete_nonexistent_instance(loaded_store: DataStore) -> None:
    """Test deleting non-existent instance returns False."""
    result = loaded_store.delete("User", 999)

    assert result is False


def test_delete_nonexistent_model(loaded_store: DataStore) -> None:
    """Test deleting from non-existent model returns False."""
    result = loaded_store.delete("NonExistent", 1)

    assert result is False


def test_delete_does_not_affect_other_instances(loaded_store: DataStore) -> None:
    """Test that delete only removes target instance."""
    loaded_store.delete("User", 2)

    assert loaded_store.read("User", 1) is not None
    assert loaded_store.read("User", 3) is not None


# =============================================================================
# TESTS: List Operation
# =============================================================================


def test_list_all_instances(loaded_store: DataStore) -> None:
    """Test listing all instances without pagination."""
    result = loaded_store.list("User", page=1, page_size=10)

    assert isinstance(result, QueryResult)
    assert len(result.items) == 3
    assert result.pagination.total_items == 3


def test_list_with_pagination(store: DataStore) -> None:
    """Test listing with pagination."""
    # Create 25 users
    for i in range(1, 26):
        store.create("User", {"name": f"User {i}"})

    # Get first page
    result = store.list("User", page=1, page_size=10)

    assert len(result.items) == 10
    assert result.pagination.page == 1
    assert result.pagination.page_size == 10
    assert result.pagination.total_items == 25
    assert result.pagination.total_pages == 3


def test_list_second_page(store: DataStore) -> None:
    """Test listing second page."""
    for i in range(1, 26):
        store.create("User", {"name": f"User {i}"})

    result = store.list("User", page=2, page_size=10)

    assert len(result.items) == 10
    assert result.items[0]["id"] == 11


def test_list_last_page_partial(store: DataStore) -> None:
    """Test listing last page with partial results."""
    for i in range(1, 26):
        store.create("User", {"name": f"User {i}"})

    result = store.list("User", page=3, page_size=10)

    assert len(result.items) == 5


def test_list_page_beyond_total(store: DataStore) -> None:
    """Test listing page beyond total pages returns empty."""
    store.load({"User": [{"id": 1, "name": "Alice"}]})

    result = store.list("User", page=10, page_size=10)

    assert len(result.items) == 0


def test_list_with_filter(loaded_store: DataStore) -> None:
    """Test listing with filter function."""
    result = loaded_store.list(
        "User", page=1, page_size=10, filter_func=lambda u: u["name"].startswith("A")
    )

    assert len(result.items) == 1
    assert result.items[0]["name"] == "Alice"


def test_list_filter_affects_pagination(store: DataStore) -> None:
    """Test that filter affects pagination counts."""
    for i in range(1, 11):
        store.create("User", {"name": f"User {i}", "active": i % 2 == 0})

    result = store.list("User", page=1, page_size=10, filter_func=lambda u: u["active"])

    assert result.pagination.total_items == 5


def test_list_empty_model(store: DataStore) -> None:
    """Test listing empty model returns empty result."""
    result = store.list("User", page=1, page_size=10)

    assert len(result.items) == 0
    assert result.pagination.total_items == 0
    assert result.pagination.total_pages == 1


def test_list_invalid_page_raises_error(loaded_store: DataStore) -> None:
    """Test that invalid page number raises error."""
    with pytest.raises(StoreError, match="Invalid page number"):
        loaded_store.list("User", page=0, page_size=10)

    with pytest.raises(StoreError, match="Invalid page number"):
        loaded_store.list("User", page=-1, page_size=10)


def test_list_invalid_page_size_raises_error(loaded_store: DataStore) -> None:
    """Test that invalid page size raises error."""
    with pytest.raises(StoreError, match="Invalid page size"):
        loaded_store.list("User", page=1, page_size=0)

    with pytest.raises(StoreError, match="Invalid page size"):
        loaded_store.list("User", page=1, page_size=MAX_PAGE_SIZE + 1)


def test_list_returns_copy(loaded_store: DataStore) -> None:
    """Test that list returns copies, not references."""
    result = loaded_store.list("User", page=1, page_size=10)
    result.items[0]["name"] = "Modified"

    user = loaded_store.read("User", 1)
    assert user is not None
    assert user["name"] == "Alice"


def test_list_uses_default_pagination(loaded_store: DataStore) -> None:
    """Test that list uses default pagination values."""
    result = loaded_store.list("User")

    assert result.pagination.page == DEFAULT_PAGE_NUMBER
    assert result.pagination.page_size == DEFAULT_PAGE_SIZE


# =============================================================================
# TESTS: Offset-Based Pagination
# =============================================================================


def test_list_offset_based_first_batch(loaded_store: DataStore) -> None:
    """Test offset-based pagination first batch."""
    result = loaded_store.list("User", offset=0, limit=2)

    assert len(result.items) == 2
    assert result.items[0]["id"] == 1
    assert result.items[1]["id"] == 2
    assert result.pagination.offset == 0
    assert result.pagination.limit == 2
    assert result.pagination.total_items == 3
    assert result.pagination.has_next is True
    assert result.pagination.has_prev is False


def test_list_offset_based_second_batch(loaded_store: DataStore) -> None:
    """Test offset-based pagination second batch."""
    result = loaded_store.list("User", offset=2, limit=2)

    assert len(result.items) == 1
    assert result.items[0]["id"] == 3
    assert result.pagination.has_next is False
    assert result.pagination.has_prev is True


def test_list_offset_beyond_total(loaded_store: DataStore) -> None:
    """Test offset-based pagination beyond total items."""
    result = loaded_store.list("User", offset=10, limit=5)

    assert len(result.items) == 0
    assert result.pagination.has_next is False
    assert result.pagination.has_prev is True


def test_list_offset_invalid_negative(loaded_store: DataStore) -> None:
    """Test list with invalid negative offset."""
    with pytest.raises(StoreError, match="Invalid offset"):
        loaded_store.list("User", offset=-1, limit=10)


def test_list_offset_invalid_limit(loaded_store: DataStore) -> None:
    """Test list with invalid limit."""
    with pytest.raises(StoreError, match="Invalid limit"):
        loaded_store.list("User", offset=0, limit=0)

    with pytest.raises(StoreError, match="Invalid limit"):
        loaded_store.list("User", offset=0, limit=200)


def test_list_conflicting_pagination_params(loaded_store: DataStore) -> None:
    """Test list with conflicting pagination parameters."""
    with pytest.raises(StoreError, match="Cannot use both"):
        loaded_store.list("User", page=1, offset=0)


def test_list_offset_with_filter(store: DataStore) -> None:
    """Test offset-based pagination with filter."""
    for i in range(1, 11):
        store.create("User", {"name": f"User {i}", "active": i % 2 == 0})

    result = store.list("User", offset=0, limit=3, filter_func=lambda u: u["active"])

    assert len(result.items) == 3
    assert result.pagination.total_items == 5
    assert all(u["active"] for u in result.items)


def test_list_page_based_still_works(loaded_store: DataStore) -> None:
    """Test that existing page-based pagination still works."""
    result = loaded_store.list("User", page=1, page_size=2)

    assert len(result.items) == 2
    assert result.pagination.page == 1
    assert result.pagination.page_size == 2
    assert result.pagination.total_pages == 2
    assert result.pagination.has_next is True
    assert result.pagination.has_prev is False


# =============================================================================
# TESTS: Count Operation
# =============================================================================


def test_count_all_instances(loaded_store: DataStore) -> None:
    """Test counting all instances."""
    count = loaded_store.count("User")

    assert count == 3


def test_count_with_filter(loaded_store: DataStore) -> None:
    """Test counting with filter."""
    count = loaded_store.count("User", filter_func=lambda u: u["name"].startswith("A"))

    assert count == 1


def test_count_empty_model(store: DataStore) -> None:
    """Test counting empty model returns 0."""
    count = store.count("User")

    assert count == 0


def test_count_nonexistent_model(store: DataStore) -> None:
    """Test counting non-existent model returns 0."""
    count = store.count("NonExistent")

    assert count == 0


# =============================================================================
# TESTS: Clear Operation
# =============================================================================


def test_clear_specific_model(loaded_store: DataStore) -> None:
    """Test clearing specific model."""
    loaded_store.load({"Post": [{"id": 1, "title": "Test"}]})

    loaded_store.clear("User")

    assert loaded_store.count("User") == 0
    assert loaded_store.count("Post") == 1


def test_clear_all_models(loaded_store: DataStore) -> None:
    """Test clearing all models."""
    loaded_store.load({"Post": [{"id": 1, "title": "Test"}]})

    loaded_store.clear()

    assert loaded_store.count("User") == 0
    assert loaded_store.count("Post") == 0
    assert loaded_store.get_models() == []


def test_clear_resets_id_counter(store: DataStore) -> None:
    """Test that clear resets ID counter."""
    store.create("User", {"name": "Alice"})
    store.clear("User")

    new_user = store.create("User", {"name": "Bob"})

    assert new_user["id"] == 1


# =============================================================================
# TESTS: Get Models Operation
# =============================================================================


def test_get_models_empty_store(store: DataStore) -> None:
    """Test get_models on empty store."""
    models = store.get_models()

    assert models == []


def test_get_models_returns_list(loaded_store: DataStore) -> None:
    """Test get_models returns list of model names."""
    models = loaded_store.get_models()

    assert isinstance(models, list)
    assert "User" in models


def test_get_models_multiple(store: DataStore) -> None:
    """Test get_models with multiple models."""
    store.load({"User": [], "Post": [], "Comment": []})

    models = store.get_models()

    assert len(models) == 3
    assert "User" in models
    assert "Post" in models
    assert "Comment" in models


# =============================================================================
# TESTS: Thread Safety
# =============================================================================


def test_thread_safe_concurrent_creates(store: DataStore) -> None:
    """Test thread safety with concurrent creates."""

    def create_users(start: int, count: int) -> None:
        for i in range(start, start + count):
            store.create("User", {"name": f"User {i}"})

    # Create 100 users across 10 threads
    threads: list[threading.Thread] = []
    for i in range(10):
        thread = threading.Thread(target=create_users, args=(i * 10, 10))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Should have 100 users with unique IDs
    assert store.count("User") == 100

    # Check all IDs are unique
    result = store.list("User", page=1, page_size=100)
    ids = [user["id"] for user in result.items]
    assert len(ids) == len(set(ids))


# =============================================================================
# TESTS: Edge Cases
# =============================================================================


def test_create_with_none_values(store: DataStore) -> None:
    """Test creating instance with None values."""
    user = store.create("User", {"name": None, "email": None})

    assert user["name"] is None
    assert user["email"] is None


def test_update_with_empty_dict(loaded_store: DataStore) -> None:
    """Test updating with empty dict."""
    original = loaded_store.read("User", 1)
    assert original is not None

    updated = loaded_store.update("User", 1, {})

    assert updated == original


def test_filter_returns_empty_list(loaded_store: DataStore) -> None:
    """Test filter that matches nothing."""
    result = loaded_store.list(
        "User", page=1, page_size=10, filter_func=lambda u: False
    )

    assert len(result.items) == 0
    assert result.pagination.total_items == 0


def test_pagination_info_correct_for_exact_pages(store: DataStore) -> None:
    """Test pagination info when items divide evenly into pages."""
    for i in range(1, 21):
        store.create("User", {"name": f"User {i}"})

    result = store.list("User", page=1, page_size=10)

    assert result.pagination.total_pages == 2


def test_pagination_info_dataclass(loaded_store: DataStore) -> None:
    """Test that PaginationInfo is a proper dataclass."""
    result = loaded_store.list("User", page=1, page_size=10)

    assert isinstance(result.pagination, PaginationInfo)
    assert hasattr(result.pagination, "page")
    assert hasattr(result.pagination, "page_size")
    assert hasattr(result.pagination, "total_items")
    assert hasattr(result.pagination, "total_pages")


def test_query_result_dataclass(loaded_store: DataStore) -> None:
    """Test that QueryResult is a proper dataclass."""
    result = loaded_store.list("User", page=1, page_size=10)

    assert isinstance(result, QueryResult)
    assert hasattr(result, "items")
    assert hasattr(result, "pagination")


# =============================================================================
# TESTS: Filtering
# =============================================================================


@pytest.fixture
def users_for_filtering() -> list[dict[str, str | int | None]]:
    """Sample users with varied data for filter testing."""
    return [
        {
            "id": 1,
            "name": "Alice",
            "age": 25,
            "email": "alice@example.com",
            "city": "NYC",
        },
        {"id": 2, "name": "Bob", "age": 30, "email": "bob@test.com", "city": "LA"},
        {
            "id": 3,
            "name": "Charlie",
            "age": 35,
            "email": "charlie@example.com",
            "city": "NYC",
        },
        {"id": 4, "name": "Diana", "age": 28, "email": "diana@test.com", "city": "SF"},
        {"id": 5, "name": "Eve", "age": 22, "email": "eve@example.com", "city": "NYC"},
        {"id": 6, "name": "Frank", "age": 40, "email": None, "city": "LA"},
    ]


@pytest.fixture
def store_with_users(
    store: DataStore, users_for_filtering: list[dict[str, str | int | None]]
) -> DataStore:
    """Store loaded with users for filtering tests."""
    store.load({"User": users_for_filtering})
    return store


def test_list_with_equality_filter(store_with_users: DataStore) -> None:
    """Test list with equality filter."""
    filters = [FilterSpec(field="city", operator=FilterOperator.EQ, value="NYC")]
    result = store_with_users.list("User", page=1, page_size=10, filters=filters)

    assert len(result.items) == 3
    assert all(item["city"] == "NYC" for item in result.items)
    assert result.pagination.total_items == 3


def test_list_with_gte_filter(store_with_users: DataStore) -> None:
    """Test list with greater than or equal filter."""
    filters = [FilterSpec(field="age", operator=FilterOperator.GTE, value=30)]
    result = store_with_users.list("User", page=1, page_size=10, filters=filters)

    assert len(result.items) == 3
    assert all(item["age"] >= 30 for item in result.items)
    assert {item["name"] for item in result.items} == {"Bob", "Charlie", "Frank"}


def test_list_with_gt_filter(store_with_users: DataStore) -> None:
    """Test list with greater than filter."""
    filters = [FilterSpec(field="age", operator=FilterOperator.GT, value=30)]
    result = store_with_users.list("User", page=1, page_size=10, filters=filters)

    assert len(result.items) == 2
    assert all(item["age"] > 30 for item in result.items)


def test_list_with_lte_filter(store_with_users: DataStore) -> None:
    """Test list with less than or equal filter."""
    filters = [FilterSpec(field="age", operator=FilterOperator.LTE, value=28)]
    result = store_with_users.list("User", page=1, page_size=10, filters=filters)

    assert len(result.items) == 3
    assert all(item["age"] <= 28 for item in result.items)


def test_list_with_lt_filter(store_with_users: DataStore) -> None:
    """Test list with less than filter."""
    filters = [FilterSpec(field="age", operator=FilterOperator.LT, value=28)]
    result = store_with_users.list("User", page=1, page_size=10, filters=filters)

    assert len(result.items) == 2
    assert all(item["age"] < 28 for item in result.items)


def test_list_with_contains_filter(store_with_users: DataStore) -> None:
    """Test list with contains filter (case-insensitive)."""
    filters = [
        FilterSpec(field="email", operator=FilterOperator.CONTAINS, value="example")
    ]
    result = store_with_users.list("User", page=1, page_size=10, filters=filters)

    assert len(result.items) == 3
    assert all(
        "example" in item["email"].lower() for item in result.items if item["email"]
    )


def test_list_with_startswith_filter(store_with_users: DataStore) -> None:
    """Test list with startswith filter (case-insensitive)."""
    filters = [FilterSpec(field="name", operator=FilterOperator.STARTSWITH, value="a")]
    result = store_with_users.list("User", page=1, page_size=10, filters=filters)

    assert len(result.items) == 1
    assert result.items[0]["name"] == "Alice"


def test_list_with_endswith_filter(store_with_users: DataStore) -> None:
    """Test list with endswith filter (case-insensitive)."""
    filters = [
        FilterSpec(field="email", operator=FilterOperator.ENDSWITH, value="test.com")
    ]
    result = store_with_users.list("User", page=1, page_size=10, filters=filters)

    assert len(result.items) == 2
    assert all(
        item["email"].endswith("test.com") for item in result.items if item["email"]
    )


def test_list_with_in_filter(store_with_users: DataStore) -> None:
    """Test list with IN filter."""
    filters = [
        FilterSpec(field="city", operator=FilterOperator.IN, value=["NYC", "SF"])
    ]
    result = store_with_users.list("User", page=1, page_size=10, filters=filters)

    assert len(result.items) == 4
    assert all(item["city"] in ["NYC", "SF"] for item in result.items)


def test_list_with_null_filter(store_with_users: DataStore) -> None:
    """Test list with null filter."""
    filters = [FilterSpec(field="email", operator=FilterOperator.EQ, value=None)]
    result = store_with_users.list("User", page=1, page_size=10, filters=filters)

    assert len(result.items) == 1
    assert result.items[0]["name"] == "Frank"
    assert result.items[0]["email"] is None


def test_list_with_multiple_filters_and_logic(store_with_users: DataStore) -> None:
    """Test list with multiple filters using AND logic."""
    filters = [
        FilterSpec(field="city", operator=FilterOperator.EQ, value="NYC"),
        FilterSpec(field="age", operator=FilterOperator.GTE, value=25),
    ]
    result = store_with_users.list("User", page=1, page_size=10, filters=filters)

    assert len(result.items) == 2
    assert all(item["city"] == "NYC" and item["age"] >= 25 for item in result.items)
    assert {item["name"] for item in result.items} == {"Alice", "Charlie"}


def test_list_filters_affect_pagination_count(store_with_users: DataStore) -> None:
    """Test that filters correctly affect total_items in pagination."""
    filters = [FilterSpec(field="city", operator=FilterOperator.EQ, value="NYC")]
    result = store_with_users.list("User", page=1, page_size=2, filters=filters)

    assert len(result.items) == 2
    assert result.pagination.total_items == 3
    assert result.pagination.total_pages == 2
    assert result.pagination.has_next is True


def test_list_string_filters_case_insensitive(store_with_users: DataStore) -> None:
    """Test that string filters are case-insensitive."""
    filters = [
        FilterSpec(field="name", operator=FilterOperator.CONTAINS, value="ALICE")
    ]
    result = store_with_users.list("User", page=1, page_size=10, filters=filters)

    assert len(result.items) == 1
    assert result.items[0]["name"] == "Alice"


# =============================================================================
# TESTS: Sorting
# =============================================================================


def test_list_with_single_field_sort_asc(store_with_users: DataStore) -> None:
    """Test list with single field ascending sort."""
    sort_by = [SortSpec(field="age", direction=SortDirection.ASC)]
    result = store_with_users.list("User", page=1, page_size=10, sort_by=sort_by)

    ages = [item["age"] for item in result.items]
    assert ages == sorted(ages)
    assert result.items[0]["name"] == "Eve"  # age 22
    assert result.items[-1]["name"] == "Frank"  # age 40


def test_list_with_single_field_sort_desc(store_with_users: DataStore) -> None:
    """Test list with single field descending sort."""
    sort_by = [SortSpec(field="age", direction=SortDirection.DESC)]
    result = store_with_users.list("User", page=1, page_size=10, sort_by=sort_by)

    ages = [item["age"] for item in result.items]
    assert ages == sorted(ages, reverse=True)
    assert result.items[0]["name"] == "Frank"  # age 40
    assert result.items[-1]["name"] == "Eve"  # age 22


def test_list_with_multiple_field_sort(store_with_users: DataStore) -> None:
    """Test list with multiple field sort."""
    sort_by = [
        SortSpec(field="city", direction=SortDirection.ASC),
        SortSpec(field="age", direction=SortDirection.DESC),
    ]
    result = store_with_users.list("User", page=1, page_size=10, sort_by=sort_by)

    # First sorted by city ASC, then by age DESC within same city
    cities = [item["city"] for item in result.items]
    assert cities == ["LA", "LA", "NYC", "NYC", "NYC", "SF"]

    # Within LA: Frank (40) should come before Bob (30)
    la_users = [item for item in result.items if item["city"] == "LA"]
    assert la_users[0]["name"] == "Frank"
    assert la_users[1]["name"] == "Bob"


def test_list_sort_handles_none_values(store_with_users: DataStore) -> None:
    """Test that sorting handles None values correctly (puts them at end)."""
    sort_by = [SortSpec(field="email", direction=SortDirection.ASC)]
    result = store_with_users.list("User", page=1, page_size=10, sort_by=sort_by)

    # None values should be at the end
    assert result.items[-1]["email"] is None
    assert result.items[-1]["name"] == "Frank"


def test_list_sort_with_different_types(store_with_users: DataStore) -> None:
    """Test sorting with different data types (int, str)."""
    # Test int sorting
    sort_by_int = [SortSpec(field="age", direction=SortDirection.ASC)]
    result_int = store_with_users.list(
        "User", page=1, page_size=10, sort_by=sort_by_int
    )
    ages = [item["age"] for item in result_int.items]
    assert ages == [22, 25, 28, 30, 35, 40]

    # Test string sorting
    sort_by_str = [SortSpec(field="name", direction=SortDirection.ASC)]
    result_str = store_with_users.list(
        "User", page=1, page_size=10, sort_by=sort_by_str
    )
    names = [item["name"] for item in result_str.items]
    assert names == ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"]


# =============================================================================
# TESTS: Combined Filtering and Sorting
# =============================================================================


def test_list_with_filters_and_sorting(store_with_users: DataStore) -> None:
    """Test list with both filters and sorting."""
    filters = [FilterSpec(field="city", operator=FilterOperator.EQ, value="NYC")]
    sort_by = [SortSpec(field="age", direction=SortDirection.DESC)]
    result = store_with_users.list(
        "User", page=1, page_size=10, filters=filters, sort_by=sort_by
    )

    assert len(result.items) == 3
    assert all(item["city"] == "NYC" for item in result.items)
    # Sorted by age descending: Charlie (35), Alice (25), Eve (22)
    assert result.items[0]["name"] == "Charlie"
    assert result.items[1]["name"] == "Alice"
    assert result.items[2]["name"] == "Eve"


def test_list_with_filters_sorting_and_page_pagination(
    store_with_users: DataStore,
) -> None:
    """Test list with filters, sorting, and page-based pagination."""
    filters = [FilterSpec(field="age", operator=FilterOperator.GTE, value=25)]
    sort_by = [SortSpec(field="name", direction=SortDirection.ASC)]
    result = store_with_users.list(
        "User", page=1, page_size=2, filters=filters, sort_by=sort_by
    )

    # Filtered: Alice, Bob, Charlie, Diana, Frank (5 total)
    # Sorted by name: Alice, Bob, Charlie, Diana, Frank
    # Page 1, size 2: Alice, Bob
    assert len(result.items) == 2
    assert result.items[0]["name"] == "Alice"
    assert result.items[1]["name"] == "Bob"
    assert result.pagination.total_items == 5
    assert result.pagination.total_pages == 3
    assert result.pagination.has_next is True


def test_list_with_filters_sorting_and_offset_pagination(
    store_with_users: DataStore,
) -> None:
    """Test list with filters, sorting, and offset-based pagination."""
    filters = [FilterSpec(field="age", operator=FilterOperator.LTE, value=30)]
    sort_by = [SortSpec(field="age", direction=SortDirection.ASC)]
    result = store_with_users.list(
        "User", offset=1, limit=2, filters=filters, sort_by=sort_by
    )

    # Filtered: Eve (22), Alice (25), Diana (28), Bob (30) - 4 total
    # Sorted by age ASC: Eve (22), Alice (25), Diana (28), Bob (30)
    # Offset 1, limit 2: Alice, Diana
    assert len(result.items) == 2
    assert result.items[0]["name"] == "Alice"
    assert result.items[1]["name"] == "Diana"
    assert result.pagination.total_items == 4
    assert result.pagination.offset == 1
    assert result.pagination.has_next is True
    assert result.pagination.has_prev is True


# =============================================================================
# TESTS: Backward Compatibility
# =============================================================================


def test_list_with_legacy_filter_func_still_works(store_with_users: DataStore) -> None:
    """Test that legacy filter_func parameter still works."""
    result = store_with_users.list(
        "User", page=1, page_size=10, filter_func=lambda u: u["age"] > 30
    )

    assert len(result.items) == 2
    assert all(item["age"] > 30 for item in result.items)


def test_list_with_both_filter_func_and_filters(store_with_users: DataStore) -> None:
    """Test that both filter_func and filters can be used together (AND logic)."""
    filters = [FilterSpec(field="city", operator=FilterOperator.EQ, value="NYC")]
    result = store_with_users.list(
        "User",
        page=1,
        page_size=10,
        filter_func=lambda u: u["age"] >= 25,
        filters=filters,
    )

    # filter_func: age >= 25 → Alice, Charlie
    # filters: city == NYC
    # Combined (AND): Alice, Charlie
    assert len(result.items) == 2
    assert {item["name"] for item in result.items} == {"Alice", "Charlie"}
