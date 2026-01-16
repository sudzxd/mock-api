"""Route handler factory for creating FastAPI endpoint handlers.

This module extracts route handler creation logic from RouterGenerator,
following the Single Responsibility Principle. The factory creates handler
functions while RouterGenerator focuses on route registration.

Architecture:
- Factory pattern for handler creation
- Protocol-based typing for dependencies
- Clean separation: HTTP logic vs routing logic
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import HTTPException, Query, Request
from pydantic import BaseModel, ValidationError

from ..config import Config
from ..constants import (
    PRIMARY_KEY_FIELD,
    BulkResponseKey,
    HTTPStatus,
    QueryParam,
    RouteDescription,
)
from ..exceptions import InstanceNotFoundError
from ..protocols import IDataStore, IFilterParser, ISortParser
from ..types import ModelSchema, QueryResult


class RouteHandlerFactory:
    """Factory for creating FastAPI route handler functions.

    Extracts handler creation logic from RouterGenerator for better separation
    of concerns. Handlers contain HTTP-specific logic (request parsing,
    validation, error handling) while RouterGenerator focuses on route
    registration.

    Example:
        >>> factory = RouteHandlerFactory(store, filter_parser, sort_parser, ...)
        >>> list_handler = factory.create_list_handler("User")
        >>> router.get("/users")(list_handler)
    """

    def __init__(
        self,
        store: IDataStore,
        filter_parser: IFilterParser,
        sort_parser: ISortParser,
        schemas: dict[str, ModelSchema],
        config: Config,
    ) -> None:
        """Initialize the route handler factory.

        Args:
            store: Data store implementation for data operations.
            filter_parser: Filter parser for parsing query filters.
            sort_parser: Sort parser for parsing sort parameters.
            schemas: Dictionary of model schemas.
            config: Configuration instance.
        """
        self._store = store
        self._filter_parser = filter_parser
        self._sort_parser = sort_parser
        self._schemas = schemas
        self._config = config

    def create_list_handler(
        self, model_name: str
    ) -> Callable[
        [Request, int | None, int | None, int | None, int | None],
        Coroutine[Any, Any, dict[str, Any]],
    ]:
        """Create LIST route handler (GET /models).

        Args:
            model_name: Name of the model.

        Returns:
            Async handler function for list endpoint.
        """
        pagination_config = self._config.pagination

        async def list_handler(
            request: Request,
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
            filters = self._filter_parser.parse_params(
                request.query_params, model_name, self._schemas[model_name]
            )
            sort_by = self._sort_parser.parse_param(
                request.query_params.get(QueryParam.SORT),
                model_name,
                self._schemas[model_name],
            )

            result: QueryResult = self._store.list(
                model_name,
                page=page,
                page_size=page_size,
                offset=offset,
                limit=limit,
                filters=filters,
                sort_by=sort_by,
            )
            return result.model_dump()

        return list_handler

    def create_create_handler(
        self, model_name: str, input_model: type[BaseModel]
    ) -> Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]:
        """Create CREATE route handler (POST /models).

        Args:
            model_name: Name of the model.
            input_model: Pydantic model for input validation.

        Returns:
            Async handler function for create endpoint.
        """

        async def create_handler(data: dict[str, Any]) -> dict[str, Any]:
            try:
                validated = input_model.model_validate(data)
                return self._store.create(model_name, validated.model_dump())
            except ValidationError as e:
                raise HTTPException(
                    status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=e.errors()
                ) from None

        # Override annotation for OpenAPI
        create_handler.__annotations__["data"] = input_model
        return create_handler

    def create_read_handler(
        self, model_name: str
    ) -> Callable[[int], Coroutine[Any, Any, dict[str, Any]]]:
        """Create READ route handler (GET /models/{id}).

        Args:
            model_name: Name of the model.

        Returns:
            Async handler function for read endpoint.
        """

        async def read_handler(instance_id: int) -> dict[str, Any]:
            instance = self._store.read(model_name, instance_id)
            if not instance:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND, detail=RouteDescription.NOT_FOUND
                )
            return instance

        return read_handler

    def create_update_handler(
        self, model_name: str, input_model: type[BaseModel]
    ) -> Callable[[int, dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]:
        """Create UPDATE route handler (PUT /models/{id}).

        Args:
            model_name: Name of the model.
            input_model: Pydantic model for input validation.

        Returns:
            Async handler function for update endpoint.
        """

        async def update_handler(
            instance_id: int, data: dict[str, Any]
        ) -> dict[str, Any]:
            try:
                validated = input_model.model_validate(data)
                return self._store.update(
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

        # Override annotation for OpenAPI
        update_handler.__annotations__["data"] = input_model
        return update_handler

    def create_delete_handler(
        self, model_name: str
    ) -> Callable[[int], Coroutine[Any, Any, None]]:
        """Create DELETE route handler (DELETE /models/{id}).

        Args:
            model_name: Name of the model.

        Returns:
            Async handler function for delete endpoint.
        """

        async def delete_handler(instance_id: int) -> None:
            deleted = self._store.delete(model_name, instance_id)
            if not deleted:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND, detail=RouteDescription.NOT_FOUND
                )

        return delete_handler

    def create_bulk_create_handler(
        self, model_name: str, input_model: type[BaseModel]
    ) -> Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]:
        """Create BULK CREATE route handler (POST /models/bulk).

        Args:
            model_name: Name of the model.
            input_model: Pydantic model for input validation.

        Returns:
            Async handler function for bulk create endpoint.
        """

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
            return self._store.bulk_create(
                model_name,
                validated_items,
                allow_partial=allow_partial,
                max_batch_size=max_batch_size,
            )

        # Override annotation for OpenAPI
        bulk_create_handler.__annotations__["request_data"] = dict[str, Any]
        return bulk_create_handler

    def create_bulk_update_handler(
        self, model_name: str, input_model: type[BaseModel]
    ) -> Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]:
        """Create BULK UPDATE route handler (PUT /models/bulk).

        Args:
            model_name: Name of the model.
            input_model: Pydantic model for input validation.

        Returns:
            Async handler function for bulk update endpoint.
        """

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
                return self._store.bulk_update(
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
        return bulk_update_handler

    def create_bulk_delete_handler(
        self, model_name: str
    ) -> Callable[[str], Coroutine[Any, Any, dict[str, Any]]]:
        """Create BULK DELETE route handler (DELETE /models/bulk?ids=1,2,3).

        Args:
            model_name: Name of the model.

        Returns:
            Async handler function for bulk delete endpoint.
        """

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
                return self._store.bulk_delete(
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

        return bulk_delete_handler
