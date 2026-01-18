"""Exception handler middleware for FastAPI.

Centralizes exception to HTTP status code mapping.
Removes repetitive try-catch blocks from endpoints.
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Third-party
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

# Project/local
from mock_api.core.exceptions import (
    EntityNotFoundError,
    MockAPIError,
    ModelNotFoundError,
    ValidationError,
)
from mock_api.core.utils.logger import get_logger

# =============================================================================
# LOGGER
# =============================================================================
logger = get_logger(__name__)


# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================
def setup_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers.

    Called once at application startup.
    Maps domain exceptions to appropriate HTTP status codes.

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(ModelNotFoundError)
    async def model_not_found_handler(  # pyright: ignore[reportUnusedFunction]
        request: Request,
        exc: ModelNotFoundError,
    ) -> JSONResponse:
        """Handle ModelNotFoundError - 404.

        Args:
            request: FastAPI request
            exc: Exception instance

        Returns:
            JSON response with 404 status
        """
        logger.warning(
            "Model not found",
            extra={"path": request.url.path, "error": str(exc)},
        )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=exc.to_dict(),
        )

    @app.exception_handler(EntityNotFoundError)
    async def entity_not_found_handler(  # pyright: ignore[reportUnusedFunction]
        request: Request,
        exc: EntityNotFoundError,
    ) -> JSONResponse:
        """Handle EntityNotFoundError - 404.

        Args:
            request: FastAPI request
            exc: Exception instance

        Returns:
            JSON response with 404 status
        """
        logger.warning(
            "Entity not found",
            extra={"path": request.url.path, "error": str(exc)},
        )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=exc.to_dict(),
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(  # pyright: ignore[reportUnusedFunction]
        request: Request,
        exc: ValidationError,
    ) -> JSONResponse:
        """Handle ValidationError - 422.

        Args:
            request: FastAPI request
            exc: Exception instance

        Returns:
            JSON response with 422 status
        """
        logger.warning(
            "Validation error",
            extra={"path": request.url.path, "error": str(exc)},
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=exc.to_dict(),
        )

    @app.exception_handler(MockAPIError)
    async def mock_api_error_handler(  # pyright: ignore[reportUnusedFunction]
        request: Request,
        exc: MockAPIError,
    ) -> JSONResponse:
        """Handle generic MockAPIError - 500.

        Catch-all for domain errors not handled by specific handlers.

        Args:
            request: FastAPI request
            exc: Exception instance

        Returns:
            JSON response with 500 status
        """
        logger.error(
            "Mock API error",
            extra={"path": request.url.path, "error": str(exc)},
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=exc.to_dict(),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(  # pyright: ignore[reportUnusedFunction]
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Handle unexpected exceptions - 500.

        Last resort handler for unhandled exceptions.

        Args:
            request: FastAPI request
            exc: Exception instance

        Returns:
            JSON response with 500 status
        """
        logger.error(
            "Unexpected error",
            extra={"path": request.url.path, "error": str(exc)},
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred",
                "details": {"original_error": str(exc)},
            },
        )
