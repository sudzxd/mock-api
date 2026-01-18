"""Parser factory for auto-detecting schema format.

Uses Strategy Pattern - selects appropriate parser based on file extension
and content inspection.
"""

from __future__ import annotations

from ...domain.schema.protocols import ISchemaParser
from .graphql_parser import GraphQLSchemaParser
from .openapi_parser import OpenAPISchemaParser
from .pydantic_parser import PydanticSchemaParser


class ParserFactory:
    """Factory for creating appropriate schema parser.

    Auto-detects schema format based on file extension and content.
    Extensible - new parsers can be registered at runtime.

    Supported formats:
    - .py files -> PydanticSchemaParser
    - .yaml, .yml, .json files -> OpenAPISchemaParser
    - .graphql, .gql files -> GraphQLSchemaParser

    Usage:
        parser = ParserFactory.create_parser("models.py")
        schemas = parser.parse_file("models.py")
    """

    # Registry of available parsers (order matters - first match wins)
    _parsers: list[type[ISchemaParser]] = [
        PydanticSchemaParser,
        OpenAPISchemaParser,
        GraphQLSchemaParser,
    ]

    @classmethod
    def create_parser(cls, file_path: str) -> ISchemaParser:
        """Create appropriate parser for file.

        Auto-detection strategy:
        1. Iterate through registered parsers
        2. Call supports_file() on each
        3. Return first parser that supports file
        4. Raise error if no parser found

        Args:
            file_path: Path to schema file

        Returns:
            Parser instance that can handle file

        Raises:
            UnsupportedSchemaError: If no parser supports file format
        """
        ...

    @classmethod
    def register_parser(cls, parser_class: type[ISchemaParser]) -> None:
        """Register custom parser.

        Allows users to add their own schema parsers.

        Args:
            parser_class: Parser class to register

        Example:
            class CustomParser(ISchemaParser):
                def parse_file(self, file_path: str) -> dict[str, ModelSchema]:
                    ...
                def supports_file(self, file_path: str) -> bool:
                    return file_path.endswith('.custom')

            ParserFactory.register_parser(CustomParser)
        """
        ...

    @classmethod
    def get_supported_formats(cls) -> list[str]:
        """Get list of supported file formats.

        Returns:
            List of file extensions (e.g., ['.py', '.yaml', '.graphql'])
        """
        ...

    @classmethod
    def detect_format(cls, file_path: str) -> str | None:
        """Detect schema format without creating parser.

        Args:
            file_path: Path to schema file

        Returns:
            Parser class name if supported, None otherwise
        """
        ...
