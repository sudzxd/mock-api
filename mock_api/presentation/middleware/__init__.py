"""Middleware (CORS, logging, exception handling, etc.)."""

from __future__ import annotations

from .exception_handlers import setup_exception_handlers

__all__ = ["setup_exception_handlers"]

# TODO: Implement additional middleware
# - CORS middleware
# - Request logging
# - Rate limiting (future)
