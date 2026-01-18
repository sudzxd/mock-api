"""Application configuration.

Configuration is loaded from environment variables and can be overridden.
Uses dataclass for type safety and immutability.
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from dataclasses import dataclass, field
from typing import Any

# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass(frozen=True)
class Config:
    """Application configuration (immutable).

    All configuration values loaded from environment or defaults.
    Injected via dependency injection throughout the application.
    """

    # Server settings
    host: str = "0.0.0.0"
    port: int = 3000
    reload: bool = False
    workers: int = 1

    # API settings
    api_prefix: str = "/api/v1"
    api_title: str = "MockAPI Server"
    api_description: str = "Generated REST API from schema"
    api_version: str = "1.0.0"

    # Pagination defaults
    default_page_size: int = 20
    max_page_size: int = 100

    # Data generation
    default_data_count: int = 10
    faker_locale: str = "en_US"
    faker_seed: int | None = None

    # Storage
    storage_url: str = "memory://"  # memory://, json://path, sqlite://path, etc.

    # CORS settings
    cors_enabled: bool = True
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    cors_methods: list[str] = field(default_factory=lambda: ["*"])
    cors_headers: list[str] = field(default_factory=lambda: ["*"])

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Feature flags
    enable_bulk_operations: bool = True
    enable_data_generation: bool = True
    enable_openapi_docs: bool = True

    def __post_init__(self) -> None:
        """Validate configuration."""
        ...

    @classmethod
    def from_env(cls) -> Config:
        """Load configuration from environment variables.

        Environment variables:
        - MOCK_API_HOST
        - MOCK_API_PORT
        - MOCK_API_STORAGE_URL
        - etc.

        Returns:
            Config instance with values from environment
        """
        ...

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dict representation of config
        """
        ...


# Global config instance (singleton pattern)
_config: Config | None = None


def get_config() -> Config:
    """Get global configuration instance.

    Lazy initialization - creates config on first call.

    Returns:
        Global Config instance
    """
    ...


def set_config(config: Config) -> None:
    """Set global configuration (for testing).

    Args:
        config: Config instance to use globally
    """
    ...
