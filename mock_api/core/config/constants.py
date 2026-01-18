"""Core application constants.

Defines constant values used across the application for pagination,
HTTP defaults, and other cross-cutting concerns.

Note: MAX_PAGE_SIZE is defined in domain layer (domain.value_objects.query)
to maintain zero dependencies in domain. Re-exported here for convenience.
"""

from __future__ import annotations

# =============================================================================
# PAGINATION
# =============================================================================
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
# MAX_PAGE_SIZE re-exported from domain.value_objects.query above

# =============================================================================
# HTTP
# =============================================================================
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 3000
API_PREFIX = "/api/v1"
