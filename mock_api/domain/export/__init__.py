"""API collection export domain protocols."""

from __future__ import annotations

from .protocols import ExportConfig, IExportStrategy

__all__ = ["IExportStrategy", "ExportConfig"]
