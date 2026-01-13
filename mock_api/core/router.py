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
from typing import Any, cast

# Third-party
from fastapi import APIRouter as FastAPIRouter
from fastapi import HTTPException, Query, Request
from pydantic import BaseModel, ValidationError, create_model
from starlette.datastructures import QueryParams

# Project/local
from ..utils.logger import get_logger
from .config import Config
from .constants import (
    API_VERSION_PREFIX,
    BOOLEAN_FALSE_VALUES,
    BOOLEAN_TRUE_VALUES,
    FILTER_OPERATOR_DELIMITER,
    IN_OPERATOR_DELIMITER,
    PRIMARY_KEY_FIELD,
    SORT_DESC_PREFIX,
    SORT_FIELD_DELIMITER,
    URL_ID_PATH_SEGMENT,
    URL_PATH_SEPARATOR,
    URL_PLURAL_SUFFIX,
    BulkResponseKey,
    FilterOperator,
    HTTPStatus,
    ModelName,
    QueryParam,
    ResponseKey,
    RouteDescription,
    SortDirection,
)
from .exceptions import InstanceNotFoundError
from .store import DataStore
from .types import FieldSchema, FilterSpec, ModelSchema, QueryResult, SortSpec

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
        config: Config | None = None,
    ) -> None:
        """Initialize the router generator.

        Args:
            schemas: Dictionary of model schemas from parser.
            store: DataStore instance for data operations.
            prefix: API prefix for all routes (default: "/api/v1").
            config: Configuration instance (auto-loads if not provided).

        Example:
            >>> router_gen = RouterGenerator(schemas, store, prefix="/api/v1")
        """
        self.schemas = schemas
        self.store = store
        self.prefix = prefix
        self._config = config or Config()
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
        pagination_fields: dict[str, tuple[Any, Any]] = {
            # Common fields (always present)
            ResponseKey.TOTAL_ITEMS: (int, ...),
            ResponseKey.HAS_NEXT: (bool, ...),
            ResponseKey.HAS_PREV: (bool, ...),
            # Page-based fields (optional - None if using offset strategy)
            ResponseKey.PAGE: (int | None, None),
            ResponseKey.PAGE_SIZE: (int | None, None),
            ResponseKey.TOTAL_PAGES: (int | None, None),
            # Offset-based fields (optional - None if using page strategy)
            ResponseKey.OFFSET: (int | None, None),
            ResponseKey.LIMIT: (int | None, None),
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
        pagination_config = self._config.pagination

        @self._router.get(
            base_path,
            response_model=response_model,
            tags=[tag],
            summary=f"List {model_name}s",
            description="Supports filtering (?field__operator=value), "
            "sorting (?sort=field,-field2), and dual pagination "
            "(?page=1&page_size=20 or ?offset=0&limit=10).",
        )
        async def list_handler(
            request: Request,
            # Page-based params
            page: int | None = Query(
                None,
                ge=1,
                description="Page number (1-indexed) for page-based pagination",
            ),
            page_size: int | None = Query(
                None,
                ge=pagination_config.min_page_size,
                le=pagination_config.max_page_size,
                description="Items per page for page-based pagination",
            ),
            # Offset-based params
            offset: int | None = Query(
                None,
                ge=0,
                description="Starting offset (0-indexed) for offset-based pagination",
            ),
            limit: int | None = Query(
                None,
                ge=pagination_config.min_limit,
                le=pagination_config.max_limit,
                description="Maximum items to return for offset-based pagination",
            ),
        ) -> dict[str, Any]:
            # Parse filters and sort from query params
            filters = self._parse_filter_params(
                request.query_params, model_name, self.schemas[model_name]
            )
            sort_by = self._parse_sort_param(
                request.query_params.get(QueryParam.SORT),
                model_name,
                self.schemas[model_name],
            )

            result: QueryResult = self.store.list(
                model_name,
                page=page,
                page_size=page_size,
                offset=offset,
                limit=limit,
                filters=filters,
                sort_by=sort_by,
            )
            return result.model_dump()

    def _add_create_route(self, model_name: str, base_path: str, tag: str) -> None:
        """Add CREATE route (POST /models)."""
        input_model = self._registry.get_input_model(model_name)
        response_model = self._registry.get_response_model(model_name)

        # Create handler without Body() annotation since we'll specify schema manually
        async def create_handler(data: dict[str, Any]) -> dict[str, Any]:
            try:
                validated = input_model.model_validate(data)
                return self.store.create(model_name, validated.model_dump())
            except ValidationError as e:
                raise HTTPException(
                    status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=e.errors()
                ) from None

        # Override the function's annotation with the actual input model
        # This allows FastAPI to generate proper OpenAPI schema
        create_handler.__annotations__["data"] = input_model

        self._router.add_api_route(
            base_path,
            create_handler,
            methods=["POST"],
            response_model=response_model,
            status_code=HTTPStatus.CREATED,
            tags=[tag],
            summary=f"Create {model_name}",
            description=RouteDescription.CREATE,
        )

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

        async def update_handler(
            instance_id: int, data: dict[str, Any]
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

        # Override the function's annotation with the actual input model
        # This allows FastAPI to generate proper OpenAPI schema
        update_handler.__annotations__["data"] = input_model

        self._router.add_api_route(
            f"{base_path}{URL_PATH_SEPARATOR}{URL_ID_PATH_SEGMENT}",
            update_handler,
            methods=["PUT"],
            response_model=response_model,
            tags=[tag],
            summary=f"Update {model_name}",
            description=RouteDescription.UPDATE,
        )

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

    def _add_bulk_create_route(self, model_name: str, base_path: str, tag: str) -> None:
        """Add BULK CREATE route (POST /models/bulk)."""
        input_model = self._registry.get_input_model(model_name)

        async def bulk_create_handler(request_data: dict[str, Any]) -> dict[str, Any]:
            # Extract data array
            if BulkResponseKey.DATA not in request_data:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Missing required field '{BulkResponseKey.DATA}'",
                )

            data_list = request_data[BulkResponseKey.DATA]

            # Validate batch size
            max_batch_size = self._config.bulk_operations.max_batch_size
            if len(data_list) > max_batch_size:
                detail = (
                    f"Batch size {len(data_list)} exceeds maximum: {max_batch_size}"
                )
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=detail,
                )

            # Validate each item
            validated_items: list[dict[str, Any]] = []
            for idx, item in enumerate(data_list):
                try:
                    validated = input_model.model_validate(item)
                    validated_items.append(validated.model_dump())
                except ValidationError as e:
                    raise HTTPException(
                        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                        detail={
                            "message": f"Validation failed for item at index {idx}",
                            "errors": e.errors(),
                        },
                    ) from None

            # Perform bulk create
            allow_partial = self._config.bulk_operations.allow_partial
            return self.store.bulk_create(
                model_name,
                validated_items,
                allow_partial=allow_partial,
                max_batch_size=max_batch_size,
            )

        # Override annotation for OpenAPI
        bulk_create_handler.__annotations__["request_data"] = dict[str, Any]

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

        async def bulk_update_handler(request_data: dict[str, Any]) -> dict[str, Any]:
            # Extract data array
            if BulkResponseKey.DATA not in request_data:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Missing required field '{BulkResponseKey.DATA}'",
                )

            data_list = request_data[BulkResponseKey.DATA]

            # Validate batch size
            max_batch_size = self._config.bulk_operations.max_batch_size
            if len(data_list) > max_batch_size:
                detail = (
                    f"Batch size {len(data_list)} exceeds maximum: {max_batch_size}"
                )
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=detail,
                )

            # Validate each item has ID and valid fields
            validated_items: list[dict[str, Any]] = []
            for idx, item in enumerate(data_list):
                if PRIMARY_KEY_FIELD not in item:
                    raise HTTPException(
                        status_code=HTTPStatus.BAD_REQUEST,
                        detail=f"Missing '{PRIMARY_KEY_FIELD}' for item at index {idx}",
                    )

                try:
                    # Validate non-ID fields
                    item_copy = item.copy()
                    instance_id = item_copy.pop(PRIMARY_KEY_FIELD)
                    validated = input_model.model_validate(item_copy)
                    validated_data = validated.model_dump()
                    validated_data[PRIMARY_KEY_FIELD] = instance_id
                    validated_items.append(validated_data)
                except ValidationError as e:
                    raise HTTPException(
                        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                        detail={
                            "message": f"Validation failed for item at index {idx}",
                            "errors": e.errors(),
                        },
                    ) from None

            # Perform bulk update
            allow_partial = self._config.bulk_operations.allow_partial
            try:
                return self.store.bulk_update(
                    model_name,
                    validated_items,
                    allow_partial=allow_partial,
                    max_batch_size=max_batch_size,
                )
            except InstanceNotFoundError as e:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=str(e),
                ) from None

        # Override annotation for OpenAPI
        bulk_update_handler.__annotations__["request_data"] = dict[str, Any]

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

        @self._router.delete(
            f"{base_path}/bulk",
            status_code=HTTPStatus.OK,
            tags=[tag],
            summary=f"Bulk delete {model_name}s",
            description="Delete multiple instances by IDs. "
            "Provide IDs as comma-separated query parameter: ?ids=1,2,3",
        )
        async def bulk_delete_handler(
            ids: str = Query(..., description="Comma-separated list of IDs to delete"),
        ) -> dict[str, Any]:
            # Parse IDs
            try:
                id_list = [int(id_str.strip()) for id_str in ids.split(",")]
            except ValueError as e:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail="Invalid ID format. IDs must be integers.",
                ) from e

            # Validate batch size
            max_batch_size = self._config.bulk_operations.max_batch_size
            if len(id_list) > max_batch_size:
                detail = f"Batch size {len(id_list)} exceeds maximum: {max_batch_size}"
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=detail,
                )

            # Perform bulk delete
            allow_partial = self._config.bulk_operations.allow_partial
            try:
                return self.store.bulk_delete(
                    model_name,
                    id_list,
                    allow_partial=allow_partial,
                    max_batch_size=max_batch_size,
                )
            except InstanceNotFoundError as e:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=str(e),
                ) from None

    # =============================================================================
    # FILTER PARSING
    # =============================================================================

    def _parse_filter_params(
        self,
        query_params: QueryParams,
        model_name: str,
        schema: ModelSchema,
    ) -> list[FilterSpec]:
        """Parse filter query parameters into FilterSpec objects.

        Args:
            query_params: Raw query parameters from request.
            model_name: Name of the model being queried.
            schema: Model schema for field validation.

        Returns:
            List of filter specifications.

        Raises:
            HTTPException: If too many filters or validation fails.
        """
        filters: list[FilterSpec] = []
        reserved_params = {
            QueryParam.PAGE,
            QueryParam.PAGE_SIZE,
            QueryParam.OFFSET,
            QueryParam.LIMIT,
            QueryParam.SORT,
        }

        for param_name, param_value in query_params.items():
            if param_name in reserved_params:
                continue

            filter_spec = self._parse_single_filter_param(
                param_name, param_value, model_name, schema
            )
            filters.append(filter_spec)

        # Check max filters limit
        max_filters = self._config.filter_sort.max_filters
        if len(filters) > max_filters:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Too many filters. Maximum allowed: {max_filters}",
            )

        return filters

    def _parse_single_filter_param(
        self, param_name: str, param_value: str, model_name: str, schema: ModelSchema
    ) -> FilterSpec:
        """Parse a single filter parameter into FilterSpec.

        Args:
            param_name: Query parameter name (e.g., "age__gte" or "name").
            param_value: Query parameter value.
            model_name: Name of the model being queried.
            schema: Model schema for field validation.

        Returns:
            FilterSpec object.

        Raises:
            HTTPException: If field, operator, or value is invalid.
        """
        # Parse field__operator or field (implicit eq)
        if FILTER_OPERATOR_DELIMITER in param_name:
            field_name, operator_str = param_name.split(FILTER_OPERATOR_DELIMITER, 1)
        else:
            field_name, operator_str = param_name, FilterOperator.EQ

        # Validate and get field schema
        field_schema = self._validate_filter_field(field_name, model_name, schema)

        # Validate and get operator enum
        operator = self._validate_filter_operator(operator_str)

        # Coerce value based on field type
        try:
            coerced_value = self._coerce_filter_value(
                param_value, field_schema, operator
            )
        except ValueError as e:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Invalid value for {field_name}: {str(e)}",
            ) from e

        return FilterSpec(field=field_name, operator=operator, value=coerced_value)

    def _validate_filter_field(
        self, field_name: str, model_name: str, schema: ModelSchema
    ) -> FieldSchema:
        """Validate filter field exists in schema.

        Args:
            field_name: Name of the field to validate.
            model_name: Name of the model being queried.
            schema: Model schema.

        Returns:
            FieldSchema for the validated field.

        Raises:
            HTTPException: If field doesn't exist.
        """
        field_map = {f.name: f for f in schema.fields}
        if field_name not in field_map:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Invalid filter field '{field_name}' for {model_name}. "
                f"Available fields: {', '.join(field_map.keys())}",
            )
        return field_map[field_name]

    def _validate_filter_operator(self, operator_str: str) -> FilterOperator:
        """Validate filter operator is supported.

        Args:
            operator_str: Operator string (e.g., "gte", "contains").

        Returns:
            FilterOperator enum value.

        Raises:
            HTTPException: If operator is invalid.
        """
        try:
            return FilterOperator(operator_str)
        except ValueError as e:
            valid_ops = ", ".join([op.value for op in FilterOperator])
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Invalid filter operator '{operator_str}'. "
                f"Valid operators: {valid_ops}",
            ) from e

    def _coerce_filter_value(
        self, value: str, field_schema: FieldSchema, operator: FilterOperator
    ) -> Any:
        """Coerce string query parameter to field type.

        Args:
            value: Raw string value from query parameter.
            field_schema: Schema of the field being filtered.
            operator: Filter operator being used.

        Returns:
            Type-coerced value.

        Raises:
            ValueError: If coercion fails.
        """
        # Handle null explicitly
        if value.lower() == "null":
            return None

        # Handle IN operator - split comma-separated values
        if operator == FilterOperator.IN:
            value_list = [v.strip() for v in value.split(IN_OPERATOR_DELIMITER)]
            return [self._coerce_single_value(v, field_schema) for v in value_list]

        return self._coerce_single_value(value, field_schema)

    def _coerce_single_value(self, value: str, field_schema: FieldSchema) -> Any:
        """Coerce a single value based on field type.

        Args:
            value: Raw string value.
            field_schema: Schema of the field.

        Returns:
            Type-coerced value.

        Raises:
            ValueError: If coercion fails.
        """
        field_type = field_schema.type

        # String - passthrough
        if field_type is str:
            return value

        # Boolean
        if field_type is bool:
            if value.lower() in BOOLEAN_TRUE_VALUES:
                return True
            if value.lower() in BOOLEAN_FALSE_VALUES:
                return False
            raise ValueError(f"Cannot convert '{value}' to bool")

        # Integer
        if field_type is int:
            return int(value)

        # Float
        if field_type is float:
            return float(value)

        # Datetime
        if field_type.__name__ == "datetime":
            from datetime import datetime

            return datetime.fromisoformat(value)

        # Date
        if field_type.__name__ == "date":
            from datetime import date

            return date.fromisoformat(value)

        # Enum
        if field_schema.is_enum:
            # For int-based enums (e.g., Priority(int, Enum)), convert to int
            # For str-based enums (e.g., Status(str, Enum)), keep as string
            # Note: field_schema.enum_values contains actual values
            enum_type = field_type
            if issubclass(enum_type, int) and not issubclass(enum_type, bool):
                # Int-based enum - convert string to int
                try:
                    int_value = int(value)
                except ValueError:
                    valid_values = ", ".join(str(v) for v in field_schema.enum_values)
                    raise ValueError(
                        f"Invalid value '{value}' for int-based enum. "
                        f"Valid values: {valid_values}"
                    ) from None
                # Validate the int is a valid enum value
                if int_value not in field_schema.enum_values:
                    valid_values = ", ".join(str(v) for v in field_schema.enum_values)
                    raise ValueError(
                        f"Invalid enum value '{int_value}'. "
                        f"Valid values: {valid_values}"
                    )
                return int_value

            # String-based enum or other - keep as string
            enum_values_str = [str(v) for v in field_schema.enum_values]
            if value not in enum_values_str:
                raise ValueError(
                    f"Invalid enum value '{value}'. "
                    f"Valid values: {', '.join(enum_values_str)}"
                )
            return value

        # Default - try direct conversion
        return field_type(value)

    # =============================================================================
    # SORT PARSING
    # =============================================================================

    def _parse_sort_param(
        self,
        sort_value: str | None,
        model_name: str,
        schema: ModelSchema,
    ) -> list[SortSpec]:
        """Parse sort query parameter into SortSpec objects.

        Args:
            sort_value: Sort parameter value (e.g., "-created_at,name").
            model_name: Name of the model being queried.
            schema: Model schema for field validation.

        Returns:
            List of sort specifications.

        Raises:
            HTTPException: If too many sort fields or validation fails.
        """
        if not sort_value:
            return []

        # Parse comma-separated fields
        field_specs = [f.strip() for f in sort_value.split(SORT_FIELD_DELIMITER)]
        sort_specs = [
            self._parse_single_sort_field(field_spec, model_name, schema)
            for field_spec in field_specs
        ]

        # Check max sort fields limit
        max_sort_fields = self._config.filter_sort.max_sort_fields
        if len(sort_specs) > max_sort_fields:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Too many sort fields. Maximum allowed: {max_sort_fields}",
            )

        return sort_specs

    def _parse_single_sort_field(
        self, field_spec: str, model_name: str, schema: ModelSchema
    ) -> SortSpec:
        """Parse a single sort field specification.

        Args:
            field_spec: Field specification (e.g., "-created_at" or "name").
            model_name: Name of the model being queried.
            schema: Model schema for field validation.

        Returns:
            SortSpec object.

        Raises:
            HTTPException: If field is invalid.
        """
        # Check for descending prefix
        if field_spec.startswith(SORT_DESC_PREFIX):
            direction = SortDirection.DESC
            field_name = field_spec[1:]
        else:
            direction = SortDirection.ASC
            field_name = field_spec

        # Validate field exists
        self._validate_sort_field(field_name, model_name, schema)

        return SortSpec(field=field_name, direction=direction)

    def _validate_sort_field(
        self, field_name: str, model_name: str, schema: ModelSchema
    ) -> None:
        """Validate sort field exists in schema.

        Args:
            field_name: Name of the field to validate.
            model_name: Name of the model being queried.
            schema: Model schema.

        Raises:
            HTTPException: If field doesn't exist.
        """
        field_names = [f.name for f in schema.fields]
        if field_name not in field_names:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Invalid sort field '{field_name}' for {model_name}. "
                f"Available fields: {', '.join(field_names)}",
            )
