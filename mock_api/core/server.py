"""FastAPI server orchestration for mock API.

This module provides the Server class that coordinates all components
(parser, store, router, generator) to create a fully functional mock API.

Architecture:
- Facade pattern to simplify component coordination
- Lazy initialization for FastAPI app
- Optional data pre-population

Example:
    >>> server = Server("models.py", generate_data=True)
    >>> app = server.create_app()
    >>> # Use with uvicorn: uvicorn module:server.app
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Third-party
from fastapi import FastAPI

# Project/local
from ..utils.logger import get_logger
from .config import Config, get_config
from .constants import API_VERSION_PREFIX, DEFAULT_GENERATION_COUNT
from .generator import DataGenerator
from .parser import SchemaParser
from .router import RouterGenerator
from .store import DataStore
from .types import ModelSchema

# =============================================================================
# TYPES & CONSTANTS
# =============================================================================
logger = get_logger(__name__)


# =============================================================================
# PUBLIC API
# =============================================================================


class Server:
    """FastAPI server orchestration for mock API.

    Coordinates parser, store, router, and optional data generation to
    create a fully functional REST API from Pydantic models.

    Example:
        >>> server = Server("models.py")
        >>> app = server.create_app()
        >>> # Run with: uvicorn module:server.app

        >>> # With pre-populated data
        >>> server = Server("models.py", generate_data=True, data_count=50)
        >>> app = server.create_app()
    """

    def __init__(
        self,
        models_file: str,
        prefix: str = API_VERSION_PREFIX,
        generate_data: bool = False,
        data_count: int = DEFAULT_GENERATION_COUNT,
        config: Config | None = None,
    ) -> None:
        """Initialize server components.

        Args:
            models_file: Path to Python file containing Pydantic models.
            prefix: API prefix for all routes (default: "/api/v1").
            generate_data: Whether to pre-populate with generated data.
            data_count: Number of instances to generate per model.
            config: Configuration instance (auto-loads if not provided).

        Example:
            >>> server = Server(
            ...     "models.py",
            ...     prefix="/api/v1",
            ...     generate_data=True,
            ...     data_count=100
            ... )
        """
        self.models_file = models_file
        self.prefix = prefix
        self.generate_data = generate_data
        self.data_count = data_count
        self.config = config or get_config()

        # Initialize components
        logger.info(f"Initializing server from {models_file}")
        self.parser = SchemaParser()
        self.schemas: dict[str, ModelSchema] = self.parser.parse_file(models_file)
        self.store = DataStore()
        self.router_generator = RouterGenerator(self.schemas, self.store, prefix)

        # Lazy app initialization
        self._app: FastAPI | None = None

        logger.info(f"Server initialized with {len(self.schemas)} model(s)")

    def create_app(self) -> FastAPI:
        """Create and configure FastAPI application.

        Returns:
            Configured FastAPI application with all routes.

        Example:
            >>> server = Server("models.py")
            >>> app = server.create_app()
            >>> # app.routes contains all generated CRUD endpoints
        """
        logger.info("Creating FastAPI application")

        app = FastAPI(
            title="Mock API",
            description="Dynamically generated REST API from Pydantic models",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
        )

        # Configure CORS if enabled
        if self.config.cors_enabled:
            from fastapi.middleware.cors import CORSMiddleware

            app.add_middleware(
                CORSMiddleware,
                allow_origins=self.config.cors_origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            logger.info(f"CORS enabled for origins: {self.config.cors_origins}")

        # Generate and include routes
        router = self.router_generator.generate_routes()
        app.include_router(router)

        logger.info(f"FastAPI app created with {len(app.routes)} route(s)")

        # Optionally pre-populate with generated data
        if self.generate_data:
            logger.info(f"Pre-populating data ({self.data_count} per model)")
            self.populate_data()

        self._app = app
        return app

    def populate_data(self) -> None:
        """Pre-populate store with generated data.

        Uses DataGenerator to create realistic test data for all models.
        Respects foreign key relationships and field patterns.

        Time Complexity: O(n * m) where n=models, m=data_count
        """
        generator = DataGenerator(self.schemas, config=self.config)

        for model_name in self.schemas:
            logger.debug(f"Generating {self.data_count} {model_name} instances")
            data = generator.generate(model_name, count=self.data_count)

            for item in data:
                self.store.create(model_name, item)

        total_items = sum(self.store.count(model_name) for model_name in self.schemas)
        logger.info(f"Pre-populated {total_items} total instances")

    @property
    def app(self) -> FastAPI:
        """Get FastAPI app, creating if necessary.

        Lazy initialization - app is only created on first access.

        Returns:
            FastAPI application instance.

        Example:
            >>> server = Server("models.py")
            >>> app = server.app  # Creates app on first access
            >>> same_app = server.app  # Returns existing app
        """
        if self._app is None:
            return self.create_app()
        return self._app

    @property
    def has_app(self) -> bool:
        """Check if app has been initialized.

        Returns:
            True if app exists, False otherwise.
        """
        return self._app is not None
