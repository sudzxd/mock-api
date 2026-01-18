"""Exception hierarchy for MockAPI Server.

Organized by layer and concern:
- Base exceptions
- Schema parsing exceptions
- Repository/storage exceptions
- Validation exceptions
- Generation exceptions
"""

from .base import MockAPIError
from .generation import GenerationError
from .repository import (
    BulkOperationError,
    DuplicateKeyError,
    EntityNotFoundError,
    ModelNotFoundError,
    RepositoryError,
)
from .schema import (
    SchemaError,
    SchemaFileNotFoundError,
    SchemaParseError,
    SchemaValidationError,
    UnsupportedSchemaError,
)
from .storage import StorageError, UnsupportedStorageError
from .validation import ValidationError

__all__ = [
    # Base
    "MockAPIError",
    # Schema
    "SchemaError",
    "SchemaParseError",
    "SchemaFileNotFoundError",
    "SchemaValidationError",
    "UnsupportedSchemaError",
    # Repository
    "RepositoryError",
    "ModelNotFoundError",
    "EntityNotFoundError",
    "DuplicateKeyError",
    "BulkOperationError",
    # Storage
    "StorageError",
    "UnsupportedStorageError",
    # Validation
    "ValidationError",
    # Generation
    "GenerationError",
]
