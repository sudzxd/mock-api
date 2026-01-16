"""Data import/export domain protocols."""

from __future__ import annotations

from .protocols import IDataExporter, IDataImporter, ImportResult

__all__ = ["IDataImporter", "IDataExporter", "ImportResult"]
