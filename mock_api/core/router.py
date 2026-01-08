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
from typing import Annotated, Any, cast

# Third-party
from fastapi import APIRouter as FastAPIRouter
from fastapi import Body, HTTPException, Query
from pydantic import BaseModel, ValidationError, create_model

# Project/local
from ..utils.logger import get_logger
from .constants import (
    API_VERSION_PREFIX,
    DEFAULT_PAGE_NUMBER,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MIN_PAGE_SIZE,
    PRIMARY_KEY_FIELD,
    URL_ID_PATH_SEGMENT,
    URL_PATH_SEPARATOR,
    URL_PLURAL_SUFFIX,
    HTTPStatus,
    ModelName,
    ResponseKey,
    RouteDescription,
)
from .exceptions import InstanceNotFoundError
from .store import DataStore
from .types import ModelSchema, QueryResult

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


class RouterGenerator:
    """Dynamic FastAPI router generator for model schemas.

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
        store: DataStore,
        prefix: str = API_VERSION_PREFIX,
    ) -> None:
        """Initialize the router generator.

        Args:
            schemas: Dictionary of model schemas from parser.
            store: DataStore instance for data operations.
            prefix: API prefix for all routes (default: "/api/v1").

        Example:
            >>> router_gen = RouterGenerator(schemas, store, prefix="/api/v1")
        """
        self.schemas = schemas
        self.store = store
        self.prefix = prefix
        self._router = FastAPIRouter(prefix=prefix)
        self._registry = ModelRegistry()

        # Pre-build all models for O(1) access
        self._build_model_registry()

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
        Time Complexity: O(n * m) where n=models, m=fields per model
        """
        for model_name, schema in self.schemas.items():
            # Response model (all fields)
            response_model = schema.pydantic_model or self._create_response_model(
                schema
            )
            self._registry.register_response_model(model_name, response_model)

            # Input model (no ID)
            input_model = self._create_input_model(schema)
            self._registry.register_input_model(model_name, input_model)

            # List response model (with pagination)
            list_response = self._create_list_response_model(response_model)
            self._registry.register_list_response_model(model_name, list_response)

    def _create_response_model(self, schema: ModelSchema) -> type[BaseModel]:
        """Create Pydantic response model from schema.

        Args:
            schema: Model schema.

        Returns:
            Dynamically created Pydantic model.
        """
        fields: dict[str, tuple[type, Any]] = {}

        for field in schema.fields:
            if field.is_optional:
                field_type: Any = field.type | type(None)
            else:
                field_type: Any = field.type
            fields[field.name] = (field_type, ...)

        model = create_model(schema.name, **fields)  # pyright: ignore[reportCallIssue,reportUnknownVariableType]
        return cast(type[BaseModel], model)

    def _create_input_model(self, schema: ModelSchema) -> type[BaseModel]:
        """Create Pydantic input model from schema (excludes ID).

        Args:
            schema: Model schema.

        Returns:
            Dynamically created Pydantic model for input.
        """
        fields: dict[str, tuple[type, Any]] = {}

        for field in schema.fields:
            # Skip ID field
            if field.name == PRIMARY_KEY_FIELD:
                continue

            if field.is_optional:
                field_type: Any = field.type | type(None)
                default: Any = None
            else:
                field_type: Any = field.type
                default = ...
            fields[field.name] = (field_type, default)

        model = create_model(f"{schema.name}{ModelName.INPUT_SUFFIX}", **fields)  # pyright: ignore[reportCallIssue,reportUnknownVariableType]
        return cast(type[BaseModel], model)

    def _create_list_response_model(
        self, item_model: type[BaseModel]
    ) -> type[BaseModel]:
        """Create paginated list response model.

        Args:
            item_model: Pydantic model for individual items.

        Returns:
            Paginated response model.
        """
        pagination_fields: dict[str, tuple[type, Any]] = {
            ResponseKey.PAGE: (int, ...),
            ResponseKey.PAGE_SIZE: (int, ...),
            ResponseKey.TOTAL_ITEMS: (int, ...),
            ResponseKey.TOTAL_PAGES: (int, ...),
        }

        pagination_model_raw = create_model(  # pyright: ignore[reportCallIssue,reportUnknownVariableType]
            ModelName.PAGINATION_INFO, **pagination_fields
        )
        pagination_model_typed = cast(type[BaseModel], pagination_model_raw)

        list_fields: dict[str, tuple[type, Any]] = {
            ResponseKey.ITEMS: (list[item_model], ...),
            ResponseKey.PAGINATION: (pagination_model_typed, ...),
        }

        model = create_model(  # pyright: ignore[reportCallIssue,reportUnknownVariableType]
            f"{item_model.__name__}{ModelName.LIST_SUFFIX}", **list_fields
        )
        return cast(type[BaseModel], model)

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
        self._add_list_route(model_name, base_path, tag)
        self._add_create_route(model_name, base_path, tag)
        self._add_read_route(model_name, base_path, tag)
        self._add_update_route(model_name, base_path, tag)
        self._add_delete_route(model_name, base_path, tag)

    def _add_list_route(self, model_name: str, base_path: str, tag: str) -> None:
        """Add LIST route (GET /models)."""
        response_model = self._registry.get_list_response_model(model_name)

        @self._router.get(
            base_path,
            response_model=response_model,
            tags=[tag],
            summary=f"List {model_name}s",
            description=RouteDescription.LIST,
        )
        async def list_handler(
            page: int = Query(DEFAULT_PAGE_NUMBER, ge=DEFAULT_PAGE_NUMBER),
            page_size: int = Query(
                DEFAULT_PAGE_SIZE, ge=MIN_PAGE_SIZE, le=MAX_PAGE_SIZE
            ),
        ) -> dict[str, Any]:
            result: QueryResult = self.store.list(
                model_name, page=page, page_size=page_size
            )
            return result.model_dump()

    def _add_create_route(self, model_name: str, base_path: str, tag: str) -> None:
        """Add CREATE route (POST /models)."""
        input_model = self._registry.get_input_model(model_name)
        response_model = self._registry.get_response_model(model_name)

        @self._router.post(
            base_path,
            response_model=response_model,
            status_code=HTTPStatus.CREATED,
            tags=[tag],
            summary=f"Create {model_name}",
            description=RouteDescription.CREATE,
        )
        async def create_handler(
            data: Annotated[dict[str, Any], Body()],
        ) -> dict[str, Any]:
            try:
                validated = input_model.model_validate(data)
                return self.store.create(model_name, validated.model_dump())
            except ValidationError as e:
                raise HTTPException(
                    status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=e.errors()
                ) from None

    def _add_read_route(self, model_name: str, base_path: str, tag: str) -> None:
        """Add READ route (GET /models/{id})."""
        response_model = self._registry.get_response_model(model_name)

        @self._router.get(
            f"{base_path}{URL_PATH_SEPARATOR}{URL_ID_PATH_SEGMENT}",
            response_model=response_model,
            tags=[tag],
            summary=f"Get {model_name} by ID",
            description=RouteDescription.READ,
        )
        async def read_handler(instance_id: int) -> dict[str, Any]:
            instance = self.store.read(model_name, instance_id)
            if not instance:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND, detail=RouteDescription.NOT_FOUND
                )
            return instance

    def _add_update_route(self, model_name: str, base_path: str, tag: str) -> None:
        """Add UPDATE route (PUT /models/{id})."""
        input_model = self._registry.get_input_model(model_name)
        response_model = self._registry.get_response_model(model_name)

        @self._router.put(
            f"{base_path}{URL_PATH_SEPARATOR}{URL_ID_PATH_SEGMENT}",
            response_model=response_model,
            tags=[tag],
            summary=f"Update {model_name}",
            description=RouteDescription.UPDATE,
        )
        async def update_handler(
            instance_id: int, data: Annotated[dict[str, Any], Body()]
        ) -> dict[str, Any]:
            try:
                validated = input_model.model_validate(data)
                return self.store.update(
                    model_name, instance_id, validated.model_dump()
                )
            except ValidationError as e:
                raise HTTPException(
                    status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=e.errors()
                ) from None
            except InstanceNotFoundError:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND, detail=RouteDescription.NOT_FOUND
                ) from None

    def _add_delete_route(self, model_name: str, base_path: str, tag: str) -> None:
        """Add DELETE route (DELETE /models/{id})."""

        @self._router.delete(
            f"{base_path}{URL_PATH_SEPARATOR}{URL_ID_PATH_SEGMENT}",
            status_code=HTTPStatus.NO_CONTENT,
            tags=[tag],
            summary=f"Delete {model_name}",
            description=RouteDescription.DELETE,
        )
        async def delete_handler(instance_id: int) -> None:
            deleted = self.store.delete(model_name, instance_id)
            if not deleted:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND, detail=RouteDescription.NOT_FOUND
                )
