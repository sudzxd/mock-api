"""Tests for data store."""

from __future__ import annotations

import threading

import pytest
from mock_api.core.constants import (
    DEFAULT_PAGE_NUMBER,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    PRIMARY_KEY_FIELD,
)
from mock_api.core.store import DataStore
from mock_api.core.types import PaginationInfo, QueryResult

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

    with pytest.raises(ValueError, match="already exists"):
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
    with pytest.raises(ValueError, match="not found"):
        loaded_store.update("User", 999, {"name": "Ghost"})


def test_update_nonexistent_model_raises_error(loaded_store: DataStore) -> None:
    """Test updating non-existent model raises error."""
    with pytest.raises(ValueError, match="not found"):
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
    with pytest.raises(ValueError, match="Page must be"):
        loaded_store.list("User", page=0, page_size=10)

    with pytest.raises(ValueError, match="Page must be"):
        loaded_store.list("User", page=-1, page_size=10)


def test_list_invalid_page_size_raises_error(loaded_store: DataStore) -> None:
    """Test that invalid page size raises error."""
    with pytest.raises(ValueError, match="Page size must be"):
        loaded_store.list("User", page=1, page_size=0)

    with pytest.raises(ValueError, match="Page size must be"):
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
