"""Protocols for middleware strategies.

This module defines the interface for HTTP middleware components that
process requests and responses.

TODO: Implement for Issues #13, #12, #6
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from collections.abc import Callable
from typing import Protocol

# Third-party
from fastapi import Request, Response

# =============================================================================
# PUBLIC API
# =============================================================================


class IMiddleware(Protocol):
    """Protocol for middleware components.

    Future implementations:
        - CORSMiddleware: CORS header handling (Issue #13)
        - AuthMiddleware: JWT/OAuth2 authentication simulation (Issue #12)
        - RateLimitMiddleware: Rate limiting (Issue #13)
        - LoggingMiddleware: Request/response logging (Issue #13)
        - ScenarioMiddleware: Error/delay scenario simulation (Issue #6)
        - MetricsMiddleware: Request metrics collection (Issue #52, #53)

    Design pattern: Chain of Responsibility
        Middlewares are chained and process requests/responses in order.

    Example usage (future):
        >>> middleware = CORSMiddleware(allowed_origins=["*"])
        >>> app.add_middleware(middleware)
    """

    async def process(
        self, request: Request, next: Callable[[Request], Response]
    ) -> Response:
        """Process a request through the middleware.

        Args:
            request: Incoming HTTP request
            next: Next handler in the chain

        Returns:
            HTTP response (potentially modified)

        Note:
            Can modify request before calling next(), and/or
            modify response after next() returns.

        Example:
            async def process(self, request, next):
                # Pre-process request
                request.state.start_time = time.time()

                # Call next middleware/handler
                response = await next(request)

                # Post-process response
                duration = time.time() - request.state.start_time
                response.headers["X-Response-Time"] = str(duration)
                return response
        """
        ...
