"""CLI for mock-api using Click.

This module provides the command-line interface for creating and managing
mock APIs from Pydantic models.

Commands:
- serve: Start the development server
- generate: Generate mock data files
- validate: Validate Pydantic models file

Example:
    $ mock-api serve --models models.py --generate-data
    $ mock-api generate --models models.py --count 100
    $ mock-api validate --models models.py
"""

# pyright: reportUnusedFunction=false

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
import json
import sys
from pathlib import Path

# Third-party
import click

# Project/local
from ..core.config import get_config
from ..core.generator import DataGenerator
from ..core.parser import SchemaParser
from ..core.server import Server
from ..utils.logger import get_logger

# =============================================================================
# TYPES & CONSTANTS
# =============================================================================
logger = get_logger(__name__)

DEFAULT_OUTPUT_DIR = "data"


# =============================================================================
# CLI GROUP
# =============================================================================


@click.group()
@click.version_option(version="1.0.0", prog_name="mock-api")
def cli() -> None:
    """Mock API - Generate REST APIs from Pydantic models.

    Create fully functional mock REST APIs with CRUD operations,
    validation, and realistic test data from your Pydantic models.

    Example:
        $ mock-api serve --models models.py --generate-data
    """
    pass


# =============================================================================
# SERVE COMMAND
# =============================================================================


@cli.command()
@click.option(
    "--models",
    "-m",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="Path to Python file containing Pydantic models",
)
@click.option(
    "--host",
    "-h",
    type=str,
    default=None,
    help="Host to bind the server to (default: from config or 0.0.0.0)",
)
@click.option(
    "--port",
    "-p",
    type=int,
    default=None,
    help="Port to bind the server to (default: from config or 3000)",
)
@click.option(
    "--reload/--no-reload",
    default=None,
    help="Enable auto-reload on code changes (default: from config or false)",
)
@click.option(
    "--generate-data/--no-generate-data",
    default=False,
    show_default=True,
    help="Pre-populate with generated data",
)
@click.option(
    "--data-count",
    "-c",
    type=int,
    default=None,
    help="Number of instances to generate per model (default: from config or 10)",
)
@click.option(
    "--prefix",
    type=str,
    default="/api/v1",
    show_default=True,
    help="API route prefix",
)
@click.option(
    "--config",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to configuration file (YAML or JSON)",
)
def serve(
    models: Path,
    host: str | None,
    port: int | None,
    reload: bool | None,
    generate_data: bool,
    data_count: int | None,
    prefix: str,
    config: Path | None,
) -> None:
    """Start the development server.

    Launches a FastAPI development server with your mock API.
    The server provides OpenAPI docs at /docs and /redoc.

    Args:
        models: Path to Python file containing Pydantic models.
        host: Host to bind the server to.
        port: Port to bind the server to.
        reload: Enable auto-reload on code changes.
        generate_data: Pre-populate with generated data.
        data_count: Number of instances to generate per model.
        prefix: API route prefix.
        config: Path to configuration file (YAML or JSON).

    Example:
        $ mock-api serve --models models.py --generate-data --data-count 50
        $ mock-api serve -m models.py --port 3000 --reload
    """
    try:
        # Load configuration
        cfg = get_config(config_file=config)

        # Apply logging configuration
        cfg.apply_logging_config()

        # Use CLI args if provided, otherwise use config values
        final_host = host if host is not None else cfg.host
        final_port = port if port is not None else cfg.port
        final_reload = reload if reload is not None else cfg.auto_reload
        final_data_count = data_count if data_count is not None else cfg.seed_count

        click.echo("🚀 Starting Mock API Server...")
        click.echo(f"📁 Models file: {models}")
        click.echo(f"🌐 Server: http://{final_host}:{final_port}")
        click.echo(f"📚 Docs: http://{final_host}:{final_port}/docs")

        # Create server
        server = Server(
            str(models),
            prefix=prefix,
            generate_data=generate_data,
            data_count=final_data_count,
            config=cfg,
        )

        if generate_data:
            click.echo(f"📊 Pre-populating {final_data_count} instances per model...")

        # Create app
        app = server.create_app()

        click.echo(f"✅ Server initialized with {len(server.schemas)} model(s)")
        click.echo()

        # Import uvicorn here to avoid dependency at module level
        try:
            import uvicorn
        except ImportError:
            click.echo(
                "❌ Error: uvicorn is not installed. Install with: pip install uvicorn",
                err=True,
            )
            sys.exit(1)

        # Run server
        uvicorn.run(
            app,
            host=final_host,
            port=final_port,
            reload=final_reload,
            log_level="info",
        )

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        logger.exception("Server startup failed")
        sys.exit(1)


# =============================================================================
# GENERATE COMMAND
# =============================================================================


@cli.command()
@click.option(
    "--models",
    "-m",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="Path to Python file containing Pydantic models",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=False, path_type=Path),
    default=DEFAULT_OUTPUT_DIR,
    show_default=True,
    help="Output directory for generated data files",
)
@click.option(
    "--count",
    "-c",
    type=int,
    default=None,
    help="Number of instances to generate per model (default: from config or 10)",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["json"], case_sensitive=False),
    default="json",
    show_default=True,
    help="Output format for generated data",
)
@click.option(
    "--config",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to configuration file (YAML or JSON)",
)
def generate(
    models: Path,
    output: Path,
    count: int | None,
    output_format: str,
    config: Path | None,
) -> None:
    """Generate mock data files.

    Creates JSON files with realistic test data for each model.
    Respects field patterns and foreign key relationships.

    Args:
        models: Path to Python file containing Pydantic models.
        output: Output directory for generated data files.
        count: Number of instances to generate per model.
        config: Path to configuration file (YAML or JSON).

    Example:
        $ mock-api generate --models models.py --count 100 --output ./data
        $ mock-api generate -m models.py -c 50 -o ./fixtures
    """
    try:
        # Load configuration
        cfg = get_config(config_file=config)

        # Use CLI arg if provided, otherwise use config value
        final_count = count if count is not None else cfg.seed_count

        click.echo("📊 Generating mock data...")
        click.echo(f"📁 Models file: {models}")
        click.echo(f"📂 Output directory: {output}")
        click.echo(f"🔢 Count per model: {final_count}")
        click.echo()

        # Parse models
        parser = SchemaParser()
        schemas = parser.parse_file(str(models))

        click.echo(f"✅ Found {len(schemas)} model(s): {', '.join(schemas.keys())}")
        click.echo()

        # Create output directory
        output.mkdir(parents=True, exist_ok=True)

        # Generate data
        generator = DataGenerator(schemas, config=cfg)
        total_generated = 0

        for model_name in schemas:
            click.echo(f"⚙️  Generating {final_count} {model_name} instances...")

            data = generator.generate(model_name, count=final_count)

            # Write to file
            output_file = output / f"{model_name.lower()}.{output_format}"
            with output_file.open("w") as f:
                json.dump(data, f, indent=2, default=str)

            total_generated += len(data)
            click.echo(f"   ✅ Wrote {len(data)} instances to {output_file}")

        click.echo()
        click.echo(f"✅ Successfully generated {total_generated} total instances")

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        logger.exception("Data generation failed")
        sys.exit(1)


# =============================================================================
# VALIDATE COMMAND
# =============================================================================


@cli.command()
@click.option(
    "--models",
    "-m",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="Path to Python file containing Pydantic models",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Show detailed model information",
)
def validate(models: Path, verbose: bool) -> None:
    """Validate Pydantic models file.

    Checks that the models file is valid and can be parsed.
    Optionally shows detailed information about each model.

    Args:
        models: Path to Python file containing Pydantic models.
        verbose: Show detailed model information.

    Example:
        $ mock-api validate --models models.py
        $ mock-api validate -m models.py --verbose
    """
    try:
        click.echo("🔍 Validating models file...")
        click.echo(f"📁 File: {models}")
        click.echo()

        # Parse models
        parser = SchemaParser()
        schemas = parser.parse_file(str(models))

        click.echo(f"✅ Valid! Found {len(schemas)} model(s):")
        click.echo()

        for model_name, schema in schemas.items():
            click.echo(f"  📦 {model_name}")

            if verbose:
                click.echo(f"     Fields: {len(schema.fields)}")
                for field in schema.fields:
                    field_info = f"       - {field.name}: {field.type.__name__}"
                    if field.is_optional:
                        field_info += " (optional)"
                    if field.is_foreign_key:
                        field_info += f" → {field.related_model}"
                    click.echo(field_info)

                if schema.relationships:
                    click.echo(f"     Relationships: {len(schema.relationships)}")
                    for rel in schema.relationships:
                        click.echo(
                            f"       - {rel.field_name} → {rel.related_model} "
                            f"({rel.relationship_type})"
                        )
                click.echo()

        if not verbose:
            click.echo()
            click.echo("💡 Use --verbose for detailed model information")

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        logger.exception("Validation failed")
        sys.exit(1)


# =============================================================================
# ENTRY POINT
# =============================================================================


def main() -> None:
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
