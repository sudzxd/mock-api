"""Main CLI entry point."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Third-party
import click

# Project/local
from .commands.serve import serve


@click.group()
@click.version_option(version="0.1.0", prog_name="mock-api")
def cli() -> None:
    """MockAPI Server - Generate REST APIs from schema definitions.

    Supports multiple schema formats:
    - Pydantic models (.py)
    - OpenAPI specifications (.yaml, .json)
    - GraphQL schemas (.graphql, .gql)
    """
    ...


# Register commands
cli.add_command(serve)


if __name__ == "__main__":
    cli()
