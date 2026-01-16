"""Protocols for data generation strategies.

This module defines the interface for field value generation strategies,
enabling custom data generation logic and provider extensibility.
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import Any, Protocol

# Project/local
from ...core.types import FieldSchema, ModelSchema

# =============================================================================
# PUBLIC API
# =============================================================================


class IFieldGenerationStrategy(Protocol):
    """Protocol for field value generation strategies.

    Current implementations:
        - FakerGenerationStrategy: Pattern and type-based generation using Faker

    Future implementations:
        - CustomProviderStrategy: User-defined Faker providers (Issue #21)
        - DomainSpecificStrategy: Medical, finance, tech providers (Issue #21)
        - SequentialStrategy: Sequential values (1, 2, 3...)
        - FixedValueStrategy: Fixed/constant values

    Design pattern: Chain of Responsibility
        Multiple strategies can be registered. The first strategy that
        `can_generate()` the field will handle generation.

    Example:
        >>> strategy = FakerGenerationStrategy()
        >>> field = FieldSchema(name="email", type=str, ...)
        >>> if strategy.can_generate(field):
        ...     value = strategy.generate(field, context)
        >>> value
        'alice@example.com'
    """

    def can_generate(self, field: FieldSchema) -> bool:
        """Check if this strategy can generate a value for the field.

        Args:
            field: Field schema definition

        Returns:
            True if strategy can handle this field type/pattern

        Example:
            >>> field = FieldSchema(name="email", type=str, ...)
            >>> strategy.can_generate(field)
            True
        """
        ...

    def generate(self, field: FieldSchema, context: GenerationContext) -> Any:
        """Generate a value for the field.

        Args:
            field: Field schema definition
            context: Generation context with schemas, instance counter, etc.

        Returns:
            Generated value of appropriate type

        Raises:
            GenerationError: If value cannot be generated

        Note:
            This method should only be called after `can_generate()` returns True.
        """
        ...


class IDataGenerator(Protocol):
    """Protocol for data generator orchestration.

    Coordinates multiple field generation strategies to generate complete
    model instances.

    Example:
        >>> generator = DataGenerator([faker_strategy, custom_strategy])
        >>> instances = generator.generate("User", count=10)
        >>> len(instances)
        10
    """

    def generate(self, model_name: str, count: int = 10) -> list[dict[str, Any]]:
        """Generate instances for a model.

        Args:
            model_name: Name of model to generate
            count: Number of instances to generate

        Returns:
            List of generated instance dictionaries

        Note:
            Handles foreign key resolution and dependency ordering automatically.
        """
        ...

    def generate_all(self, count: int = 10) -> dict[str, list[dict[str, Any]]]:
        """Generate instances for all models.

        Args:
            count: Number of instances to generate per model

        Returns:
            Dictionary mapping model names to lists of instances

        Example:
            >>> generator.generate_all(count=5)
            {"User": [{...}, ...], "Post": [{...}, ...]}
        """
        ...


class GenerationContext:
    """Context for field generation.

    Provides access to schemas, previously generated data,
    and generation configuration.

    Attributes:
        schemas: All model schemas
        instance_counter: Counter for current instance being generated
        generated_data: Previously generated instances for FK resolution
        config: Generation configuration (locale, seed, etc.)
    """

    def __init__(
        self,
        schemas: dict[str, ModelSchema],
        instance_counter: int,
        generated_data: dict[str, list[dict[str, Any]]],
        config: Any,
    ) -> None:
        self.schemas = schemas
        self.instance_counter = instance_counter
        self.generated_data = generated_data
        self.config = config
