"""Data generator for creating realistic mock data based on schemas.

This module provides a facade/delegate to the data generator implementation.
Delegates to: mock_api/implementations/generation/faker_strategy.py
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Any

# Project/local
from ..implementations.generation import FakerDataGenerator
from .config import Config
from .types import ModelSchema

# =============================================================================
# PUBLIC API
# =============================================================================


class DataGenerator:
    """Facade for data generation that delegates to implementation layer.

    This class provides a stable interface while delegating actual generation
    to the implementation layer, following the facade pattern.
    """

    def __init__(
        self,
        schemas: dict[str, ModelSchema],
        locale: str | None = None,
        seed: int | None = None,
        config: Config | None = None,
    ) -> None:
        """Initialize generator with Faker-based implementation.

        Args:
            schemas: Dictionary of model schemas to generate data for
            locale: Faker locale for localized data (default: en_US)
            seed: Random seed for reproducible generation
            config: Configuration object
        """
        self._generator = FakerDataGenerator(
            schemas=schemas,
            locale=locale,
            seed=seed,
            config=config,
        )

    @property
    def data(self) -> dict[str, list[dict[str, Any]]]:
        """Get all generated data."""
        return self._generator.data

    @property
    def schemas(self) -> dict[str, ModelSchema]:
        """Get schemas used by generator."""
        return self._generator.schemas

    @property
    def faker(self):
        """Get Faker instance for testing."""
        return self._generator.faker

    def generate(self, model_name: str, count: int = 10) -> list[dict[str, Any]]:
        """Generate mock instances for a specific model.

        Args:
            model_name: Name of model to generate data for
            count: Number of instances to generate

        Returns:
            List of generated instance dictionaries

        Raises:
            ModelNotFoundError: If model_name not in schemas
        """
        return self._generator.generate(model_name, count)

    def generate_all(self, count: int = 10) -> dict[str, list[dict[str, Any]]]:
        """Generate data for all models in dependency order.

        Ensures models are generated in the correct order to satisfy
        foreign key relationships.

        Args:
            count: Number of instances to generate per model

        Returns:
            Dictionary mapping model names to lists of instances
        """
        return self._generator.generate_all(count)
