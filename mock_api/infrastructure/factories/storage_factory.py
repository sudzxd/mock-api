"""Storage factory for creating repository instances from URL."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Any
from urllib.parse import urlparse

# Project/local
from mock_api.core.exceptions.storage import UnsupportedStorageError
from mock_api.domain.services.protocols import (
    IFilterExecutor,
    ISortExecutor,
    IValidationService,
)
from mock_api.domain.value_objects.schema import ModelSchema
from mock_api.infrastructure.repositories.memory.memory_repository import (
    MemoryRepository,
)

# =============================================================================
# TYPES & CONSTANTS
# =============================================================================
# Storage URL schemes
MEMORY_SCHEME = "memory"
JSON_SCHEME = "json"
SQLITE_SCHEME = "sqlite"
POSTGRESQL_SCHEME = "postgresql"
REDIS_SCHEME = "redis"


# =============================================================================
# CORE CLASSES
# =============================================================================
class StorageFactory:
    """Factory for creating storage backends from URL.

    Supported formats:
    - memory:// -> MemoryRepository
    - json://path/to/file.json -> JSONRepository
    - sqlite:///path/to/file.db -> SQLiteRepository
    - postgresql://user:pass@host:port/db -> PostgreSQLRepository
    - redis://host:port -> RedisRepository

    Registry pattern allows adding custom backends.
    """

    # Registry: scheme -> (class, requires_path)
    _registry: dict[str, tuple[type, bool]] = {}

    @classmethod
    def create(
        cls,
        storage_url: str | None,
        schemas: dict[str, ModelSchema],
        validation_service: IValidationService,
        filter_executor: IFilterExecutor,
        sort_executor: ISortExecutor,
    ) -> (
        Any
    ):  # Returns object implementing IReadRepository, IWriteRepository, IBulkRepository
        """Create repository from storage URL.

        Implementation:
        1. Parse URL scheme
        2. Lookup in registry
        3. Instantiate appropriate repository
        4. Return instance

        Args:
            storage_url: Storage URL (e.g., 'memory://', 'sqlite:///data.db')
            schemas: Model schemas for validation
            validation_service: Service for data validation
            filter_executor: Service for executing filter specifications
            sort_executor: Service for executing sort specifications

        Returns:
            Repository instance

        Raises:
            UnsupportedStorageError: If scheme not supported
            ValueError: If URL format is invalid
        """
        # Parse URL
        scheme, _path = cls._parse_url(storage_url or "memory://")

        # Validate scheme
        cls._validate_scheme(scheme)

        # Get repository class
        repository_class, _requires_path = cls._registry[scheme]

        # Create instance with all dependencies
        # For now, all repositories take schemas, validation_service, and executors
        # TODO: Use path and requires_path for file-based/remote storage
        return repository_class(
            schemas, validation_service, filter_executor, sort_executor
        )

    @classmethod
    def register(
        cls,
        scheme: str,
        repository_class: type,
        requires_path: bool = True,
    ) -> None:
        """Register custom storage backend.

        Args:
            scheme: URL scheme (e.g., 'redis', 'mongodb')
            repository_class: Repository class
            requires_path: Whether this backend needs a path
        """
        cls._registry[scheme] = (repository_class, requires_path)

    @classmethod
    def _parse_url(cls, storage_url: str) -> tuple[str, str | None]:
        """Parse storage URL into scheme and path.

        Args:
            storage_url: Storage URL

        Returns:
            Tuple of (scheme, path)

        Raises:
            ValueError: If URL is invalid
        """
        # Default to memory:// if no URL provided
        if not storage_url:
            return (MEMORY_SCHEME, None)

        # Parse URL
        parsed = urlparse(storage_url)

        # Extract scheme
        scheme = parsed.scheme.lower()
        if not scheme:
            raise ValueError(f"Invalid storage URL '{storage_url}': missing scheme")

        # Extract path (if applicable)
        path = parsed.path if parsed.path else None

        return (scheme, path)

    @classmethod
    def _validate_scheme(cls, scheme: str) -> None:
        """Validate scheme is registered.

        Args:
            scheme: URL scheme

        Raises:
            UnsupportedStorageError: If scheme not registered
        """
        if scheme not in cls._registry:
            available_schemes = list(cls._registry.keys())
            raise UnsupportedStorageError(
                storage_url=scheme,
                supported_schemes=available_schemes,
            )


# =============================================================================
# AUTO-REGISTRATION
# =============================================================================
# Auto-register built-in storage backends
StorageFactory.register(MEMORY_SCHEME, MemoryRepository, requires_path=False)
