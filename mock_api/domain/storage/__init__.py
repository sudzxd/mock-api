"""Storage backend domain protocols."""

from __future__ import annotations

from .protocols import IBulkStorageStrategy, IStorageStrategy

__all__ = ["IStorageStrategy", "IBulkStorageStrategy"]
