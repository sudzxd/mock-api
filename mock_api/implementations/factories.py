"""Factory classes for creating strategy implementations.

This module provides factories for creating concrete implementations of
domain protocols. Uses dependency injection to provide implementations
to the application layer.
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.config import Config
    from ..core.types import ModelSchema
    from ..domain.generation import IDataGenerator, IFieldGenerationStrategy
    from ..domain.schema import ISchemaParser

# Project/local
from .generation import FakerDataGenerator
from .parsing import PydanticSchemaParser
from .storage import InMemoryRepository

# =============================================================================
# PUBLIC API
# =============================================================================


class SchemaParserFactory:
    """Factory for creating schema parser implementations.

    Current implementation: Pydantic models only

    TODO: Add support for multiple parser types (Issues #9, TBD):
        - TypeScript parser: TypeScriptSchemaParser
        - OpenAPI parser: OpenAPISchemaParser (Issue #9)
        - JSON Schema parser: JSONSchemaParser
    """

    @staticmethod
    def create(parser_type: str = "pydantic") -> ISchemaParser:
        """Create schema parser based on type.

        Args:
            parser_type: Type of parser ("pydantic", "typescript", "openapi")

        Returns:
            Schema parser implementation

        Raises:
            ValueError: If parser_type is not supported
        """
        if parser_type == "pydantic":
            return PydanticSchemaParser()
        # TODO: Add TypeScript parser support
        # elif parser_type == "typescript":
        #     return TypeScriptSchemaParser()
        # TODO: Add OpenAPI parser support (Issue #9)
        # elif parser_type == "openapi":
        #     return OpenAPISchemaParser()
        raise ValueError(
            f"Unsupported parser type: {parser_type}. Supported types: pydantic"
        )


class StorageStrategyFactory:
    """Factory for creating storage backend implementations.

    Current implementation: In-memory storage only

    TODO: Add support for persistent storage backends:
        - JSON file storage (Issue #48)
        - SQLite storage (Issue #51)
        - PostgreSQL storage (Issue #50)

    Example (future):
        >>> factory = StorageStrategyFactory()
        >>> storage = factory.create("json://data.json")
        >>> storage = factory.create("sqlite://mock.db")
        >>> storage = factory.create("postgresql://localhost:5432/mock")
    """

    @staticmethod
    def create(
        storage_url: str = "memory://",
    ) -> InMemoryRepository:
        """Create storage backend based on URL.

        Args:
            storage_url: Storage URL (e.g., "memory://", "json://data.json")

        Returns:
            Storage strategy implementation

        Raises:
            ValueError: If storage_url format is not supported
        """
        if storage_url.startswith("memory://"):
            return InMemoryRepository()
        # TODO: Add JSON storage support (Issue #48)
        # elif storage_url.startswith("json://"):
        #     path = storage_url.replace("json://", "")
        #     repository = JSONRepository(path)
        #     if schemas:
        #         repository.initialize(schemas)
        #     return repository
        # TODO: Add SQLite storage support (Issue #51)
        # elif storage_url.startswith("sqlite://"):
        #     path = storage_url.replace("sqlite://", "")
        #     repository = SQLiteRepository(path)
        #     if schemas:
        #         repository.initialize(schemas)
        #     return repository
        # TODO: Add PostgreSQL storage support (Issue #50)
        # elif storage_url.startswith("postgresql://"):
        #     repository = PostgreSQLRepository(storage_url)
        #     if schemas:
        #         await repository.initialize(schemas)
        #     return repository
        raise ValueError(
            f"Unsupported storage URL: {storage_url}. Supported formats: memory://"
        )


class DataGeneratorFactory:
    """Factory for creating data generator implementations.

    Current implementation: Faker-based generation only

    TODO: Add support for custom generation strategies (Issue #21):
        - Custom Faker providers
        - Domain-specific generators (medical, finance, tech)
        - Sequential value generators
        - Fixed value generators

    Example (future):
        >>> factory = DataGeneratorFactory()
        >>> generator = factory.create(
        ...     schemas,
        ...     custom_providers=[MedicalProvider(), FinanceProvider()]
        ... )
    """

    @staticmethod
    def create(
        schemas: dict[str, ModelSchema],
        locale: str | None = None,
        seed: int | None = None,
        config: Config | None = None,
        custom_strategies: list[IFieldGenerationStrategy] | None = None,
    ) -> IDataGenerator:
        """Create data generator with optional custom strategies.

        Args:
            schemas: Model schemas for generation
            locale: Faker locale (default: en_US)
            seed: Random seed for reproducibility
            config: Configuration object
            custom_strategies: Custom field generation strategies (Issue #21)

        Returns:
            Data generator implementation
        """
        # TODO: Issue #21 - Use custom_strategies when implemented
        _ = custom_strategies  # Suppress unused argument warning
        return FakerDataGenerator(
            schemas=schemas,
            locale=locale,
            seed=seed,
            config=config,
        )


# =============================================================================
# FUTURE FACTORIES (TODOs)
# =============================================================================

# TODO: Issue #47 - Create ExportStrategyFactory
# class ExportStrategyFactory:
#     """Factory for creating API collection exporters."""
#     @staticmethod
#     def create(export_format: str) -> IExportStrategy:
#         # Postman, Insomnia, HTTPie, OpenAPI
#         ...

# TODO: Issue #46 - Create DataTransferFactory
# class DataTransferFactory:
#     """Factory for creating data import/export strategies."""
#     @staticmethod
#     def create_importer(format: str) -> IDataImporter:
#         # JSON, CSV, SQL
#         ...
#     @staticmethod
#     def create_exporter(format: str) -> IDataExporter:
#         # JSON, CSV, SQL
#         ...

# TODO: Issues #13, #12, #6 - Create MiddlewareFactory
# class MiddlewareFactory:
#     """Factory for creating middleware implementations."""
#     @staticmethod
#     def create(middleware_type: str) -> IMiddleware:
#         # CORS, Auth, RateLimit, Logging, Scenarios
#         ...

# TODO: Issues #52, #53 - Create MonitoringFactory
# class MonitoringFactory:
#     """Factory for creating monitoring implementations."""
#     @staticmethod
#     def create_health_check() -> IHealthCheck:
#         ...
#     @staticmethod
#     def create_metrics_collector(format: str) -> IMetricsCollector:
#         # Prometheus, StatsD, CloudWatch
#         ...
