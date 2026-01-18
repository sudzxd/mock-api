"""Repository protocols - data access contracts."""

# =============================================================================
# IMPORTS
# =============================================================================
# Project/local
from .protocols import IBulkRepository, IReadRepository, IWriteRepository

__all__ = [
    "IReadRepository",
    "IWriteRepository",
    "IBulkRepository",
]
