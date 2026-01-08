"""Data generator for creating realistic mock data based on schemas.

This module provides smart fake data generation using field names and types
to produce realistic test data. It integrates with Faker for common data types
and includes relationship-aware generation.
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
import random
from collections import deque
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

# Third-party
from faker import Faker

# Project/local
from ..utils.logger import get_logger
from .config import Config, get_config
from .constants import (
    CREATED_AT_MAX_DAYS_AGO,
    DEFAULT_FK_RANGE_MAX,
    DEFAULT_FK_RANGE_MIN,
    DEFAULT_GENERATION_COUNT,
    OPTIONAL_FIELD_NULL_PROBABILITY,
    PARAGRAPH_SENTENCE_COUNT,
    PRIMARY_KEY_FIELD,
    RANDOM_FLOAT_MAX,
    RANDOM_FLOAT_MIN,
    RANDOM_FLOAT_PRECISION,
    RANDOM_INT_MAX,
    RANDOM_INT_MIN,
    TEXT_MAX_CHARS,
    TITLE_WORD_COUNT,
    UPDATED_AT_MAX_DAYS_AGO,
    FieldPattern,
)
from .types import FieldSchema, ModelSchema

# =============================================================================
# TYPES & CONSTANTS
# =============================================================================
logger = get_logger(__name__)

# Type alias for field generator functions
FieldGeneratorFunc = Callable[[Faker, int], Any]

# =============================================================================
# PUBLIC API
# =============================================================================


class DataGenerator:
    """Generate realistic mock data based on model schemas.

    Uses field names and types to intelligently generate appropriate fake data.
    Supports relationships and ensures referential integrity.

    Example:
        >>> from mock_api.core.parser import SchemaParser
        >>> parser = SchemaParser()
        >>> schemas = parser.parse_file("models.py")
        >>> generator = DataGenerator(schemas)
        >>> users = generator.generate("User", count=5)
        >>> len(users)
        5
    """

    def __init__(
        self,
        schemas: dict[str, ModelSchema],
        locale: str | None = None,
        seed: int | None = None,
        config: Config | None = None,
    ) -> None:
        """Initialize the data generator.

        Args:
            schemas: Dictionary of model schemas from parser.
            locale: Faker locale for generating localized data (overrides config).
            seed: Random seed for reproducible data generation.
            config: Configuration instance (auto-loads if not provided).

        Example:
            >>> generator = DataGenerator(schemas, locale="en_US", seed=42)
        """
        self.schemas = schemas
        self.config = config or get_config()

        # Use explicit locale if provided, otherwise use config
        final_locale = locale if locale is not None else self.config.locale
        self.faker = Faker(final_locale)

        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)

        # Storage for generated data (for FK resolution)
        self._data: dict[str, list[dict[str, Any]]] = {}

        # Initialize field generators strategy map
        self._pattern_generators = self._build_pattern_generators()
        self._type_generators = self._build_type_generators()

        # Build optimized pattern lookup maps
        # Exact match: O(1) lookup by field name
        self._exact_pattern_map: dict[str, FieldGeneratorFunc] = {
            pattern.value: generator
            for pattern, generator in self._pattern_generators.items()
        }
        # Partial match: patterns for substring matching
        self._partial_patterns = list(self._pattern_generators.items())

        # FK ID cache for faster foreign key resolution
        self._fk_id_cache: dict[str, list[int]] = {}

        logger.debug(f"Initialized generator with {len(schemas)} schema(s)")

    @property
    def data(self) -> dict[str, list[dict[str, Any]]]:
        """Return the generated data for inspection."""
        return self._data

    def generate(
        self, model_name: str, count: int = DEFAULT_GENERATION_COUNT
    ) -> list[dict[str, Any]]:
        """Generate mock data instances for a model.

        Args:
            model_name: Name of the model to generate data for.
            count: Number of instances to generate.

        Returns:
            List of dictionaries representing model instances.

        Raises:
            ValueError: If model_name doesn't exist in schemas.

        Example:
            >>> users = generator.generate("User", count=3)
            >>> len(users)
            3
            >>> "name" in users[0]
            True
        """
        if model_name not in self.schemas:
            raise ValueError(
                f"Model '{model_name}' not found. "
                f"Available models: {', '.join(self.schemas.keys())}"
            )

        schema = self.schemas[model_name]
        logger.info(f"Generating {count} instance(s) of {model_name}")

        instances: list[dict[str, Any]] = []
        for i in range(count):
            instance = self._generate_instance(schema, instance_id=i + 1)
            instances.append(instance)

        # Store generated data for FK resolution in other models
        self._data[model_name] = instances

        logger.debug(f"Generated {len(instances)} {model_name} instance(s)")
        return instances

    def generate_all(
        self, count_per_model: int = DEFAULT_GENERATION_COUNT
    ) -> dict[str, list[dict[str, Any]]]:
        """Generate data for all models in dependency order.

        Ensures models are generated in the correct order to satisfy
        foreign key relationships.

        Args:
            count_per_model: Number of instances to generate per model.

        Returns:
            Dictionary mapping model names to their generated instances.

        Example:
            >>> all_data = generator.generate_all(count_per_model=5)
            >>> "User" in all_data
            True
            >>> "Post" in all_data
            True
        """
        logger.info(f"Generating data for {len(self.schemas)} model(s)")

        # Determine generation order based on dependencies
        generation_order = self._get_generation_order()
        logger.debug(f"Generation order: {' → '.join(generation_order)}")

        result: dict[str, list[dict[str, Any]]] = {}
        for model_name in generation_order:
            result[model_name] = self.generate(model_name, count=count_per_model)

        return result

    # =============================================================================
    # PRIVATE HELPERS: Strategy Pattern - Generator Functions
    # =============================================================================

    def _build_pattern_generators(self) -> dict[FieldPattern, FieldGeneratorFunc]:
        """Build mapping of field patterns to generator functions.

        Uses strategy pattern to avoid long if-else chains.

        Returns:
            Dictionary mapping FieldPattern enum values to generator functions.
        """
        return {
            # Identity
            FieldPattern.ID: lambda _faker, instance_id: instance_id,
            # Contact
            FieldPattern.EMAIL: lambda faker, _: faker.email(),
            FieldPattern.PHONE: lambda faker, _: faker.phone_number(),
            # Names
            FieldPattern.NAME: lambda faker, _: faker.name(),
            FieldPattern.USERNAME: lambda faker, _: faker.user_name(),
            FieldPattern.FIRST_NAME: lambda faker, _: faker.first_name(),
            FieldPattern.FIRSTNAME: lambda faker, _: faker.first_name(),
            FieldPattern.LAST_NAME: lambda faker, _: faker.last_name(),
            FieldPattern.LASTNAME: lambda faker, _: faker.last_name(),
            # Address
            FieldPattern.ADDRESS: lambda faker, _: faker.address(),
            FieldPattern.STREET: lambda faker, _: faker.street_address(),
            FieldPattern.CITY: lambda faker, _: faker.city(),
            FieldPattern.STATE: lambda faker, _: faker.state(),
            FieldPattern.PROVINCE: lambda faker, _: faker.state(),
            FieldPattern.COUNTRY: lambda faker, _: faker.country(),
            FieldPattern.ZIP: lambda faker, _: faker.postcode(),
            FieldPattern.POSTAL: lambda faker, _: faker.postcode(),
            # Timestamps
            FieldPattern.CREATED_AT: lambda _faker, _: datetime.now()
            - timedelta(days=random.randint(0, CREATED_AT_MAX_DAYS_AGO)),
            FieldPattern.CREATEDAT: lambda _faker, _: datetime.now()
            - timedelta(days=random.randint(0, CREATED_AT_MAX_DAYS_AGO)),
            FieldPattern.UPDATED_AT: lambda _faker, _: datetime.now()
            - timedelta(days=random.randint(0, UPDATED_AT_MAX_DAYS_AGO)),
            FieldPattern.UPDATEDAT: lambda _faker, _: datetime.now()
            - timedelta(days=random.randint(0, UPDATED_AT_MAX_DAYS_AGO)),
            # Content
            FieldPattern.TITLE: lambda faker, _: faker.sentence(
                nb_words=TITLE_WORD_COUNT
            ).rstrip("."),
            FieldPattern.CONTENT: lambda faker, _: faker.paragraph(
                nb_sentences=PARAGRAPH_SENTENCE_COUNT
            ),
            FieldPattern.BODY: lambda faker, _: faker.paragraph(
                nb_sentences=PARAGRAPH_SENTENCE_COUNT
            ),
            FieldPattern.DESCRIPTION: lambda faker, _: faker.paragraph(
                nb_sentences=PARAGRAPH_SENTENCE_COUNT
            ),
            FieldPattern.TEXT: lambda faker, _: faker.text(max_nb_chars=TEXT_MAX_CHARS),
            FieldPattern.COMMENT: lambda faker, _: faker.text(
                max_nb_chars=TEXT_MAX_CHARS
            ),
            # URLs
            FieldPattern.URL: lambda faker, _: faker.url(),
            FieldPattern.WEBSITE: lambda faker, _: faker.url(),
        }

    def _build_type_generators(self) -> dict[type, FieldGeneratorFunc]:
        """Build mapping of Python types to generator functions.

        Returns:
            Dictionary mapping types to generator functions.
        """
        return {
            str: lambda faker, _: faker.word(),
            int: lambda _faker, _: random.randint(RANDOM_INT_MIN, RANDOM_INT_MAX),
            float: lambda _faker, _: round(
                random.uniform(RANDOM_FLOAT_MIN, RANDOM_FLOAT_MAX),
                RANDOM_FLOAT_PRECISION,
            ),
            bool: lambda faker, _: faker.boolean(),
            datetime: lambda faker, _: faker.date_time(),
        }

    # =============================================================================
    # PRIVATE HELPERS: Instance Generation
    # =============================================================================

    def _generate_instance(
        self, schema: ModelSchema, instance_id: int
    ) -> dict[str, Any]:
        """Generate a single instance of a model.

        Args:
            schema: The model schema to generate data for.
            instance_id: Unique identifier for this instance.

        Returns:
            Dictionary representing a single model instance.
        """
        instance: dict[str, Any] = {}

        for field in schema.fields:
            instance[field.name] = self._generate_field_value(
                field, schema.name, instance_id
            )

        return instance

    def _generate_field_value(
        self, field: FieldSchema, _model_name: str, instance_id: int
    ) -> Any:
        """Generate a value for a single field.

        Args:
            field: The field schema to generate a value for.
            _model_name: Name of the model (reserved for future use).
            instance_id: ID of the instance being generated.

        Returns:
            Generated value appropriate for the field type.
        """
        # Handle None for optional fields (configurable probability)
        if field.is_optional and random.random() < OPTIONAL_FIELD_NULL_PROBABILITY:
            return None

        # Handle enum fields
        if field.is_enum and field.enum_values:
            return random.choice(field.enum_values)

        # Handle foreign keys
        if field.is_foreign_key and field.related_model:
            return self._generate_foreign_key(field.related_model)

        # Generate by pattern or type using strategy pattern
        return self._generate_by_strategy(field, instance_id)

    def _generate_by_strategy(self, field: FieldSchema, instance_id: int) -> Any:
        """Generate value using optimized strategy pattern.

        Uses O(1) exact match lookup, then O(n) partial matching.

        Args:
            field: The field schema.
            instance_id: Instance identifier.

        Returns:
            Generated value.

        Time Complexity:
        - Best case: O(1) - exact match in hash map
        - Worst case: O(n) - partial match iteration
        """
        field_name_lower = field.name.lower()

        # Try exact pattern match first - O(1) hash map lookup
        if field_name_lower in self._exact_pattern_map:
            return self._exact_pattern_map[field_name_lower](self.faker, instance_id)

        # Try partial pattern match (contains) - O(n) but only if exact fails
        for pattern, generator in self._partial_patterns:
            if pattern.value in field_name_lower:
                return generator(self.faker, instance_id)

        # Fallback to type-based generation - O(1) dict lookup
        type_generator = self._type_generators.get(field.type)
        if type_generator:
            return type_generator(self.faker, instance_id)

        # Ultimate fallback
        return None

    # =============================================================================
    # PRIVATE HELPERS: Foreign Key Generation
    # =============================================================================

    def _generate_foreign_key(self, related_model: str) -> int:
        """Generate a foreign key value with cached ID lookup.

        Uses cached list of available IDs for O(1) random selection.

        Args:
            related_model: Name of the related model.

        Returns:
            ID of a random instance from the related model.

        Time Complexity: O(1) with cache, O(n) on first call per model
        """
        # Check cache first - O(1)
        if related_model in self._fk_id_cache and self._fk_id_cache[related_model]:
            return random.choice(self._fk_id_cache[related_model])

        # If related model data exists, build cache
        if related_model in self._data and self._data[related_model]:
            # Build cache of IDs - O(n) but only once per model
            self._fk_id_cache[related_model] = [
                inst[PRIMARY_KEY_FIELD] for inst in self._data[related_model]
            ]
            return random.choice(self._fk_id_cache[related_model])

        # If no data exists yet, generate it first
        if related_model in self.schemas:
            logger.debug(f"Generating {related_model} data for FK resolution")
            self.generate(related_model, count=DEFAULT_GENERATION_COUNT)
            # Recursively call now that data exists
            return self._generate_foreign_key(related_model)

        # Fallback: return random ID
        logger.warning(f"Could not resolve FK for {related_model}, using random ID")
        return random.randint(DEFAULT_FK_RANGE_MIN, DEFAULT_FK_RANGE_MAX)

    # =============================================================================
    # PRIVATE HELPERS: Dependency Resolution
    # =============================================================================

    def _get_generation_order(self) -> list[str]:
        """Determine generation order using topological sort.

        Uses Kahn's algorithm with deque for O(n + m) complexity where:
        - n = number of models
        - m = number of dependencies

        Returns:
            List of model names in dependency order.

        Time Complexity: O(n + m) - optimal for topological sort
        """
        # Build adjacency list and in-degree count
        dep_graph: dict[str, set[str]] = {name: set() for name in self.schemas}
        in_degree = dict.fromkeys(self.schemas, 0)

        # Build dependency graph
        for model_name, schema in self.schemas.items():
            for field in schema.fields:
                if field.is_foreign_key and field.related_model:
                    # Skip self-referential dependencies
                    if field.related_model == model_name:
                        continue

                    # model_name depends on related_model
                    # So related_model must be generated before model_name
                    if field.related_model in self.schemas:
                        dep_graph[field.related_model].add(model_name)
                        in_degree[model_name] += 1

        # Kahn's algorithm using deque for O(1) append/popleft
        queue = deque([name for name, degree in in_degree.items() if degree == 0])
        ordered: list[str] = []

        while queue:
            # Process node with no dependencies - O(1) popleft
            node = queue.popleft()
            ordered.append(node)

            # Reduce in-degree for dependent models
            for dependent in dep_graph[node]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)  # O(1) append

        # Check for circular dependencies
        if len(ordered) < len(self.schemas):
            remaining = set(self.schemas.keys()) - set(ordered)
            logger.warning(f"Circular dependency detected in models: {remaining}")
            # Add remaining in arbitrary order
            ordered.extend(remaining)

        return ordered
