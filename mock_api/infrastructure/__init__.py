"""Infrastructure layer - concrete implementations of domain protocols.

This layer implements all domain protocols with technical details:
- Parsers: PydanticSchemaParser, OpenAPISchemaParser, GraphQLSchemaParser
- Repositories: MemoryRepository, JSONRepository, SQLiteRepository, etc.
- Services: FilterService, SortService, ValidationService
- Generators: FakerDataGenerator
- Factories: ParserFactory, StorageFactory
"""
