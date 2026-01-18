"""Serve command - start mock API server."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
# Third-party
import click
import uvicorn
from fastapi import FastAPI

# Project/local
from mock_api.application.dto.requests import BulkCreateEntitiesRequest
from mock_api.application.use_cases import BulkCreateEntitiesUseCase
from mock_api.core.config.constants import API_PREFIX, DEFAULT_HOST, DEFAULT_PORT
from mock_api.domain.value_objects.schema import ModelSchema
from mock_api.infrastructure.generators.faker_generator import FakerDataGenerator
from mock_api.infrastructure.parsers.pydantic_parser import PydanticSchemaParser
from mock_api.presentation.api.v1.router import create_router
from mock_api.presentation.dependencies.injection import get_container
from mock_api.presentation.dependencies.injection import (
    initialize_dependencies as inject_initialize_dependencies,
)
from mock_api.presentation.middleware import setup_exception_handlers


# =============================================================================
# PUBLIC API
# =============================================================================
@click.command()
@click.argument("schema_file", type=click.Path(exists=True))
@click.option("--port", default=DEFAULT_PORT, help="Port to run server on")
@click.option("--host", default=DEFAULT_HOST, help="Host to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload (dev mode)")
@click.option(
    "--generate-data/--no-generate-data",
    default=False,
    help="Generate fake data on startup",
)
@click.option(
    "--data-count", default=10, help="Number of entities to generate per model"
)
@click.option("--storage-url", default="memory://", help="Storage backend URL")
def serve(
    schema_file: str,
    port: int,
    host: str,
    reload: bool,
    generate_data: bool,
    data_count: int,
    storage_url: str,
) -> None:
    """Start mock API server from schema file.

    Supported schema formats:
    - Pydantic: models.py
    - OpenAPI: openapi.yaml, openapi.json
    - GraphQL: schema.graphql, schema.gql

    Examples:
        mock-api serve models.py
        mock-api serve openapi.yaml --port 8000
        mock-api serve schema.graphql --generate-data --data-count 50

    Args:
        schema_file: Path to schema file
        port: Port to run server on
        host: Host to bind to
        reload: Enable auto-reload (dev mode)
        generate_data: Generate fake data on startup
        data_count: Number of entities to generate per model
        storage_url: Storage backend URL
    """
    # Display startup message
    click.echo("🚀 Starting Mock API Server...")
    click.echo(f"📄 Schema file: {schema_file}")
    click.echo(f"🌐 Server: http://{host}:{port}")
    click.echo(f"💾 Storage: {storage_url}")

    # Initialize FastAPI app
    app = _initialize_app(schema_file, storage_url, generate_data, data_count)

    # Start uvicorn server
    click.echo(f"✅ Server ready! Docs available at http://{host}:{port}/docs")
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


# =============================================================================
# PRIVATE HELPERS
# =============================================================================
def _initialize_app(
    schema_file: str,
    storage_url: str,
    generate_data: bool,
    data_count: int,
) -> FastAPI:
    """Initialize FastAPI application with parsed schema.

    Flow:
    1. Parse schema file into ModelSchema objects
    2. Initialize global dependencies (repository, services)
    3. Optionally generate fake data
    4. Create FastAPI app
    5. Create and include router

    Args:
        schema_file: Path to schema file
        storage_url: Storage backend URL
        generate_data: Whether to generate data
        data_count: Number of entities to generate

    Returns:
        FastAPI application instance
    """
    # Parse schema
    click.echo(f"📖 Parsing schema from {schema_file}...")
    schemas = _parse_schema(schema_file)
    click.echo(f"✅ Found {len(schemas)} models: {', '.join(schemas.keys())}")

    # Initialize dependencies
    click.echo("🔧 Initializing dependencies...")
    _initialize_dependencies(schemas, storage_url)

    # Generate fake data if requested
    if generate_data:
        click.echo(f"🎲 Generating {data_count} entities per model...")
        _generate_data(schemas, data_count)

    # Create FastAPI app
    app = FastAPI(
        title="Mock API Server",
        description="Auto-generated REST API from schema",
        version="1.0.0",
    )

    # Setup exception handlers (centralized error handling)
    setup_exception_handlers(app)

    # Create and include router
    router = create_router(schemas, prefix=API_PREFIX)
    app.include_router(router)

    return app


def _parse_schema(schema_file: str) -> dict[str, ModelSchema]:
    """Parse schema using PydanticSchemaParser.

    Args:
        schema_file: Path to schema file

    Returns:
        Dict of parsed ModelSchema objects

    Raises:
        SchemaParseError: If parsing fails
    """
    # For MVP, only support Pydantic parser
    # TODO: Add ParserFactory for multi-format support
    parser = PydanticSchemaParser()
    return parser.parse_file(schema_file)


def _initialize_dependencies(schemas: dict[str, ModelSchema], storage_url: str) -> None:
    """Initialize global dependencies.

    Calls the presentation layer's initialize_dependencies to set up:
    - Repository (via StorageFactory)
    - FilterService
    - SortService
    - Schemas

    Args:
        schemas: Parsed schemas
        storage_url: Storage URL
    """
    inject_initialize_dependencies(schemas, storage_url)


def _generate_data(schemas: dict[str, ModelSchema], count: int) -> None:
    """Generate fake data for all models.

    Uses FakerDataGenerator to create entities and BulkCreateEntitiesUseCase
    to persist them efficiently to the repository.

    Args:
        schemas: Parsed schemas
        count: Number of entities per model
    """
    # Get dependency container
    container = get_container()

    # Create generator and use case
    generator = FakerDataGenerator(schemas)
    use_case = BulkCreateEntitiesUseCase(container.repository, container.schemas)

    # Generate and persist data for each model
    for model_name, schema in schemas.items():
        try:
            # Generate fake entities
            entities = generator.generate(schema, count=count)

            # Create request DTO
            request = BulkCreateEntitiesRequest(
                model_name=model_name, data_list=entities
            )

            # Bulk persist all entities at once
            use_case.execute(request)

            click.echo(f"  ✓ Generated {count} {model_name} entities")

        except Exception as e:
            click.echo(f"  ✗ Failed to generate {model_name}: {e}", err=True)
