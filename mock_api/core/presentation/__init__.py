"""Presentation layer for mockapi-server core module.

This module contains HTTP-specific components for creating FastAPI route
handlers, following clean architecture principles.
"""

from .route_handler_factory import RouteHandlerFactory

__all__ = [
    "RouteHandlerFactory",
]
