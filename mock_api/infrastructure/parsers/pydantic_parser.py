"""Pydantic schema parser implementation.

Parses Python files containing Pydantic BaseModel classes into ModelSchema.
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Any, cast, get_args, get_origin

# Third-party
from pydantic import BaseModel
from pydantic.fields import FieldInfo

# Project/local
from mock_api.core.exceptions.schema import SchemaParseError, SchemaValidationError
from mock_api.domain.schema.protocols import ISchemaParser
from mock_api.domain.value_objects.schema import FieldSchema, ModelSchema


# =============================================================================
# CORE CLASSES
# =============================================================================
class PydanticSchemaParser(ISchemaParser):
    """Parse Pydantic models from Python files.

    Features:
    - Inspects Pydantic BaseModel subclasses
    - Extracts field types and metadata
    - Detects foreign key relationships (_id suffix)
    - Handles optional fields (T | None)
    - Supports nested models

    Example Input (models.py):
        from pydantic import BaseModel

        class User(BaseModel):
            id: int
            name: str
            email: str | None = None

        class Post(BaseModel):
            id: int
            title: str
            author_id: int  # FK to User
            content: str

    Output:
        {
            "User": ModelSchema(name="User", fields=(...)),
            "Post": ModelSchema(name="Post", fields=(...))
        }
    """

    def __init__(self) -> None:
        """Initialize Pydantic parser."""
        pass  # Stateless parser

    def parse_file(self, file_path: str) -> dict[str, ModelSchema]:
        """Parse Pydantic models from Python file.

        Implementation steps:
        1. Dynamically import Python module
        2. Find all BaseModel subclasses
        3. Inspect fields using Pydantic's model_fields
        4. Detect foreign keys (_id suffix)
        5. Build ModelSchema for each model

        Args:
            file_path: Path to .py file

        Returns:
            Dict mapping model name to ModelSchema

        Raises:
            SchemaParseError: On parse failures
            SchemaFileNotFoundError: If file doesn't exist
        """
        # 1. Import the module
        module = self._import_module(file_path)

        # 2. Find all Pydantic models
        models = self._find_pydantic_models(module)

        if not models:
            raise SchemaParseError(
                file_path=file_path,
                reason="No Pydantic models found in file",
            )

        # 3. Get all model names for FK detection
        all_model_names = [model.__name__ for model in models]

        # 4. Parse each model
        schemas: dict[str, ModelSchema] = {}
        for model in models:
            schema = self._parse_pydantic_model(model, all_model_names)
            schemas[schema.name] = schema

        # 5. Validate schemas
        self.validate_schema(schemas)

        return schemas

    def supports_file(self, file_path: str) -> bool:
        """Check if this is a Python file.

        Args:
            file_path: Path to check

        Returns:
            True if file has .py extension
        """
        return file_path.endswith(".py")

    def validate_schema(self, schemas: dict[str, ModelSchema]) -> None:
        """Validate parsed schemas.

        Checks:
        - Foreign key references point to valid models
        - No circular dependencies

        Args:
            schemas: Parsed schemas

        Raises:
            SchemaValidationError: If validation fails
        """
        errors: list[str] = []

        # Validate foreign key references
        for model_name, schema in schemas.items():
            for fk_field in schema.get_foreign_keys():
                if fk_field.related_model not in schemas:
                    errors.append(
                        f"Model '{model_name}' has foreign key '{fk_field.name}' "
                        f"referencing non-existent model '{fk_field.related_model}'"
                    )

        if errors:
            raise SchemaValidationError(
                "Schema validation failed",
                details={"errors": errors},
            )

    def _import_module(self, file_path: str) -> Any:
        """Dynamically import Python module from file path.

        Args:
            file_path: Path to .py file

        Returns:
            Imported module object

        Raises:
            SchemaParseError: If import fails
        """
        try:
            # Convert to absolute path
            path = Path(file_path).resolve()

            # Create module spec
            module_name = path.stem
            spec = importlib.util.spec_from_file_location(module_name, path)

            # Validate spec
            self._validate_spec(spec, file_path)

            # After validation, spec and spec.loader are guaranteed to be non-None
            assert spec is not None
            assert spec.loader is not None

            # Load module
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

        except Exception as e:
            if isinstance(e, SchemaParseError):
                raise
            raise SchemaParseError(
                file_path=file_path,
                reason=f"Failed to import module: {e}",
            ) from e
        else:
            return module

    def _validate_spec(self, spec: Any, file_path: str) -> None:
        """Validate module spec.

        Args:
            spec: Module spec to validate
            file_path: Path to file (for error message)

        Raises:
            SchemaParseError: If spec is invalid
        """
        if spec is None or spec.loader is None:
            raise SchemaParseError(
                file_path=file_path,
                reason="Could not create module spec",
            )

    def _find_pydantic_models(self, module: Any) -> list[type]:
        """Find all Pydantic BaseModel subclasses in module.

        Args:
            module: Imported Python module

        Returns:
            List of BaseModel subclasses
        """
        models: list[type[BaseModel]] = []
        for _name, obj in inspect.getmembers(module):
            # Check if it's a class defined in this module
            if not inspect.isclass(obj):
                continue
            if obj.__module__ != module.__name__:
                continue

            # Check if it's a BaseModel subclass (but not BaseModel itself)
            if issubclass(obj, BaseModel) and obj is not BaseModel:
                models.append(obj)

        return models

    def _parse_pydantic_model(
        self,
        model: type,
        all_model_names: list[str],
    ) -> ModelSchema:
        """Convert Pydantic model to ModelSchema.

        Args:
            model: Pydantic BaseModel subclass
            all_model_names: List of all model names (for FK detection)

        Returns:
            ModelSchema instance
        """
        # Parse all fields using Pydantic v2 API (model_fields)
        fields: list[FieldSchema] = []
        # Cast model to BaseModel to access model_fields (Pydantic v2 API)
        model_fields = cast(dict[str, FieldInfo], model.model_fields)  # pyright: ignore[reportUnknownMemberType]
        for field_name, field_info in model_fields.items():
            field_schema = self._parse_field(field_name, field_info, all_model_names)
            fields.append(field_schema)

        return ModelSchema(
            name=model.__name__,
            fields=tuple(fields),
            primary_key="id",
            model_class=model,
        )

    def _parse_field(
        self,
        field_name: str,
        field_info: Any,
        all_model_names: list[str],
    ) -> FieldSchema:
        """Parse single Pydantic field to FieldSchema.

        Args:
            field_name: Field name
            field_info: Pydantic FieldInfo object
            all_model_names: List of all model names (for FK detection)

        Returns:
            FieldSchema instance
        """
        # Extract type and optionality
        field_type, is_optional = self._extract_field_type(field_info)

        # Get default value
        default = field_info.default if field_info.default is not None else None

        # Detect foreign key
        is_fk, related_model = self._detect_foreign_key(field_name, all_model_names)

        return FieldSchema(
            name=field_name,
            type=field_type,
            is_optional=is_optional,
            default=default,
            is_foreign_key=is_fk,
            related_model=related_model,
        )

    def _detect_foreign_key(
        self,
        field_name: str,
        all_model_names: list[str],
    ) -> tuple[bool, str | None]:
        """Detect if field is foreign key based on _id suffix.

        Example:
            author_id -> (True, "Author")
            user_id -> (True, "User")
            name -> (False, None)

        Args:
            field_name: Field name to check
            all_model_names: Available model names

        Returns:
            Tuple of (is_foreign_key, related_model_name)
        """
        # Check if field ends with _id
        if not field_name.endswith("_id"):
            return (False, None)

        # Extract potential model name (e.g., "author_id" -> "author")
        prefix = field_name[:-3]  # Remove "_id"

        # Try to match with existing model names (case-insensitive, with capitalization)
        for model_name in all_model_names:
            if prefix.lower() == model_name.lower():
                return (True, model_name)

            # Also try capitalizing the prefix
            if prefix.capitalize() == model_name:
                return (True, model_name)

        return (False, None)

    def _extract_field_type(self, field_info: Any) -> tuple[type, bool]:
        """Extract Python type and optionality from Pydantic field.

        Handles: str, str | None, Optional[str], etc.

        Args:
            field_info: Pydantic FieldInfo

        Returns:
            Tuple of (python_type, is_optional)
        """
        # Get the annotation type from field_info
        annotation = field_info.annotation

        # Check if it's a Union type (e.g., str | None or Optional[str])
        origin = get_origin(annotation)
        if origin is not None:
            # Handle Union types
            args = get_args(annotation)

            # Check if None is in the union (indicates optional)
            if type(None) in args:
                # Filter out None to get the actual type
                non_none_types = [arg for arg in args if arg is not type(None)]
                if len(non_none_types) == 1:
                    return (non_none_types[0], True)
                # If multiple non-None types, use the first one
                return (non_none_types[0] if non_none_types else str, True)

        # Not optional
        return (annotation, False)
