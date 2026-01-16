"""Schema parser for extracting model definitions from Pydantic files.

This module handles parsing Python files containing Pydantic models and
converting them into an internal schema representation that can be used
for mock data generation.
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
import importlib.util
import inspect
import sys
from collections import defaultdict
from enum import Enum
from pathlib import Path
from typing import Any, get_args

# Third-party
from pydantic import BaseModel

# Project/local
from ...core.constants import (
    DEFAULT_USER_MODEL_NAME,
    FOREIGN_KEY_SUFFIX,
    PRIMARY_KEY_FIELD,
    PYTHON_FILE_EXTENSION,
    SEMANTIC_USER_FIELD_NAMES,
    RelationshipType,
)
from ...core.exceptions import (
    SchemaFileNotFoundError,
    SchemaParseError,
    SchemaValidationError,
)
from ...core.protocols import ISchemaParser
from ...core.types import FieldSchema, ModelSchema, Relationship
from ...utils.logger import get_logger

# =============================================================================
# TYPES & CONSTANTS
# =============================================================================
logger = get_logger(__name__)


# =============================================================================
# PUBLIC API
# =============================================================================


class SchemaParser(ISchemaParser):
    """Parse Pydantic models from Python files into internal schema format.

    Implements ISchemaParser protocol for dependency injection and extensibility.

    Optimized with multiple caching layers for fast lookups:
    - Model name cache: O(1) name resolution
    - Semantic cache: O(1) semantic field resolution
    - Field index: O(1) field name lookups
    - Type index: O(1) type-based queries

    Example:
        >>> parser = SchemaParser()
        >>> schemas = parser.parse_file("models.py")
        >>> "User" in schemas
        True
        >>> schemas["User"].fields[0].name
        'id'
    """

    def __init__(self) -> None:
        """Initialize parser with multi-level caching for performance."""
        # Model name resolution cache
        self._model_name_cache: dict[str, str] = {}
        self._semantic_cache: dict[str, str | None] = {}

        # Field and type indices for fast queries
        self._field_index: dict[str, set[str]] = {}  # {model: {field_names}}
        self._type_index: dict[type, set[str]] = {}  # {type: {model_names}}

    def parse_file(self, file_path: str) -> dict[str, ModelSchema]:
        """Parse all Pydantic models from a Python file.

        Args:
            file_path: Path to Python file containing Pydantic models.

        Returns:
            Dictionary mapping model names to their schemas.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file is not a Python file.

        Example:
            >>> parser = SchemaParser()
            >>> schemas = parser.parse_file("models.py")
            >>> len(schemas)
            2
        """
        path = Path(file_path)

        # Check extension first (before existence check)
        if path.suffix != PYTHON_FILE_EXTENSION:
            raise SchemaValidationError(
                file_path,
                f"Must be a Python file ({PYTHON_FILE_EXTENSION}), got: {path.suffix}",
            )

        if not path.exists():
            raise SchemaFileNotFoundError(file_path)

        # Import the module dynamically
        logger.debug(f"Importing module from {path}")
        module = self._import_module(path)

        # Extract all Pydantic models
        logger.debug("Extracting Pydantic models")
        models = self._extract_pydantic_models(module)
        logger.info(f"Found {len(models)} model(s): {', '.join(models.keys())}")

        # Convert to schemas
        schemas = {
            name: self._model_to_schema(name, model) for name, model in models.items()
        }

        # Build lookup caches for efficient FK resolution
        self._build_model_caches(schemas)

        # Detect relationships between models
        logger.debug("Detecting relationships")
        self._detect_relationships(schemas)

        # Log relationship summary using efficient chain iteration
        total_relationships = sum(
            len(schema.relationships) for schema in schemas.values()
        )
        logger.info(f"Detected {total_relationships} relationship(s)")

        # Log foreign key summary
        fk_fields = [
            field.name
            for schema in schemas.values()
            for field in schema.fields
            if field.is_foreign_key
        ]
        if fk_fields:
            logger.debug(
                f"Foreign keys detected: {', '.join(fk_fields[:5])}"
                + (f" (+{len(fk_fields) - 5} more)" if len(fk_fields) > 5 else "")
            )

        return schemas

    # =============================================================================
    # PUBLIC QUERY METHODS (leveraging indices)
    # =============================================================================

    def get_models_with_field(self, field_name: str) -> set[str]:
        """Get all models that have a specific field.

        Args:
            field_name: Name of the field to search for.

        Returns:
            Set of model names that have this field.

        Time Complexity: O(n) - iterate through field index

        Example:
            >>> parser.get_models_with_field("email")
            {'User', 'Contact'}
        """
        return {
            model for model, fields in self._field_index.items() if field_name in fields
        }

    def get_models_with_type(self, field_type: type) -> set[str]:
        """Get all models that use a specific type.

        Args:
            field_type: Type to search for (e.g., str, int, datetime).

        Returns:
            Set of model names using this type.

        Time Complexity: O(1) - direct index lookup

        Example:
            >>> parser.get_models_with_type(datetime)
            {'Article', 'Post'}
        """
        return self._type_index.get(field_type, set())

    def has_field(self, model_name: str, field_name: str) -> bool:
        """Check if a model has a specific field.

        Args:
            model_name: Name of the model.
            field_name: Name of the field.

        Returns:
            True if model has the field.

        Time Complexity: O(1) - set membership test

        Example:
            >>> parser.has_field("User", "email")
            True
        """
        return field_name in self._field_index.get(model_name, set())

    # =============================================================================
    # PRIVATE HELPERS
    # =============================================================================

    def _import_module(self, path: Path) -> Any:
        """Import a Python file as a module.

        Args:
            path: Path to the Python file.

        Returns:
            The imported module object.
        """
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            raise SchemaParseError(str(path), "Cannot load module specification")

        module = importlib.util.module_from_spec(spec)
        sys.modules[path.stem] = module
        spec.loader.exec_module(module)
        return module

    def _extract_pydantic_models(self, module: Any) -> dict[str, type[BaseModel]]:
        """Extract all Pydantic BaseModel subclasses from a module.

        Args:
            module: The imported Python module.

        Returns:
            Dictionary mapping class names to Pydantic model classes.
        """
        models: dict[str, type[BaseModel]] = {}

        for name, obj in inspect.getmembers(module, inspect.isclass):
            # Check if it's a Pydantic model (subclass of BaseModel)
            # but not BaseModel itself
            if (
                issubclass(obj, BaseModel)
                and obj is not BaseModel
                and obj.__module__ == module.__name__
            ):
                models[name] = obj

        return models

    def _model_to_schema(self, name: str, model: type[BaseModel]) -> ModelSchema:
        """Convert a Pydantic model to internal schema representation.

        Args:
            name: Name of the model class.
            model: The Pydantic model class.

        Returns:
            ModelSchema representing the Pydantic model.
        """
        fields: list[FieldSchema] = []

        # Get model fields from Pydantic
        for field_name, field_info in model.model_fields.items():
            # Extract type information, handling Optional/Union types
            field_type, type_is_optional = self._extract_type_info(
                field_info.annotation
            )

            # Combine with Pydantic's is_required check for full optionality
            is_optional = type_is_optional or (field_info.is_required() is False)

            is_fk = self._is_foreign_key(field_name)

            # Check if field is an enum and extract values
            is_enum = self._is_enum_type(field_type)
            enum_values: list[Any] = []
            if is_enum:
                enum_values = self._extract_enum_values(field_type)

            field_schema = FieldSchema(
                name=field_name,
                type=field_type,
                is_optional=is_optional,
                default=field_info.default if field_info.default is not None else None,
                is_foreign_key=is_fk,
                related_model=None,  # Will be set in relationship detection
                is_enum=is_enum,
                enum_values=enum_values,
            )
            fields.append(field_schema)

        return ModelSchema(name=name, fields=fields, pydantic_model=model)

    def _extract_type_info(self, annotation: Any) -> tuple[type, bool]:
        """Extract type and optionality from a type annotation.

        Handles Optional/Union types by extracting the non-None type
        and detecting if None is in the union.

        Args:
            annotation: Type annotation from Pydantic field.

        Returns:
            Tuple of (base_type, is_optional) where base_type is the
            non-None type and is_optional indicates if None is allowed.

        Example:
            >>> parser = SchemaParser()
            >>> parser._extract_type_info(int | None)
            (int, True)
            >>> parser._extract_type_info(str)
            (str, False)
        """
        field_type: Any = annotation
        is_optional = False

        # Handle Optional types (Union[T, None])
        # Use typing.get_args for robust union detection
        if field_type is not None:
            args = get_args(field_type)

            # Check if None is in the type arguments (Union[T, None] or T | None)
            if args and type(None) in args:
                is_optional = True
                # Extract the non-None type
                non_none_types = [arg for arg in args if arg is not type(None)]
                if non_none_types:
                    field_type = non_none_types[0]

        # Ensure we have a valid type
        if field_type is None:
            field_type = type(None)

        return field_type, is_optional

    def _is_enum_type(self, field_type: type) -> bool:
        """Check if a type is an Enum.

        Args:
            field_type: The type to check.

        Returns:
            True if the type is an Enum subclass.

        Example:
            >>> from enum import Enum
            >>> class Status(str, Enum):
            ...     ACTIVE = "active"
            >>> parser = SchemaParser()
            >>> parser._is_enum_type(Status)
            True
            >>> parser._is_enum_type(str)
            False
        """
        try:
            return inspect.isclass(field_type) and issubclass(field_type, Enum)
        except TypeError:
            # issubclass raises TypeError for non-class types
            return False

    def _extract_enum_values(self, enum_type: type[Enum]) -> list[Any]:
        """Extract all possible values from an Enum.

        Args:
            enum_type: The Enum class to extract values from.

        Returns:
            List of enum member values.

        Example:
            >>> from enum import Enum
            >>> class Status(str, Enum):
            ...     ACTIVE = "active"
            ...     INACTIVE = "inactive"
            >>> parser = SchemaParser()
            >>> parser._extract_enum_values(Status)
            ['active', 'inactive']
        """
        return [member.value for member in enum_type]

    def _is_foreign_key(self, field_name: str) -> bool:
        """Check if a field name indicates a foreign key.

        Args:
            field_name: Name of the field to check.

        Returns:
            True if field ends with FOREIGN_KEY_SUFFIX and is not PRIMARY_KEY_FIELD.

        Example:
            >>> parser = SchemaParser()
            >>> parser._is_foreign_key("author_id")
            True
            >>> parser._is_foreign_key("id")
            False
        """
        return (
            field_name.endswith(FOREIGN_KEY_SUFFIX) and field_name != PRIMARY_KEY_FIELD
        )

    def _detect_relationships(self, schemas: dict[str, ModelSchema]) -> None:
        """Detect and populate relationships between models using optimized algorithms.

        Uses efficient data structures to avoid nested loops:
        1. Build FK index for O(1) lookups
        2. Batch relationship creation
        3. Use defaultdict for inverse relationship grouping

        Args:
            schemas: Dictionary of model schemas to analyze.
        """
        # Build index of foreign keys for efficient processing
        fk_index: dict[str, list[tuple[str, str]]] = defaultdict(list)

        # First pass: index all foreign keys
        for model_name, schema in schemas.items():
            for field_schema in schema.fields:
                if field_schema.is_foreign_key:
                    fk_base = field_schema.name.removesuffix(FOREIGN_KEY_SUFFIX)
                    fk_index[fk_base].append((model_name, field_schema.name))

        # Group inverse relationships to batch-create them
        inverse_relationships: dict[str, list[Relationship]] = defaultdict(list)

        # Second pass: resolve relationships using cached lookups
        for fk_base, fk_fields in fk_index.items():
            related_model = self._find_related_model(fk_base)

            if not related_model:
                continue

            # Process all FK fields for this base name
            for model_name, field_name in fk_fields:
                schema = schemas[model_name]

                # Find the field and set related model
                field_schema = next(
                    (f for f in schema.fields if f.name == field_name), None
                )
                if field_schema:
                    field_schema.related_model = related_model

                    # Add many-to-one relationship
                    relationship = Relationship(
                        field_name=field_name,
                        related_model=related_model,
                        relationship_type=RelationshipType.MANY_TO_ONE,
                    )
                    schema.relationships.append(relationship)

                    # Prepare inverse relationship (batch later)
                    inverse_relationship = Relationship(
                        field_name=f"{model_name.lower()}s",
                        related_model=model_name,
                        relationship_type=RelationshipType.ONE_TO_MANY,
                    )
                    inverse_relationships[related_model].append(inverse_relationship)

        # Third pass: batch-add inverse relationships
        for model_name, relationships in inverse_relationships.items():
            if model_name in schemas:
                schemas[model_name].relationships.extend(relationships)

        # Fourth pass: detect and resolve circular dependencies
        self._resolve_circular_dependencies(schemas)

    def _resolve_circular_dependencies(self, schemas: dict[str, ModelSchema]) -> None:
        """Detect and handle circular dependencies using graph algorithms.

        Uses topological sort to detect cycles and provides warnings
        for complex relationship patterns that might cause issues.

        Args:
            schemas: Dictionary of model schemas to analyze.
        """
        # Build adjacency list for dependency graph
        graph: dict[str, set[str]] = defaultdict(set)

        for model_name, schema in schemas.items():
            for relationship in schema.relationships:
                if relationship.relationship_type == RelationshipType.MANY_TO_ONE:
                    # model_name depends on relationship.related_model
                    graph[model_name].add(relationship.related_model)

        # Detect strongly connected components (cycles)
        cycles = self._find_cycles_dfs(graph)

        if cycles:
            logger.warning(f"Detected {len(cycles)} circular dependency cycles:")
            for cycle in cycles[:3]:  # Log first 3 cycles only
                logger.warning(f"  Cycle: {' -> '.join(cycle)}")
            if len(cycles) > 3:
                logger.warning(f"  ... and {len(cycles) - 3} more cycles")

    def _find_cycles_dfs(self, graph: dict[str, set[str]]) -> list[list[str]]:
        """Find cycles in dependency graph using DFS.

        Uses efficient DFS with color-coding to detect back edges
        which indicate cycles in the dependency graph.

        Args:
            graph: Adjacency list representation of dependencies.

        Returns:
            List of cycles, where each cycle is a list of model names.
        """
        # Color coding: 0=white (unvisited), 1=gray (visiting), 2=black (done)
        colors: dict[str, int] = defaultdict(int)
        cycles: list[list[str]] = []
        path: list[str] = []

        def dfs(node: str) -> None:
            if colors[node] == 1:  # Back edge found - cycle detected
                # Extract cycle from path
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return

            if colors[node] == 2:  # Already processed
                return

            colors[node] = 1  # Mark as visiting
            path.append(node)

            for neighbor in graph.get(node, set()):
                dfs(neighbor)

            path.pop()
            colors[node] = 2  # Mark as done

        # Run DFS from all unvisited nodes
        for node in graph:
            if colors[node] == 0:
                dfs(node)

        return cycles

    def _build_model_caches(self, schemas: dict[str, ModelSchema]) -> None:
        """Build optimized lookup caches and indices.

        Creates O(1) lookup structures:
        - model_name_cache: lowercase -> actual model name
        - semantic_cache: semantic field name -> resolved model
        - field_index: model -> set of field names
        - type_index: type -> set of models using that type

        Args:
            schemas: Dictionary of model schemas.

        Time Complexity: O(n * m) where n=models, m=avg fields per model
        """
        # Clear existing caches
        self._model_name_cache.clear()
        self._semantic_cache.clear()
        self._field_index.clear()
        self._type_index.clear()

        # Build lowercase name -> actual name mapping - O(n)
        for model_name in schemas:
            self._model_name_cache[model_name.lower()] = model_name

        # Pre-compute semantic field resolutions - O(s) where s=semantic names
        for semantic_name in SEMANTIC_USER_FIELD_NAMES:
            if DEFAULT_USER_MODEL_NAME in schemas:
                self._semantic_cache[semantic_name] = DEFAULT_USER_MODEL_NAME
            else:
                self._semantic_cache[semantic_name] = None

        # Build field index - O(n * m)
        for model_name, schema in schemas.items():
            self._field_index[model_name] = {field.name for field in schema.fields}

        # Build type index - O(n * m)
        for model_name, schema in schemas.items():
            for field in schema.fields:
                if field.type not in self._type_index:
                    self._type_index[field.type] = set()
                self._type_index[field.type].add(model_name)

    def _find_related_model(self, fk_base: str) -> str | None:
        """Find the related model name from a foreign key base using cached lookups.

        Uses O(1) cache lookups instead of iterating through all models.

        Args:
            fk_base: Base name of FK field (e.g., "author" from "author_id").

        Returns:
            Name of related model, or None if not found.

        Example:
            >>> parser = SchemaParser()
            >>> parser._find_related_model("user")
            'User'
        """
        # Strategy 1: Direct cache lookup (user → User)
        if fk_base in self._model_name_cache:
            return self._model_name_cache[fk_base]

        # Strategy 2: Capitalized form lookup
        capitalized = fk_base.capitalize()
        if capitalized.lower() in self._model_name_cache:
            return self._model_name_cache[capitalized.lower()]

        # Strategy 3: Semantic name lookup
        return self._semantic_cache.get(fk_base)
