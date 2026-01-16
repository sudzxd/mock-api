"""Data generation domain protocols."""

from __future__ import annotations

from .protocols import GenerationContext, IDataGenerator, IFieldGenerationStrategy

__all__ = ["IFieldGenerationStrategy", "IDataGenerator", "GenerationContext"]
