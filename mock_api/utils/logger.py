"""Centralized logging configuration for mockapi-server.

This module provides a consistent logging interface across the application
with colored output using Rich for better developer experience.
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
import logging

# Third-party
from rich.console import Console
from rich.logging import RichHandler

# =============================================================================
# TYPES & CONSTANTS
# =============================================================================
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_FORMAT = "%(message)s"
DATE_FORMAT = "[%X]"

# =============================================================================
# PUBLIC API
# =============================================================================


def get_logger(name: str, level: int = DEFAULT_LOG_LEVEL) -> logging.Logger:
    """Get a configured logger instance.

    Args:
        name: Logger name (typically __name__ of the calling module).
        level: Logging level (default: INFO).

    Returns:
        Configured logger with Rich handler for colored output.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Parsing schema file")
        >>> logger.debug("Found 3 models")
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(level)

        # Use Rich handler for beautiful colored output
        console = Console(stderr=True)
        handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
        )
        handler.setFormatter(logging.Formatter(DEFAULT_FORMAT, datefmt=DATE_FORMAT))

        logger.addHandler(handler)
        logger.propagate = False

    return logger


def configure_logging(level: int = DEFAULT_LOG_LEVEL) -> None:
    """Configure root logger for the application.

    Args:
        level: Global logging level to set.

    Example:
        >>> configure_logging(logging.DEBUG)
    """
    logging.basicConfig(
        level=level,
        format=DEFAULT_FORMAT,
        datefmt=DATE_FORMAT,
        handlers=[
            RichHandler(
                console=Console(stderr=True),
                show_time=True,
                show_path=False,
                rich_tracebacks=True,
            )
        ],
    )
