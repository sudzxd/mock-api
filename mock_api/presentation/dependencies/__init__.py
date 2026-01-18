"""FastAPI dependency injection."""

from .injection import (
    get_create_entity_use_case,
    get_delete_entity_use_case,
    get_get_entity_use_case,
    get_list_entities_use_case,
    get_update_entity_use_case,
    initialize_dependencies,
)

__all__ = [
    "initialize_dependencies",
    "get_create_entity_use_case",
    "get_get_entity_use_case",
    "get_update_entity_use_case",
    "get_delete_entity_use_case",
    "get_list_entities_use_case",
]
