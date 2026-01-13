"""Tests for DataStore bulk operations."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Any

# Third-party
import pytest

# Project/Local
from mock_api.core.constants import PRIMARY_KEY_FIELD, BulkResponseKey
from mock_api.core.exceptions import (
    BatchSizeExceededError,
    DuplicateInstanceError,
    InstanceNotFoundError,
)
from mock_api.core.store import DataStore

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def store() -> DataStore:
    """Create a fresh DataStore instance."""
    return DataStore()


@pytest.fixture
def sample_users() -> list[dict[str, Any]]:
    """Sample user data for testing."""
    return [
        {"name": "Alice", "email": "alice@example.com"},
        {"name": "Bob", "email": "bob@example.com"},
        {"name": "Charlie", "email": "charlie@example.com"},
    ]


# =============================================================================
# TESTS: Bulk Create
# =============================================================================


def test_bulk_create_success(
    store: DataStore, sample_users: list[dict[str, Any]]
) -> None:
    """Test bulk create with all items succeeding."""
    result = store.bulk_create("User", sample_users)

    assert result[BulkResponseKey.CREATED] == 3
    assert len(result[BulkResponseKey.DATA]) == 3
    assert BulkResponseKey.ERRORS not in result

    # Verify all items were created
    for idx, item in enumerate(result[BulkResponseKey.DATA]):
        assert item[PRIMARY_KEY_FIELD] == idx + 1
        assert item["name"] == sample_users[idx]["name"]
        assert item["email"] == sample_users[idx]["email"]


def test_bulk_create_empty_list(store: DataStore) -> None:
    """Test bulk create with empty list."""
    result = store.bulk_create("User", [])

    assert result[BulkResponseKey.CREATED] == 0
    assert result[BulkResponseKey.DATA] == []
    assert BulkResponseKey.ERRORS not in result


def test_bulk_create_auto_assigns_ids(store: DataStore) -> None:
    """Test that bulk create auto-assigns sequential IDs."""
    data = [{"name": f"User{i}"} for i in range(5)]
    result = store.bulk_create("User", data)

    created_ids = [item[PRIMARY_KEY_FIELD] for item in result[BulkResponseKey.DATA]]
    assert created_ids == [1, 2, 3, 4, 5]


def test_bulk_create_with_duplicate_id_rollback(store: DataStore) -> None:
    """Test bulk create rolls back on duplicate ID when not partial."""
    # Create initial item
    store.create("User", {"name": "Existing"})

    # Try to bulk create with duplicate ID
    data = [
        {"name": "Alice"},
        {PRIMARY_KEY_FIELD: 1, "name": "Duplicate"},  # Duplicate ID
        {"name": "Bob"},
    ]

    with pytest.raises(DuplicateInstanceError):
        store.bulk_create("User", data)

    # Verify rollback - only original item exists
    assert store.count("User") == 1


def test_bulk_create_partial_mode_continues_on_error(store: DataStore) -> None:
    """Test bulk create in partial mode continues on errors."""
    # Create initial item
    store.create("User", {"name": "Existing"})

    data = [
        {"name": "Alice"},
        {PRIMARY_KEY_FIELD: 1, "name": "Duplicate"},  # Will fail
        {"name": "Bob"},
    ]

    result = store.bulk_create("User", data, allow_partial=True)

    assert result[BulkResponseKey.CREATED] == 2
    assert len(result[BulkResponseKey.DATA]) == 2
    assert len(result[BulkResponseKey.ERRORS]) == 1
    assert result[BulkResponseKey.ERRORS][0]["index"] == 1


def test_bulk_create_exceeds_batch_size(store: DataStore) -> None:
    """Test bulk create raises error when batch size exceeded."""
    data = [{"name": f"User{i}"} for i in range(10)]

    with pytest.raises(BatchSizeExceededError):
        store.bulk_create("User", data, max_batch_size=5)


# =============================================================================
# TESTS: Bulk Update
# =============================================================================


def test_bulk_update_success(store: DataStore) -> None:
    """Test bulk update with all items succeeding."""
    # Create initial items
    store.create("User", {"name": "Alice", "email": "alice@example.com"})
    store.create("User", {"name": "Bob", "email": "bob@example.com"})

    # Update them
    updates = [
        {PRIMARY_KEY_FIELD: 1, "name": "Alice Updated"},
        {PRIMARY_KEY_FIELD: 2, "name": "Bob Updated"},
    ]

    result = store.bulk_update("User", updates)

    assert result[BulkResponseKey.UPDATED] == 2
    assert len(result[BulkResponseKey.DATA]) == 2
    assert BulkResponseKey.ERRORS not in result

    # Verify updates
    user1 = store.read("User", 1)
    user2 = store.read("User", 2)
    assert user1 is not None
    assert user2 is not None
    assert user1["name"] == "Alice Updated"
    assert user2["name"] == "Bob Updated"


def test_bulk_update_empty_list(store: DataStore) -> None:
    """Test bulk update with empty list."""
    result = store.bulk_update("User", [])

    assert result[BulkResponseKey.UPDATED] == 0
    assert result[BulkResponseKey.DATA] == []


def test_bulk_update_missing_id_rollback(store: DataStore) -> None:
    """Test bulk update rolls back when ID missing in non-partial mode."""
    store.create("User", {"name": "Alice"})
    store.create("User", {"name": "Bob"})

    updates = [
        {PRIMARY_KEY_FIELD: 1, "name": "Alice Updated"},
        {"name": "Missing ID"},  # Missing ID
    ]

    with pytest.raises(ValueError):
        store.bulk_update("User", updates)

    # Verify rollback
    user1 = store.read("User", 1)
    assert user1 is not None
    assert user1["name"] == "Alice"  # Not updated


def test_bulk_update_not_found_rollback(store: DataStore) -> None:
    """Test bulk update rolls back on not found error."""
    store.create("User", {"name": "Alice"})

    updates = [
        {PRIMARY_KEY_FIELD: 1, "name": "Alice Updated"},
        {PRIMARY_KEY_FIELD: 999, "name": "Not Found"},  # Doesn't exist
    ]

    with pytest.raises(InstanceNotFoundError):
        store.bulk_update("User", updates)

    # Verify rollback
    user1 = store.read("User", 1)
    assert user1 is not None
    assert user1["name"] == "Alice"  # Not updated


def test_bulk_update_partial_mode_continues_on_error(store: DataStore) -> None:
    """Test bulk update in partial mode continues on errors."""
    store.create("User", {"name": "Alice"})
    store.create("User", {"name": "Bob"})

    updates = [
        {PRIMARY_KEY_FIELD: 1, "name": "Alice Updated"},
        {PRIMARY_KEY_FIELD: 999, "name": "Not Found"},  # Will fail
        {PRIMARY_KEY_FIELD: 2, "name": "Bob Updated"},
    ]

    result = store.bulk_update("User", updates, allow_partial=True)

    assert result[BulkResponseKey.UPDATED] == 2
    assert len(result[BulkResponseKey.ERRORS]) == 1
    assert result[BulkResponseKey.ERRORS][0]["index"] == 1

    # Verify successful updates
    user1 = store.read("User", 1)
    user2 = store.read("User", 2)
    assert user1 is not None
    assert user2 is not None
    assert user1["name"] == "Alice Updated"
    assert user2["name"] == "Bob Updated"


def test_bulk_update_model_not_found(store: DataStore) -> None:
    """Test bulk update with non-existent model."""
    updates = [{PRIMARY_KEY_FIELD: 1, "name": "Test"}]

    with pytest.raises(InstanceNotFoundError):
        store.bulk_update("NonExistent", updates)


def test_bulk_update_exceeds_batch_size(store: DataStore) -> None:
    """Test bulk update raises error when batch size exceeded."""
    updates = [{PRIMARY_KEY_FIELD: i, "name": f"User{i}"} for i in range(10)]

    with pytest.raises(BatchSizeExceededError):
        store.bulk_update("User", updates, max_batch_size=5)


# =============================================================================
# TESTS: Bulk Delete
# =============================================================================


def test_bulk_delete_success(store: DataStore) -> None:
    """Test bulk delete with all items succeeding."""
    # Create items
    store.create("User", {"name": "Alice"})
    store.create("User", {"name": "Bob"})
    store.create("User", {"name": "Charlie"})

    result = store.bulk_delete("User", [1, 2, 3])

    assert result[BulkResponseKey.DELETED] == 3
    assert result[BulkResponseKey.IDS] == [1, 2, 3]
    assert BulkResponseKey.ERRORS not in result

    # Verify deletion
    assert store.count("User") == 0


def test_bulk_delete_empty_list(store: DataStore) -> None:
    """Test bulk delete with empty list."""
    result = store.bulk_delete("User", [])

    assert result[BulkResponseKey.DELETED] == 0
    assert result[BulkResponseKey.IDS] == []


def test_bulk_delete_not_found_rollback(store: DataStore) -> None:
    """Test bulk delete rolls back on not found error."""
    store.create("User", {"name": "Alice"})
    store.create("User", {"name": "Bob"})

    with pytest.raises(InstanceNotFoundError):
        store.bulk_delete("User", [1, 999, 2])  # 999 doesn't exist

    # Verify rollback - all items still exist
    assert store.count("User") == 2


def test_bulk_delete_partial_mode_continues_on_error(store: DataStore) -> None:
    """Test bulk delete in partial mode continues on errors."""
    store.create("User", {"name": "Alice"})
    store.create("User", {"name": "Bob"})
    store.create("User", {"name": "Charlie"})

    result = store.bulk_delete("User", [1, 999, 3], allow_partial=True)

    assert result[BulkResponseKey.DELETED] == 2
    assert result[BulkResponseKey.IDS] == [1, 3]
    assert len(result[BulkResponseKey.ERRORS]) == 1
    assert result[BulkResponseKey.ERRORS][0]["index"] == 1

    # Verify successful deletions and remaining item
    assert store.count("User") == 1
    user2 = store.read("User", 2)
    assert user2 is not None
    assert user2["name"] == "Bob"


def test_bulk_delete_model_not_found(store: DataStore) -> None:
    """Test bulk delete with non-existent model."""
    with pytest.raises(InstanceNotFoundError):
        store.bulk_delete("NonExistent", [1, 2, 3])


def test_bulk_delete_exceeds_batch_size(store: DataStore) -> None:
    """Test bulk delete raises error when batch size exceeded."""
    with pytest.raises(BatchSizeExceededError):
        store.bulk_delete("User", list(range(1, 11)), max_batch_size=5)


# =============================================================================
# TESTS: Thread Safety
# =============================================================================


def test_bulk_operations_are_atomic(store: DataStore) -> None:
    """Test that bulk operations are atomic within their scope."""
    # Create initial data
    for i in range(5):
        store.create("User", {"name": f"User{i}"})

    # Attempt bulk update with error - should rollback all
    updates = [{PRIMARY_KEY_FIELD: i, "name": f"Updated{i}"} for i in range(1, 6)]
    updates.append({PRIMARY_KEY_FIELD: 999, "name": "Invalid"})  # Will fail

    with pytest.raises(InstanceNotFoundError):
        store.bulk_update("User", updates)

    # Verify no updates were applied
    for i in range(1, 6):
        user = store.read("User", i)
        assert user is not None
        assert user["name"] == f"User{i - 1}"  # Original name


def test_bulk_create_increments_counter_correctly(store: DataStore) -> None:
    """Test that bulk create increments ID counter correctly."""
    # Bulk create 3 items
    store.bulk_create("User", [{"name": f"User{i}"} for i in range(3)])

    # Create single item - should get ID 4
    result = store.create("User", {"name": "User4"})
    assert result[PRIMARY_KEY_FIELD] == 4
