"""Custom exceptions for mockapi-server.

This module provides a hierarchy of custom exceptions for better error handling
and more helpful error messages throughout the application.

Exception Hierarchy:
    MockAPIException (base)
    ├── ConfigurationError
    │   ├── ConfigFileNotFoundError
    │   └── ConfigParseError
    ├── SchemaError
    │   ├── SchemaParseError
    │   ├── SchemaFileNotFoundError
    │   └── SchemaValidationError
    ├── ModelNotFoundError
    ├── StoreError
    │   ├── InstanceNotFoundError
    │   ├── DuplicateInstanceError
    │   └── BatchSizeExceededError
    └── InitializationError
        ├── FileExistsError
        └── InvalidProjectNameError

Example:
    >>> from mock_api.core.exceptions import ModelNotFoundError
    >>> raise ModelNotFoundError("User", available_models=["Post", "Comment"])
    ModelNotFoundError: Model 'User' not found.
    Available models: Post, Comment
    Suggestion: Check your model name spelling or ensure the model is
    defined in your schema file.
"""

from __future__ import annotations

# =============================================================================
# BASE EXCEPTION
# =============================================================================


class MockAPIException(Exception):
    """Base exception for all mockapi-server errors.

    All custom exceptions inherit from this base class, making it easy to
    catch any mockapi-server specific error.

    Attributes:
        message: The error message.
        suggestion: Optional helpful suggestion for resolving the error.
    """

    def __init__(self, message: str, suggestion: str | None = None) -> None:
        """Initialize the exception.

        Args:
            message: The error message describing what went wrong.
            suggestion: Optional suggestion for how to fix the error.
        """
        self.message = message
        self.suggestion = suggestion

        # Build full error message
        full_message = message
        if suggestion:
            full_message = f"{message}\nSuggestion: {suggestion}"

        super().__init__(full_message)


# =============================================================================
# CONFIGURATION ERRORS
# =============================================================================


class ConfigurationError(MockAPIException):
    """Base exception for configuration-related errors."""

    pass


class ConfigFileNotFoundError(ConfigurationError):
    """Raised when a configuration file cannot be found.

    Example:
        >>> raise ConfigFileNotFoundError("mockapi-server.yml")
        ConfigFileNotFoundError: Configuration file not found: mockapi-server.yml
    """

    def __init__(self, file_path: str) -> None:
        """Initialize the exception.

        Args:
            file_path: Path to the configuration file that was not found.
        """
        message = f"Configuration file not found: {file_path}"
        suggestion = (
            "Ensure the file exists and the path is correct. "
            "Supported formats: .yml, .yaml, .json"
        )
        super().__init__(message, suggestion)
        self.file_path = file_path


class ConfigParseError(ConfigurationError):
    """Raised when a configuration file cannot be parsed.

    Example:
        >>> raise ConfigParseError("mockapi-server.yml", "Invalid YAML syntax")
        ConfigParseError: Failed to parse configuration file
        'mockapi-server.yml': Invalid YAML syntax
    """

    def __init__(self, file_path: str, reason: str) -> None:
        """Initialize the exception.

        Args:
            file_path: Path to the configuration file.
            reason: The reason why parsing failed.
        """
        message = f"Failed to parse configuration file '{file_path}': {reason}"
        suggestion = "Ensure the file contains valid YAML or JSON syntax."
        super().__init__(message, suggestion)
        self.file_path = file_path
        self.reason = reason


# =============================================================================
# SCHEMA ERRORS
# =============================================================================


class SchemaError(MockAPIException):
    """Base exception for schema-related errors."""

    pass


class SchemaParseError(SchemaError):
    """Raised when a schema file cannot be parsed.

    Example:
        >>> raise SchemaParseError("models.py", "Invalid Python syntax")
        SchemaParseError: Failed to parse schema file 'models.py': Invalid Python syntax
    """

    def __init__(self, file_path: str, reason: str) -> None:
        """Initialize the exception.

        Args:
            file_path: Path to the schema file.
            reason: The reason why parsing failed.
        """
        message = f"Failed to parse schema file '{file_path}': {reason}"
        suggestion = (
            "Ensure the file contains valid Python code with Pydantic models. "
            "Check for syntax errors or import issues."
        )
        super().__init__(message, suggestion)
        self.file_path = file_path
        self.reason = reason


class SchemaFileNotFoundError(SchemaError):
    """Raised when a schema file cannot be found.

    Example:
        >>> raise SchemaFileNotFoundError("models.py")
        SchemaFileNotFoundError: Schema file not found: models.py
    """

    def __init__(self, file_path: str) -> None:
        """Initialize the exception.

        Args:
            file_path: Path to the schema file that was not found.
        """
        message = f"Schema file not found: {file_path}"
        suggestion = "Ensure the file exists and the path is correct."
        super().__init__(message, suggestion)
        self.file_path = file_path


class SchemaValidationError(SchemaError):
    """Raised when schema validation fails.

    Example:
        >>> raise SchemaValidationError("User", "Missing required field 'id'")
        SchemaValidationError: Schema validation failed for model 'User':
        Missing required field 'id'
    """

    def __init__(self, model_name: str, reason: str) -> None:
        """Initialize the exception.

        Args:
            model_name: Name of the model that failed validation.
            reason: The reason why validation failed.
        """
        message = f"Schema validation failed for model '{model_name}': {reason}"
        suggestion = "Ensure your Pydantic model is properly defined."
        super().__init__(message, suggestion)
        self.model_name = model_name
        self.reason = reason


# =============================================================================
# MODEL ERRORS
# =============================================================================


class ModelNotFoundError(MockAPIException):
    """Raised when a model cannot be found in the schema.

    Example:
        >>> raise ModelNotFoundError("User", available_models=["Post", "Comment"])
        ModelNotFoundError: Model 'User' not found.
        Available models: Post, Comment
    """

    def __init__(
        self, model_name: str, available_models: list[str] | None = None
    ) -> None:
        """Initialize the exception.

        Args:
            model_name: Name of the model that was not found.
            available_models: Optional list of available model names.
        """
        if available_models:
            available = ", ".join(available_models)
            message = f"Model '{model_name}' not found.\nAvailable models: {available}"
        else:
            message = f"Model '{model_name}' not found."

        suggestion = (
            "Check your model name spelling or ensure the model is defined "
            "in your schema file."
        )
        super().__init__(message, suggestion)
        self.model_name = model_name
        self.available_models = available_models


# =============================================================================
# STORE ERRORS
# =============================================================================


class StoreError(MockAPIException):
    """Base exception for data store errors."""

    pass


class InstanceNotFoundError(StoreError):
    """Raised when an instance cannot be found in the store.

    Example:
        >>> raise InstanceNotFoundError("User", 999)
        InstanceNotFoundError: User with id=999 not found
    """

    def __init__(self, model_name: str, instance_id: int) -> None:
        """Initialize the exception.

        Args:
            model_name: Name of the model.
            instance_id: ID of the instance that was not found.
        """
        message = f"{model_name} with id={instance_id} not found"
        suggestion = f"Ensure the {model_name} instance exists in the store."
        super().__init__(message, suggestion)
        self.model_name = model_name
        self.instance_id = instance_id


class DuplicateInstanceError(StoreError):
    """Raised when attempting to create a duplicate instance.

    Example:
        >>> raise DuplicateInstanceError("User", 1)
        DuplicateInstanceError: User with id=1 already exists
    """

    def __init__(self, model_name: str, instance_id: int) -> None:
        """Initialize the exception.

        Args:
            model_name: Name of the model.
            instance_id: ID of the duplicate instance.
        """
        message = f"{model_name} with id={instance_id} already exists"
        suggestion = "Use a different ID or update the existing instance instead."
        super().__init__(message, suggestion)
        self.model_name = model_name
        self.instance_id = instance_id


class BatchSizeExceededError(StoreError):
    """Raised when bulk operation batch size exceeds the configured limit.

    Example:
        >>> raise BatchSizeExceededError(1500, 1000)
        BatchSizeExceededError: Batch size 1500 exceeds maximum allowed: 1000
    """

    def __init__(self, batch_size: int, max_batch_size: int) -> None:
        """Initialize the exception.

        Args:
            batch_size: The actual batch size requested.
            max_batch_size: The maximum allowed batch size.
        """
        message = f"Batch size {batch_size} exceeds maximum allowed: {max_batch_size}"
        suggestion = (
            f"Reduce batch size to {max_batch_size} or fewer items, "
            "or increase max_batch_size in configuration."
        )
        super().__init__(message, suggestion)
        self.batch_size = batch_size
        self.max_batch_size = max_batch_size


# =============================================================================
# INITIALIZATION ERRORS
# =============================================================================


class InitializationError(MockAPIException):
    """Base exception for CLI init command errors."""

    pass


class FileExistsError(InitializationError):
    """Raised when files already exist and --force flag is not used.

    Example:
        >>> raise FileExistsError(["models.py", "mockapi-server.yml"])
        FileExistsError: Files already exist: models.py, mockapi-server.yml
    """

    def __init__(self, files: list[str]) -> None:
        """Initialize the exception.

        Args:
            files: List of existing file paths.
        """
        file_list = ", ".join(files)
        message = f"Files already exist: {file_list}"
        suggestion = "Use --force to overwrite existing files or remove them manually."
        super().__init__(message, suggestion)
        self.files = files


class InvalidProjectNameError(InitializationError):
    """Raised when project name contains invalid characters.

    Example:
        >>> raise InvalidProjectNameError("my project!")
        InvalidProjectNameError: Invalid project name: 'my project!'
    """

    def __init__(self, project_name: str) -> None:
        """Initialize the exception.

        Args:
            project_name: The invalid project name.
        """
        message = f"Invalid project name: '{project_name}'"
        suggestion = (
            "Project name must contain only alphanumeric characters, "
            "hyphens, and underscores."
        )
        super().__init__(message, suggestion)
        self.project_name = project_name
