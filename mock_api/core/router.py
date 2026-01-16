"""Dynamic FastAPI router generation from model schemas.

This module generates REST API routes dynamically based on parsed Pydantic
model schemas, providing full CRUD operations with validation and documentation.

Architecture:
- Model registry pattern for type-safe model storage
- Factory pattern for route handler creation
- Protocol-based typing for better type safety

Note: Dynamic model creation with pydantic.create_model() intentionally uses
runtime type construction which cannot be fully validated by static type checkers.
The cast() usage is safe as we control the field definitions.
"""

# pyright: reportArgumentType=false, reportCallIssue=false, reportUnusedFunction=false

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Generic, TypeVar

# Third-party
from fastapi import APIRouter as FastAPIRouter
from pydantic import BaseModel

# Project/local
from ..utils.logger import get_logger
from .config import Config
from .constants import (
    API_VERSION_PREFIX,
    URL_ID_PATH_SEGMENT,
    URL_PATH_SEPARATOR,
    URL_PLURAL_SUFFIX,
    HTTPStatus,
)
from .presentation import RouteHandlerFactory
from .protocols import (
    IDataStore,
    IFilterParser,
    IModelFactory,
    IRouterGenerator,
    ISortParser,
)
from .types import ModelSchema

# =============================================================================
# BASE MODEL CLASSES
# =============================================================================

T = TypeVar("T", bound=BaseModel)


class PaginationInfo(BaseModel):
    """Clean pagination information model."""

    total_items: int
    has_next: bool
    has_prev: bool
    # Strategy-specific fields (optional)
    page: int | None = None
    page_size: int | None = None
    total_pages: int | None = None
    offset: int | None = None
    limit: int | None = None


class ListResponse(BaseModel, Generic[T]):
    """Clean generic list response model."""

    items: list[T]
    pagination: PaginationInfo


# =============================================================================
# TYPES & CONSTANTS
# =============================================================================
logger = get_logger(__name__)


class ModelRegistry:
    """Registry for storing generated Pydantic models with type safety.

    Uses dictionary-based storage for O(1) lookups.
    """

    def __init__(self) -> None:
        """Initialize empty model registry."""
        self._response_models: dict[str, type[BaseModel]] = {}
        self._input_models: dict[str, type[BaseModel]] = {}
        self._list_response_models: dict[str, type[BaseModel]] = {}

    def register_response_model(self, model_name: str, model: type[BaseModel]) -> None:
        """Register a response model."""
        self._response_models[model_name] = model

    def register_input_model(self, model_name: str, model: type[BaseModel]) -> None:
        """Register an input model."""
        self._input_models[model_name] = model

    def register_list_response_model(
        self, model_name: str, model: type[BaseModel]
    ) -> None:
        """Register a list response model."""
        self._list_response_models[model_name] = model

    def get_response_model(self, model_name: str) -> type[BaseModel]:
        """Get response model - O(1) lookup."""
        return self._response_models[model_name]

    def get_input_model(self, model_name: str) -> type[BaseModel]:
        """Get input model - O(1) lookup."""
        return self._input_models[model_name]

    def get_list_response_model(self, model_name: str) -> type[BaseModel]:
        """Get list response model - O(1) lookup."""
        return self._list_response_models[model_name]


# =============================================================================
# PUBLIC API
# =============================================================================


class RouterGenerator(IRouterGenerator):
    """Dynamic FastAPI router generator for model schemas.

    Implements IRouterGenerator protocol for dependency injection and extensibility.

    Generates RESTful CRUD endpoints for each model with:
    - List with pagination (GET /models)
    - Create (POST /models)
    - Read by ID (GET /models/{id})
    - Update by ID (PUT /models/{id})
    - Delete by ID (DELETE /models/{id})

    Uses model registry pattern for type-safe model management.

    Example:
        >>> router_gen = RouterGenerator(schemas, store)
        >>> app_router = router_gen.generate_routes()
        >>> app.include_router(app_router)
    """

    def __init__(
        self,
        schemas: dict[str, ModelSchema],
        store: IDataStore,
        filter_parser: IFilterParser,
        sort_parser: ISortParser,
        model_factory: IModelFactory,
        prefix: str = API_VERSION_PREFIX,
        config: Config | None = None,
    ) -> None:
        """Initialize the router generator.

        Args:
            schemas: Dictionary of model schemas from parser.
            store: Data store implementation for data operations.
            filter_parser: Filter parser implementation for parsing query filters.
            sort_parser: Sort parser implementation for parsing sort parameters.
            model_factory: Model factory implementation for creating Pydantic models.
            prefix: API prefix for all routes (default: "/api/v1").
            config: Configuration instance (auto-loads if not provided).

        Example:
            >>> filter_parser = FilterParser()
            >>> sort_parser = SortParser()
            >>> model_factory = ModelFactory()
            >>> router_gen = RouterGenerator(
            ...     schemas, store, filter_parser, sort_parser, model_factory
            ... )
        """
        self.schemas = schemas
        self.store = store
        self.prefix = prefix
        self._config = config or Config()
        self._router = FastAPIRouter(prefix=prefix)
        self._registry = ModelRegistry()
        self._filter_parser = filter_parser
        self._sort_parser = sort_parser
        self._model_factory = model_factory

        # Pre-build all models for O(1) access
        self._build_model_registry()

        # Initialize handler factory for creating route handlers
        self._handler_factory = RouteHandlerFactory(
            store=store,
            filter_parser=filter_parser,
            sort_parser=sort_parser,
            schemas=schemas,
            config=self._config,
        )

        logger.debug(f"Initialized router with {len(schemas)} schema(s)")

    @property
    def registry(self) -> ModelRegistry:
        """Public access to model registry for testing."""
        return self._registry

    def generate_routes(self) -> FastAPIRouter:
        """Generate FastAPI routes for all models.

        Creates CRUD endpoints for each model in schemas.

        Returns:
            FastAPI APIRouter with all generated routes.

        Example:
            >>> app_router = router_gen.generate_routes()
            >>> len(app_router.routes)
            15  # 5 routes per model × 3 models
        """
        for model_name in self.schemas:
            self._generate_model_routes(model_name)

        logger.info(f"Generated {len(self._router.routes)} route(s)")
        return self._router

    # =============================================================================
    # PRIVATE HELPERS: Model Registry
    # =============================================================================

    def _build_model_registry(self) -> None:
        """Pre-build all Pydantic models and store in registry.

        Builds models upfront for type safety and performance.
        Uses injected ModelFactory for model creation.
        Time Complexity: O(n * m) where n=models, m=fields per model
        """
        for model_name, schema in self.schemas.items():
            # Response model (original Pydantic model from user)
            response_model = self._model_factory.create_response_model(schema)
            self._registry.register_response_model(model_name, response_model)

            # Input model (excludes ID field)
            input_model = self._model_factory.create_input_model(schema)
            self._registry.register_input_model(model_name, input_model)

            # List response model (with pagination)
            list_response = self._model_factory.create_list_response_model(
                response_model
            )
            self._registry.register_list_response_model(model_name, list_response)

    # =============================================================================
    # PRIVATE HELPERS: Route Generation
    # =============================================================================

    def _generate_model_routes(self, model_name: str) -> None:
        """Generate all CRUD routes for a single model.

        Args:
            model_name: Name of the model.
        """
        base_path = f"{URL_PATH_SEPARATOR}{model_name.lower()}{URL_PLURAL_SUFFIX}"
        tag = model_name

        # Routes use registry for type-safe model access
        # Add bulk operations first to avoid path conflicts with /{instance_id}
        self._add_bulk_create_route(model_name, base_path, tag)
        self._add_bulk_update_route(model_name, base_path, tag)
        self._add_bulk_delete_route(model_name, base_path, tag)
        # Regular CRUD operations
        self._add_list_route(model_name, base_path, tag)
        self._add_create_route(model_name, base_path, tag)
        self._add_read_route(model_name, base_path, tag)
        self._add_update_route(model_name, base_path, tag)
        self._add_delete_route(model_name, base_path, tag)

    def _add_list_route(self, model_name: str, base_path: str, tag: str) -> None:
        """Add LIST route (GET /models) with filtering, sorting, and pagination."""
        response_model = self._registry.get_list_response_model(model_name)
        list_handler = self._handler_factory.create_list_handler(model_name)

        self._router.add_api_route(
            base_path,
            list_handler,
            methods=["GET"],
            response_model=response_model,
            tags=[tag],
            summary=f"List {model_name}s",
            description="Supports filtering (?field__operator=value), "
            "sorting (?sort=field,-field2), and dual pagination "
            "(?page=1&page_size=20 or ?offset=0&limit=10).",
        )

    def _add_create_route(self, model_name: str, base_path: str, tag: str) -> None:
        """Add CREATE route (POST /models)."""
        input_model = self._registry.get_input_model(model_name)
        response_model = self._registry.get_response_model(model_name)
        create_handler = self._handler_factory.create_create_handler(
            model_name, input_model
        )

        self._router.add_api_route(
            base_path,
            create_handler,
            methods=["POST"],
            response_model=response_model,
            status_code=HTTPStatus.CREATED,
            tags=[tag],
            summary=f"Create {model_name}",
            description="Create a new instance of the model.",
        )

    def _add_read_route(self, model_name: str, base_path: str, tag: str) -> None:
        """Add READ route (GET /models/{id})."""
        response_model = self._registry.get_response_model(model_name)
        read_handler = self._handler_factory.create_read_handler(model_name)

        self._router.add_api_route(
            f"{base_path}{URL_PATH_SEPARATOR}{URL_ID_PATH_SEGMENT}",
            read_handler,
            methods=["GET"],
            response_model=response_model,
            tags=[tag],
            summary=f"Get {model_name} by ID",
            description="Retrieve a single instance by its ID.",
        )

    def _add_update_route(self, model_name: str, base_path: str, tag: str) -> None:
        """Add UPDATE route (PUT /models/{id})."""
        input_model = self._registry.get_input_model(model_name)
        response_model = self._registry.get_response_model(model_name)
        update_handler = self._handler_factory.create_update_handler(
            model_name, input_model
        )

        self._router.add_api_route(
            f"{base_path}{URL_PATH_SEPARATOR}{URL_ID_PATH_SEGMENT}",
            update_handler,
            methods=["PUT"],
            response_model=response_model,
            tags=[tag],
            summary=f"Update {model_name}",
            description="Update an existing instance by its ID.",
        )

    def _add_delete_route(self, model_name: str, base_path: str, tag: str) -> None:
        """Add DELETE route (DELETE /models/{id})."""
        delete_handler = self._handler_factory.create_delete_handler(model_name)

        self._router.add_api_route(
            f"{base_path}{URL_PATH_SEPARATOR}{URL_ID_PATH_SEGMENT}",
            delete_handler,
            methods=["DELETE"],
            status_code=HTTPStatus.NO_CONTENT,
            tags=[tag],
            summary=f"Delete {model_name}",
            description="Delete an instance by its ID.",
        )

    def _add_bulk_create_route(self, model_name: str, base_path: str, tag: str) -> None:
        """Add BULK CREATE route (POST /models/bulk)."""
        input_model = self._registry.get_input_model(model_name)
        bulk_create_handler = self._handler_factory.create_bulk_create_handler(
            model_name, input_model
        )

        self._router.add_api_route(
            f"{base_path}/bulk",
            bulk_create_handler,
            methods=["POST"],
            status_code=HTTPStatus.CREATED,
            tags=[tag],
            summary=f"Bulk create {model_name}s",
            description="Create multiple instances in a single request. "
            "All items must pass validation.",
        )

    def _add_bulk_update_route(self, model_name: str, base_path: str, tag: str) -> None:
        """Add BULK UPDATE route (PUT /models/bulk)."""
        input_model = self._registry.get_input_model(model_name)
        bulk_update_handler = self._handler_factory.create_bulk_update_handler(
            model_name, input_model
        )

        self._router.add_api_route(
            f"{base_path}/bulk",
            bulk_update_handler,
            methods=["PUT"],
            status_code=HTTPStatus.OK,
            tags=[tag],
            summary=f"Bulk update {model_name}s",
            description="Update multiple instances in a single request. "
            "Each item must include 'id' field.",
        )

    def _add_bulk_delete_route(self, model_name: str, base_path: str, tag: str) -> None:
        """Add BULK DELETE route (DELETE /models/bulk?ids=1,2,3)."""
        bulk_delete_handler = self._handler_factory.create_bulk_delete_handler(
            model_name
        )

        self._router.add_api_route(
            f"{base_path}/bulk",
            bulk_delete_handler,
            methods=["DELETE"],
            status_code=HTTPStatus.OK,
            tags=[tag],
            summary=f"Bulk delete {model_name}s",
            description="Delete multiple instances by IDs. "
            "Provide IDs as comma-separated query parameter: ?ids=1,2,3",
        )
