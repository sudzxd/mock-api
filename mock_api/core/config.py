"""Configuration management for mockapi-server.

This module provides centralized configuration management with support for:
- Default values
- Configuration files (YAML/JSON)
- Environment variables (highest priority)

Usage:
    from mock_api.core.config import get_config

    config = get_config()
    print(config.port)  # 3000

    # Load from file
    config = get_config(config_file="mockapi-server.yml")

    # Override with env vars
    # export MOCK_API_PORT=8000
    config = get_config()  # port will be 8000
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
import json
import logging
import os
from pathlib import Path
from typing import Any

# Third-party
from pydantic import BaseModel, Field, field_validator

# Local
from mock_api.core.constants import (
    CONFIG_FILE_NAMES,
    DEFAULT_AUTO_RELOAD,
    DEFAULT_CORS_ENABLED,
    DEFAULT_CORS_ORIGINS,
    DEFAULT_HOST,
    DEFAULT_LIMIT,
    DEFAULT_LOG_LEVEL,
    DEFAULT_PAGE_SIZE,
    DEFAULT_PORT,
    DEFAULT_SEED_COUNT,
    DEFAULT_STRICT_MODE,
    ENV_VAR_PREFIX,
    MAX_LIMIT,
    MAX_PAGE_SIZE,
    MAX_PORT,
    MAX_SEED_COUNT,
    MIN_LIMIT,
    MIN_PAGE_SIZE,
    MIN_PORT,
    MIN_SEED_COUNT,
    BooleanValue,
    ConfigField,
    FileExtension,
    LogLevel,
    PaginationStrategy,
)
from mock_api.core.exceptions import ConfigFileNotFoundError, ConfigParseError
from mock_api.utils.logger import configure_logging

# =============================================================================
# CONFIGURATION SCHEMA
# =============================================================================


class PaginationConfig(BaseModel):
    """Pagination configuration schema.

    Attributes:
        strategy: Default pagination strategy ("page" or "offset").
        default_page_size: Default items per page for page-based pagination.
        default_limit: Default limit for offset-based pagination.
        max_page_size: Maximum page size allowed.
        max_limit: Maximum limit allowed.
        min_page_size: Minimum page size allowed.
        min_limit: Minimum limit allowed.
    """

    strategy: str = Field(
        default=PaginationStrategy.PAGE,
        description="Default pagination strategy: 'page' or 'offset'",
    )

    default_page_size: int = Field(
        default=DEFAULT_PAGE_SIZE,
        description="Default page size for page-based pagination",
        ge=MIN_PAGE_SIZE,
        le=MAX_PAGE_SIZE,
    )

    default_limit: int = Field(
        default=DEFAULT_LIMIT,
        description="Default limit for offset-based pagination",
        ge=MIN_LIMIT,
        le=MAX_LIMIT,
    )

    max_page_size: int = Field(
        default=MAX_PAGE_SIZE,
        description="Maximum page size allowed",
        ge=1,
    )

    max_limit: int = Field(
        default=MAX_LIMIT,
        description="Maximum limit allowed",
        ge=1,
    )

    min_page_size: int = Field(
        default=MIN_PAGE_SIZE,
        description="Minimum page size allowed",
        ge=1,
    )

    min_limit: int = Field(
        default=MIN_LIMIT,
        description="Minimum limit allowed",
        ge=1,
    )

    @field_validator("strategy")
    @classmethod
    def validate_strategy(cls, v: str) -> str:
        """Validate pagination strategy."""
        valid_strategies = {PaginationStrategy.PAGE, PaginationStrategy.OFFSET}
        if v not in valid_strategies:
            raise ValueError(
                f"Invalid pagination strategy: {v}. Must be one of {valid_strategies}"
            )
        return v

    model_config = {"frozen": False, "extra": "forbid"}


class Config(BaseModel):
    """Configuration schema for mockapi-server.

    All settings can be overridden via:
    1. Configuration file (mockapi-server.yml or mockapi-server.json)
    2. Environment variables (prefixed with MOCK_API_)

    Environment variable examples:
        MOCK_API_SEED_COUNT=20
        MOCK_API_PORT=8000
        MOCK_API_LOG_LEVEL=DEBUG
    """

    seed_count: int = Field(
        default=DEFAULT_SEED_COUNT,
        description="Number of entities to generate per model",
        ge=MIN_SEED_COUNT,
        le=MAX_SEED_COUNT,
    )

    port: int = Field(
        default=DEFAULT_PORT,
        description="Port to run the server on",
        ge=MIN_PORT,
        le=MAX_PORT,
    )

    host: str = Field(
        default=DEFAULT_HOST,
        description="Host address to bind the server to",
    )

    locale: str = Field(
        default="en_US",
        description="Locale for fake data generation (e.g., en_US, fr_FR)",
    )

    log_level: str = Field(
        default=DEFAULT_LOG_LEVEL,
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    cors_enabled: bool = Field(
        default=DEFAULT_CORS_ENABLED,
        description="Enable CORS middleware",
    )

    cors_origins: list[str] = Field(
        default=DEFAULT_CORS_ORIGINS,
        description="Allowed CORS origins",
    )

    auto_reload: bool = Field(
        default=DEFAULT_AUTO_RELOAD,
        description="Enable auto-reload on file changes",
    )

    strict_mode: bool = Field(
        default=DEFAULT_STRICT_MODE,
        description="Enable strict schema validation",
    )

    pagination: PaginationConfig = Field(
        default_factory=PaginationConfig,
        description="Pagination configuration",
    )

    @field_validator("locale")
    @classmethod
    def validate_locale(cls, v: str) -> str:
        """Validate locale format."""
        # Valid formats: "en" (2 chars) or "en_US" (language_COUNTRY)
        if len(v) == 2:
            return v
        if "_" in v:
            parts = v.split("_")
            if len(parts) == 2 and len(parts[0]) == 2 and len(parts[1]) == 2:
                return v
        raise ValueError(f"Invalid locale format: {v}. Expected format: en_US or en")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {level.value for level in LogLevel}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, v: list[str]) -> list[str]:
        """Validate CORS origins."""
        if not v:
            raise ValueError("CORS origins cannot be empty")
        return v

    def get_log_level_int(self) -> int:
        """Get logging level as integer constant.

        Returns:
            Logging level constant (e.g., logging.INFO)
        """
        return getattr(logging, self.log_level)

    def apply_logging_config(self) -> None:
        """Apply logging configuration to the application."""
        configure_logging(level=self.get_log_level_int())

    model_config = {"frozen": False, "extra": "forbid"}


# =============================================================================
# FILE LOADING
# =============================================================================


def load_config_file(file_path: Path) -> dict[str, Any]:
    """Load configuration from YAML or JSON file.

    Args:
        file_path: Path to configuration file

    Returns:
        Configuration dictionary

    Raises:
        ConfigFileNotFoundError: If config file doesn't exist
        ConfigParseError: If config file format is invalid
    """
    if not file_path.exists():
        raise ConfigFileNotFoundError(str(file_path))

    content = file_path.read_text()

    # Try JSON first
    if file_path.suffix == FileExtension.JSON:
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ConfigParseError(str(file_path), f"Invalid JSON: {e}") from e

    # Try YAML
    if file_path.suffix in {FileExtension.YML, FileExtension.YAML}:
        try:
            import yaml
        except ImportError:
            raise ImportError(
                "PyYAML is required for YAML config files. "
                "Install with: pip install pyyaml"
            ) from None

        try:
            return yaml.safe_load(content) or {}
        except yaml.YAMLError as e:
            raise ConfigParseError(str(file_path), f"Invalid YAML: {e}") from e

    raise ConfigParseError(
        str(file_path),
        f"Unsupported format: {file_path.suffix}. Use .json, .yml, or .yaml",
    )


def find_config_file() -> Path | None:
    """Find configuration file in current directory or parent directories.

    Searches for (in order):
    - mockapi-server.yml
    - mockapi-server.yaml
    - mockapi-server.json

    Returns:
        Path to config file if found, None otherwise
    """
    current_dir = Path.cwd()

    # Check current directory and up to 3 parent directories
    for _ in range(4):
        for filename in CONFIG_FILE_NAMES:
            config_path = current_dir / filename
            if config_path.exists():
                return config_path

        parent = current_dir.parent
        if parent == current_dir:
            break
        current_dir = parent

    return None


# =============================================================================
# ENVIRONMENT VARIABLES
# =============================================================================


def load_from_env() -> dict[str, Any]:
    """Load configuration from environment variables.

    Environment variables should be prefixed with MOCK_API_ and use
    uppercase with underscores.

    Examples:
        MOCK_API_SEED_COUNT=20
        MOCK_API_PORT=8000
        MOCK_API_LOG_LEVEL=DEBUG
        MOCK_API_CORS_ORIGINS=http://localhost:3000,http://app.example.com

    Returns:
        Configuration dictionary from environment variables
    """
    config: dict[str, Any] = {}

    for key, value in os.environ.items():
        if not key.startswith(ENV_VAR_PREFIX):
            continue

        # Convert MOCK_API_SEED_COUNT -> seed_count
        config_key = key[len(ENV_VAR_PREFIX) :].lower()

        # Handle special types
        if config_key in {ConfigField.SEED_COUNT, ConfigField.PORT}:
            config[config_key] = int(value)
        elif config_key in {
            ConfigField.CORS_ENABLED,
            ConfigField.AUTO_RELOAD,
            ConfigField.STRICT_MODE,
        }:
            config[config_key] = value.lower() in {
                BooleanValue.TRUE,
                BooleanValue.ONE,
                BooleanValue.YES,
                BooleanValue.ON,
            }
        elif config_key == ConfigField.CORS_ORIGINS:
            # Split comma-separated list
            config[config_key] = [origin.strip() for origin in value.split(",")]
        else:
            config[config_key] = value

    return config


# =============================================================================
# PUBLIC API
# =============================================================================


def get_config(config_file: str | Path | None = None) -> Config:
    """Get configuration with layered priority.

    Priority (highest to lowest):
    1. Environment variables (MOCK_API_*)
    2. Config file (explicit or auto-discovered)
    3. Default values

    Args:
        config_file: Path to config file. If None, auto-discovers.

    Returns:
        Configuration instance

    Raises:
        FileNotFoundError: If specified config file doesn't exist
        ValueError: If config file or values are invalid

    Example:
        # Use defaults and env vars
        config = get_config()

        # Load from specific file
        config = get_config("custom-config.yml")

        # Access values
        print(f"Server running on {config.host}:{config.port}")
    """
    # Start with defaults
    config_data = {}

    # Load from file if provided or found
    if config_file:
        file_path = Path(config_file)
        config_data = load_config_file(file_path)
    else:
        # Try to auto-discover config file
        found_file = find_config_file()
        if found_file:
            config_data = load_config_file(found_file)

    # Override with environment variables (highest priority)
    env_config = load_from_env()
    config_data.update(env_config)

    # Create and validate config
    return Config(**config_data)


# Singleton instance for convenience
_config_instance: Config | None = None


def get_global_config() -> Config:
    """Get or create global config instance.

    This is a convenience function for getting a singleton config instance.
    Use get_config() if you need to reload configuration.

    Returns:
        Global configuration instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = get_config()
    return _config_instance


def reset_global_config() -> None:
    """Reset global config instance.

    Useful for testing or when you need to reload configuration.
    """
    global _config_instance
    _config_instance = None
