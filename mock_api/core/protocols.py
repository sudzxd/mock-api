"""Protocol definitions for core components.

This module defines abstract interfaces (protocols) for all major components,
enabling dependency inversion and allowing alternative implementations.

Following SOLID principles:
- Dependency Inversion: Depend on abstractions, not concretions
- Liskov Substitution: Implementations can be swapped
- Interface Segregation: Focused, cohesive interfaces

Example:
    >>> from mock_api.core.protocols import IDataStore
    >>> class CustomStore:
    ...     def create(self, model_name: str, data: dict, auto_id: bool = True):
    ...         # Your implementation
    ...         pass
    >>> # Use custom implementation
    >>> server = Server("models.py", store=CustomStore())
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, Self

from .types import FilterSpec, ModelSchema, QueryResult, SortSpec

# =============================================================================
# PARSER PROTOCOLS
# =============================================================================


class ISchemaParser(Protocol):
    """Protocol for parsing Pydantic models into internal schema format.

    Implementations must extract model definitions from Python files and
    convert them into ModelSchema objects for internal use.

    Example:
        >>> class CustomParser:
        ...     def parse_file(self, file_path: str) -> dict[str, ModelSchema]:
        ...         # Your custom parsing logic
        ...         return {"User": ModelSchema(...)}
        >>> parser: ISchemaParser = CustomParser()
    """

    def parse_file(self, file_path: str) -> dict[str, ModelSchema]:
        """Parse all Pydantic models from a Python file.

        Args:
            file_path: Path to Python file containing Pydantic models.

        Returns:
            Dictionary mapping model names to their schemas.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file is invalid.
        """
        ...

    def get_models_with_field(self, field_name: str) -> set[str]:
        """Get all models that have a specific field.

        Args:
            field_name: Name of the field to search for.

        Returns:
            Set of model names containing the field.
        """
        ...

    def get_models_with_type(self, field_type: type) -> set[str]:
        """Get all models that have fields of a specific type.

        Args:
            field_type: Python type to search for.

        Returns:
            Set of model names containing fields of this type.
        """
        ...

    def has_field(self, model_name: str, field_name: str) -> bool:
        """Check if a model has a specific field.

        Args:
            model_name: Name of the model.
            field_name: Name of the field.

        Returns:
            True if field exists, False otherwise.
        """
        ...


# =============================================================================
# STORAGE PROTOCOLS
# =============================================================================


class IConcurrencyManager(Protocol):
    """Protocol for concurrency and thread safety management.

    Different storage backends use different concurrency strategies:
    - In-memory: threading.Lock
    - SQL: Database transactions (BEGIN/COMMIT/ROLLBACK)
    - JSON: File locking (fcntl.flock)
    - Async: asyncio.Lock

    Example:
        >>> class SQLConcurrencyManager:
        ...     def __enter__(self):
        ...         self.conn.execute("BEGIN TRANSACTION")
        ...     def __exit__(self, exc_type, exc_val, exc_tb):
        ...         if exc_type:
        ...             self.conn.execute("ROLLBACK")
        ...         else:
        ...             self.conn.execute("COMMIT")
    """

    def __enter__(self) -> Self:
        """Acquire lock or begin transaction.

        Returns:
            Self for context manager protocol.
        """
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Release lock or commit/rollback transaction.

        Args:
            exc_type: Exception type if error occurred.
            exc_val: Exception value if error occurred.
            exc_tb: Exception traceback if error occurred.
        """
        ...


class IStorageManager(Protocol):
    """Protocol for low-level storage operations.

    Abstracts the underlying storage mechanism:
    - In-memory: OrderedDict operations
    - SQL: SQL queries (SELECT/INSERT/UPDATE/DELETE)
    - JSON: File read/write operations
    - NoSQL: Database client operations

    Example:
        >>> class SQLStorageManager:
        ...     def get(self, model_name: str, instance_id: int):
        ...         cursor.execute("SELECT * FROM ? WHERE id = ?",
                    (model_name, instance_id))
        ...         return cursor.fetchone()
    """

    def ensure_model_exists(self, model_name: str) -> None:
        """Ensure storage structure exists for model.

        Args:
            model_name: Name of the model.
        """
        ...

    def get(self, model_name: str, instance_id: int) -> dict[str, Any] | None:
        """Retrieve instance by ID.

        Args:
            model_name: Name of the model.
            instance_id: ID of the instance.

        Returns:
            Instance dict or None if not found.
        """
        ...

    def put(self, model_name: str, instance_id: int, instance: dict[str, Any]) -> None:
        """Store instance.

        Args:
            model_name: Name of the model.
            instance_id: ID of the instance.
            instance: Instance data to store.
        """
        ...

    def delete(self, model_name: str, instance_id: int) -> dict[str, Any] | None:
        """Delete instance and return it.

        Args:
            model_name: Name of the model.
            instance_id: ID of the instance.

        Returns:
            Deleted instance or None if not found.
        """
        ...

    def get_all(self, model_name: str) -> list[dict[str, Any]]:
        """Get all instances for a model.

        Args:
            model_name: Name of the model.

        Returns:
            List of all instances.
        """
        ...

    def contains(self, model_name: str, instance_id: int) -> bool:
        """Check if instance exists.

        Args:
            model_name: Name of the model.
            instance_id: ID to check.

        Returns:
            True if instance exists, False otherwise.
        """
        ...

    def count(self, model_name: str) -> int:
        """Count instances in a model.

        Args:
            model_name: Name of the model.

        Returns:
            Number of instances.
        """
        ...

    def clear(self, model_name: str | None = None) -> None:
        """Clear storage.

        Args:
            model_name: If provided, clear only this model. Otherwise clear all.
        """
        ...

    def get_models(self) -> list[str]:
        """Get list of all model names in storage.

        Returns:
            List of model names.
        """
        ...


class IRepository(Protocol):
    """Protocol for basic CRUD operations on data storage.

    Provides foundational data access operations without query logic.
    Implementations handle storage-specific concerns (in-memory, JSON, SQLite, etc.).

    TODO: Enable multiple storage backends (issues #48-51):
    - JSON file storage (issue #48)
    - SQLite storage (issue #49)
    - PostgreSQL storage (issue #50)
    - Redis storage (issue #51)

    Example:
        >>> class SQLiteRepository:
        ...     def create(self, model_name: str, data: dict, auto_id: bool = True):
        ...         # SQLite implementation
        ...         pass
        >>> repo: IRepository = SQLiteRepository()
    """

    def load(self, data: dict[str, list[dict[str, Any]]]) -> None:
        """Load bulk data into the repository.

        Args:
            data: Dictionary mapping model names to lists of instances.
        """
        ...

    def create(
        self, model_name: str, data: dict[str, Any], auto_id: bool = True
    ) -> dict[str, Any]:
        """Create a new instance.

        Args:
            model_name: Name of the model.
            data: Dictionary of field values.
            auto_id: If True, automatically assign ID if not provided.

        Returns:
            The created instance with ID assigned.
        """
        ...

    def read(self, model_name: str, instance_id: int) -> dict[str, Any] | None:
        """Read a single instance by ID.

        Args:
            model_name: Name of the model.
            instance_id: ID of the instance.

        Returns:
            The instance or None if not found.
        """
        ...

    def update(
        self, model_name: str, instance_id: int, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing instance.

        Args:
            model_name: Name of the model.
            instance_id: ID of the instance to update.
            data: Dictionary of field values to update.

        Returns:
            The updated instance.
        """
        ...

    def delete(self, model_name: str, instance_id: int) -> bool:
        """Delete an instance by ID.

        Args:
            model_name: Name of the model.
            instance_id: ID of the instance to delete.

        Returns:
            True if deleted, False if not found.
        """
        ...

    def list(
        self,
        model_name: str,
        page: int | None = None,
        page_size: int | None = None,
        offset: int | None = None,
        limit: int | None = None,
        filters: list[FilterSpec] | None = None,
        sort_by: list[SortSpec] | None = None,
        filter_func: Callable[[dict[str, Any]], bool] | None = None,
    ) -> QueryResult:
        """List instances with optional filtering, sorting, and pagination.

        Implementations should optimize queries for their backend:
        - In-memory: Filter/sort in Python after loading
        - SQL: Generate WHERE/ORDER BY clauses for database-level optimization

        Args:
            model_name: Name of the model.
            page: Page number (1-indexed) for page-based pagination.
            page_size: Number of items per page.
            offset: Starting offset (0-indexed) for offset-based pagination.
            limit: Maximum items to return.
            filters: Optional list of filter specifications.
            sort_by: Optional list of sort specifications.
            filter_func: Optional custom filter function (legacy support).

        Returns:
            QueryResult with filtered, sorted, paginated items and metadata.

        Note:
            SQL implementations should push filters/sorts to database level,
            not load all data into memory first.
        """
        ...

    def count(
        self,
        model_name: str,
        filter_func: Callable[[dict[str, Any]], bool] | None = None,
    ) -> int:
        """Count instances, optionally with filtering.

        Args:
            model_name: Name of the model.
            filter_func: Optional function to filter instances.

        Returns:
            Number of instances matching the filter.
        """
        ...

    def clear(self, model_name: str | None = None) -> None:
        """Clear data from repository.

        Args:
            model_name: Name of model to clear, or None to clear all.
        """
        ...

    def get_models(self) -> list[str]:
        """Get list of all model names in repository.

        Returns:
            List of model names.
        """
        ...


class IBulkRepository(Protocol):
    """Protocol for bulk operations on data storage.

    Provides atomic bulk operations for efficient batch processing.
    Implementations should optimize for their specific backend.

    TODO: Optimize bulk operations for different backends (issues #48-51)

    Example:
        >>> class PostgreSQLBulkRepository:
        ...     def bulk_create(self, model_name: str, data_list: list[dict]):
        ...         # Use PostgreSQL COPY for efficient bulk insert
        ...         pass
    """

    def bulk_create(
        self,
        model_name: str,
        data_list: list[dict[str, Any]],
        allow_partial: bool = False,
        max_batch_size: int | None = None,
    ) -> dict[str, Any]:
        """Create multiple instances atomically.

        Args:
            model_name: Name of the model.
            data_list: List of instances to create.
            allow_partial: If True, continue on errors; if False, rollback.
            max_batch_size: Maximum batch size allowed.

        Returns:
            Dict with 'created' count and optional 'errors'.
        """
        ...

    def bulk_update(
        self,
        model_name: str,
        data_list: list[dict[str, Any]],
        allow_partial: bool = False,
        max_batch_size: int | None = None,
    ) -> dict[str, Any]:
        """Update multiple instances atomically.

        Args:
            model_name: Name of the model.
            data_list: List of instances to update (must include 'id').
            allow_partial: If True, continue on errors; if False, rollback.
            max_batch_size: Maximum batch size allowed.

        Returns:
            Dict with 'updated' count and optional 'errors'.
        """
        ...

    def bulk_delete(
        self,
        model_name: str,
        id_list: list[int],
        allow_partial: bool = False,
        max_batch_size: int | None = None,
    ) -> dict[str, Any]:
        """Delete multiple instances atomically.

        Args:
            model_name: Name of the model.
            id_list: List of instance IDs to delete.
            allow_partial: If True, continue on errors; if False, rollback.
            max_batch_size: Maximum batch size allowed.

        Returns:
            Dict with 'deleted' count and optional 'errors'.
        """
        ...


class IDataStore(Protocol):
    """Protocol for data storage and retrieval operations.

    Implementations provide thread-safe CRUD operations with support for
    filtering, sorting, pagination, and bulk operations.

    Example:
        >>> class RedisStore:
        ...     def create(self, model_name: str, data: dict, auto_id: bool = True):
        ...         # Redis implementation
        ...         pass
        >>> store: IDataStore = RedisStore()
    """

    def load(self, data: dict[str, list[dict[str, Any]]]) -> None:
        """Load bulk data into the store.

        Args:
            data: Dictionary mapping model names to lists of instances.
        """
        ...

    def create(
        self, model_name: str, data: dict[str, Any], auto_id: bool = True
    ) -> dict[str, Any]:
        """Create a new instance.

        Args:
            model_name: Name of the model to create.
            data: Dictionary of field values.
            auto_id: If True, automatically assign ID if not provided.

        Returns:
            The created instance with ID assigned.

        Raises:
            DuplicateInstanceError: If instance with same ID already exists.
        """
        ...

    def read(self, model_name: str, instance_id: int) -> dict[str, Any] | None:
        """Read a single instance by ID.

        Args:
            model_name: Name of the model.
            instance_id: ID of the instance to retrieve.

        Returns:
            The instance if found, None otherwise.
        """
        ...

    def update(
        self, model_name: str, instance_id: int, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing instance.

        Args:
            model_name: Name of the model.
            instance_id: ID of the instance to update.
            data: Dictionary of fields to update.

        Returns:
            The updated instance.

        Raises:
            InstanceNotFoundError: If instance not found.
        """
        ...

    def delete(self, model_name: str, instance_id: int) -> bool:
        """Delete an instance by ID.

        Args:
            model_name: Name of the model.
            instance_id: ID of the instance to delete.

        Returns:
            True if deleted, False if not found.
        """
        ...

    def list(
        self,
        model_name: str,
        page: int | None = None,
        page_size: int | None = None,
        offset: int | None = None,
        limit: int | None = None,
        filters: list[FilterSpec] | None = None,
        sort_by: list[SortSpec] | None = None,
        filter_func: Any = None,
    ) -> QueryResult:
        """List instances with pagination, filtering, and sorting.

        Args:
            model_name: Name of the model.
            page: Page number (1-indexed) for page-based pagination.
            page_size: Number of items per page.
            offset: Starting offset (0-indexed) for offset-based pagination.
            limit: Maximum items to return.
            filters: Optional list of filter specifications.
            sort_by: Optional list of sort specifications.
            filter_func: Optional custom filter function.

        Returns:
            QueryResult with items and pagination info.
        """
        ...

    def count(
        self,
        model_name: str,
        filter_func: Callable[[dict[str, Any]], bool] | None = None,
    ) -> int:
        """Count instances, optionally with filtering function.

        Args:
            model_name: Name of the model.
            filter_func: Optional function to filter instances.

        Returns:
            Number of instances matching the filter.
        """
        ...

    def bulk_create(
        self,
        model_name: str,
        data_list: list[dict[str, Any]],
        allow_partial: bool = False,
        max_batch_size: int | None = None,
    ) -> dict[str, Any]:
        """Create multiple instances atomically.

        Args:
            model_name: Name of the model to create.
            data_list: List of instance dictionaries to create.
            allow_partial: If True, continue on errors; if False, rollback.
            max_batch_size: Maximum batch size allowed.

        Returns:
            Dict with 'created' count, 'data' list, and optional 'errors'.

        Raises:
            BatchSizeExceededError: If batch size exceeds maximum.
        """
        ...

    def bulk_update(
        self,
        model_name: str,
        data_list: list[dict[str, Any]],
        allow_partial: bool = False,
        max_batch_size: int | None = None,
    ) -> dict[str, Any]:
        """Update multiple instances atomically.

        Args:
            model_name: Name of the model.
            data_list: List of dicts with 'id' and fields to update.
            allow_partial: If True, continue on errors; if False, rollback.
            max_batch_size: Maximum batch size allowed.

        Returns:
            Dict with 'updated' count, 'data' list, and optional 'errors'.

        Raises:
            BatchSizeExceededError: If batch size exceeds maximum.
            InstanceNotFoundError: If instance not found (when not in partial mode).
        """
        ...

    def bulk_delete(
        self,
        model_name: str,
        id_list: list[int],
        allow_partial: bool = False,
        max_batch_size: int | None = None,
    ) -> dict[str, Any]:
        """Delete multiple instances atomically.

        Args:
            model_name: Name of the model.
            id_list: List of instance IDs to delete.
            allow_partial: If True, continue on errors; if False, rollback.
            max_batch_size: Maximum batch size allowed.

        Returns:
            Dict with 'deleted' count and optional 'errors'.

        Raises:
            BatchSizeExceededError: If batch size exceeds maximum.
        """
        ...


# =============================================================================
# GENERATOR PROTOCOLS
# =============================================================================


class IDataGenerator(Protocol):
    """Protocol for generating mock data for models.

    Implementations generate realistic test data respecting field types,
    foreign key relationships, and semantic patterns.

    Example:
        >>> class CustomGenerator:
        ...     def generate(self, model_name: str, count: int = 10):
        ...         # Your custom generation logic
        ...         return [{"id": 1, "name": "Test"}]
        >>> generator: IDataGenerator = CustomGenerator(schemas)
    """

    @property
    def data(self) -> dict[str, list[dict[str, Any]]]:
        """Get all generated data.

        Returns:
            Dictionary mapping model names to lists of generated instances.
        """
        ...

    def generate(
        self,
        model_name: str,
        count: int = 10,
        exclude_fks: bool = False,
    ) -> list[dict[str, Any]]:
        """Generate mock data for a specific model.

        Args:
            model_name: Name of the model to generate data for.
            count: Number of instances to generate.
            exclude_fks: If True, don't populate foreign key fields.

        Returns:
            List of generated instances.
        """
        ...

    def generate_all(self, count: int = 10) -> dict[str, list[dict[str, Any]]]:
        """Generate mock data for all models.

        Respects foreign key dependencies and generates in correct order.

        Args:
            count: Number of instances to generate per model.

        Returns:
            Dictionary mapping model names to lists of generated instances.
        """
        ...


# =============================================================================
# ROUTER PROTOCOLS
# =============================================================================


class IRouterGenerator(Protocol):
    """Protocol for generating FastAPI routes from model schemas.

    Implementations create RESTful CRUD endpoints with validation, filtering,
    sorting, and pagination support.

    Example:
        >>> class CustomRouter:
        ...     def generate_routes(self):
        ...         # Your custom route generation logic
        ...         return FastAPIRouter()
        >>> router_gen: IRouterGenerator = CustomRouter(schemas, store)
    """

    def generate_routes(self) -> Any:
        """Generate FastAPI routes for all models.

        Creates CRUD endpoints for each model in schemas.

        Returns:
            FastAPI APIRouter with all generated routes.
        """
        ...


# =============================================================================
# SERVICE PROTOCOLS (from Phase 1)
# =============================================================================


class IFilterParser(Protocol):
    """Protocol for parsing and validating filter query parameters.

    Implementations parse query parameters like ?age__gte=18 into FilterSpec
    objects with proper type coercion and validation.

    Example:
        >>> class CustomFilterParser:
        ...     def parse_params(self, query_params, model_name, schema):
        ...         # Your custom filter parsing logic
        ...         return [FilterSpec(...)]
        >>> parser: IFilterParser = CustomFilterParser()
    """

    def parse_params(
        self,
        query_params: Any,
        model_name: str,
        schema: ModelSchema,
    ) -> list[FilterSpec]:
        """Parse filter query parameters into FilterSpec objects.

        Args:
            query_params: Query parameters from HTTP request.
            model_name: Name of the model being filtered.
            schema: Model schema for field validation.

        Returns:
            List of FilterSpec objects representing the filters.

        Raises:
            HTTPException: If filter parameters are invalid.
        """
        ...


class ISortParser(Protocol):
    """Protocol for parsing and validating sort query parameters.

    Implementations parse query parameters like ?sort=-created_at,name into
    SortSpec objects with field validation.

    Example:
        >>> class CustomSortParser:
        ...     def parse_param(self, sort_value, model_name, schema):
        ...         # Your custom sort parsing logic
        ...         return [SortSpec(...)]
        >>> parser: ISortParser = CustomSortParser()
    """

    def parse_param(
        self,
        sort_value: str | None,
        model_name: str,
        schema: ModelSchema,
    ) -> list[SortSpec]:
        """Parse sort query parameter into SortSpec objects.

        Args:
            sort_value: Sort parameter value (e.g., "-created_at,name").
            model_name: Name of the model being sorted.
            schema: Model schema for field validation.

        Returns:
            List of SortSpec objects representing the sort order.

        Raises:
            HTTPException: If sort parameters are invalid.
        """
        ...


class IModelFactory(Protocol):
    """Protocol for creating Pydantic models from schemas.

    Implementations create response models, input models (excluding ID), and
    list response models (with pagination) for FastAPI route handlers.

    Example:
        >>> class CustomModelFactory:
        ...     def create_response_model(self, schema):
        ...         # Your custom model creation logic
        ...         return YourPydanticModel
        >>> factory: IModelFactory = CustomModelFactory()
    """

    def create_response_model(self, schema: ModelSchema) -> type[Any]:
        """Create Pydantic response model from schema.

        Args:
            schema: Model schema containing field definitions.

        Returns:
            Pydantic model class for API responses.

        Raises:
            ValueError: If schema is invalid or missing pydantic_model.
        """
        ...

    def create_input_model(self, schema: ModelSchema) -> type[Any]:
        """Create Pydantic input model from schema (excludes ID field).

        Input models are used for POST/PUT requests where the ID is
        auto-generated or provided separately in the path.

        Args:
            schema: Model schema containing field definitions.

        Returns:
            Pydantic model class for API request bodies.
        """
        ...

    def create_list_response_model(self, item_model: type[Any]) -> type[Any]:
        """Create paginated list response model.

        Wraps the item model in a list response with pagination metadata.

        Args:
            item_model: Pydantic model for individual items.

        Returns:
            Pydantic model class for paginated list responses.
        """
        ...
