"""Constants for the core module.

This module contains all constant values used across the core functionality
to avoid magic strings and numbers scattered throughout the code.
"""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
from enum import StrEnum

# =============================================================================
# ENUMS
# =============================================================================


class RelationshipType(StrEnum):
    """Types of relationships between models."""

    MANY_TO_ONE = "many_to_one"
    ONE_TO_MANY = "one_to_many"
    ONE_TO_ONE = "one_to_one"
    MANY_TO_MANY = "many_to_many"


class HTTPMethod(StrEnum):
    """HTTP methods for API operations."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class LogLevel(StrEnum):
    """Logging level options."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ConfigFormat(StrEnum):
    """Supported configuration file formats."""

    YAML = "yaml"
    YML = "yml"
    JSON = "json"


class HTTPStatus:
    """HTTP status codes for API responses."""

    # Success codes
    OK = 200
    CREATED = 201
    NO_CONTENT = 204

    # Client error codes
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    UNPROCESSABLE_ENTITY = 422

    # Server error codes
    INTERNAL_SERVER_ERROR = 500


class FieldPattern(StrEnum):
    """Common field name patterns for smart data generation."""

    # Identity
    ID = "id"
    # Contact
    EMAIL = "email"
    PHONE = "phone"
    # Names
    NAME = "name"
    USERNAME = "username"
    FIRST_NAME = "first_name"
    FIRSTNAME = "firstname"
    LAST_NAME = "last_name"
    LASTNAME = "lastname"
    # Address
    ADDRESS = "address"
    STREET = "street"
    CITY = "city"
    STATE = "state"
    PROVINCE = "province"
    COUNTRY = "country"
    ZIP = "zip"
    POSTAL = "postal"
    # Timestamps
    CREATED_AT = "created_at"
    CREATEDAT = "createdat"
    UPDATED_AT = "updated_at"
    UPDATEDAT = "updatedat"
    # Content
    TITLE = "title"
    CONTENT = "content"
    BODY = "body"
    DESCRIPTION = "description"
    TEXT = "text"
    COMMENT = "comment"
    # URLs
    URL = "url"
    WEBSITE = "website"


class FileExtension(StrEnum):
    """File extensions for various file types."""

    JSON = ".json"
    YAML = ".yaml"
    YML = ".yml"
    PYTHON = ".py"


class ConfigField(StrEnum):
    """Configuration field names."""

    SEED_COUNT = "seed_count"
    PORT = "port"
    HOST = "host"
    LOCALE = "locale"
    LOG_LEVEL = "log_level"
    CORS_ENABLED = "cors_enabled"
    CORS_ORIGINS = "cors_origins"
    AUTO_RELOAD = "auto_reload"
    STRICT_MODE = "strict_mode"


class BooleanValue(StrEnum):
    """String values that represent boolean true."""

    TRUE = "true"
    ONE = "1"
    YES = "yes"
    ON = "on"


# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================

# Configuration defaults
DEFAULT_SEED_COUNT = 10
DEFAULT_PORT = 3000
DEFAULT_HOST = "0.0.0.0"
DEFAULT_LOG_LEVEL = LogLevel.INFO
DEFAULT_CORS_ENABLED = True
DEFAULT_CORS_ORIGINS = ["*"]
DEFAULT_AUTO_RELOAD = False
DEFAULT_STRICT_MODE = False

# Configuration file names (search order)
CONFIG_FILE_NAMES = ["mockapi-server.yml", "mockapi-server.yaml", "mockapi-server.json"]

# Environment variable prefix
ENV_VAR_PREFIX = "MOCK_API_"

# Configuration validation limits
MIN_PORT = 1
MAX_PORT = 65535
MIN_SEED_COUNT = 1
MAX_SEED_COUNT = 10000

# =============================================================================
# PARSER CONSTANTS
# =============================================================================

# File validation
PYTHON_FILE_EXTENSION = FileExtension.PYTHON

# Foreign key detection
FOREIGN_KEY_SUFFIX = "_id"
PRIMARY_KEY_FIELD = "id"

# Model name constants
DEFAULT_USER_MODEL_NAME = "User"

# Semantic field name mappings for FK resolution
# These field name bases will automatically resolve to DEFAULT_USER_MODEL_NAME if exists
SEMANTIC_USER_FIELD_NAMES = {
    "author",
    "owner",
    "creator",
    "user",
    "assignee",
    "moderator",
    "reviewer",
    "editor",
}

# =============================================================================
# GENERATOR CONSTANTS
# =============================================================================

# Default values for data generation
DEFAULT_GENERATION_COUNT = 10
DEFAULT_LOCALE = "en_US"

# Optional field generation probability
OPTIONAL_FIELD_NULL_PROBABILITY = 0.2

# Default FK generation range
DEFAULT_FK_RANGE_MIN = 1
DEFAULT_FK_RANGE_MAX = 100

# Random number generation ranges
RANDOM_INT_MIN = 1
RANDOM_INT_MAX = 1000
RANDOM_FLOAT_MIN = 0.0
RANDOM_FLOAT_MAX = 1000.0
RANDOM_FLOAT_PRECISION = 2

# Date generation ranges (in days)
CREATED_AT_MAX_DAYS_AGO = 365
UPDATED_AT_MAX_DAYS_AGO = 30

# Text generation parameters
TITLE_WORD_COUNT = 6
PARAGRAPH_SENTENCE_COUNT = 5
TEXT_MAX_CHARS = 200

# =============================================================================
# STORE CONSTANTS
# =============================================================================

# Pagination defaults
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MIN_PAGE_SIZE = 1

# Query defaults
DEFAULT_PAGE_NUMBER = 1

# =============================================================================
# ROUTER CONSTANTS
# =============================================================================


class RouteDescription(StrEnum):
    """API route descriptions for OpenAPI documentation."""

    LIST = "List all instances with pagination"
    CREATE = "Create a new instance"
    READ = "Get a single instance by ID"
    UPDATE = "Update an existing instance"
    DELETE = "Delete an instance by ID"
    NOT_FOUND = "Instance not found"


class QueryParam(StrEnum):
    """Query parameter names for API requests."""

    PAGE = "page"
    PAGE_SIZE = "page_size"


class ResponseKey(StrEnum):
    """Keys used in API response JSON structures."""

    ITEMS = "items"
    PAGINATION = "pagination"
    PAGE = "page"
    PAGE_SIZE = "page_size"
    TOTAL_ITEMS = "total_items"
    TOTAL_PAGES = "total_pages"


class ModelName(StrEnum):
    """Model name constants for dynamic model creation."""

    PAGINATION_INFO = "PaginationInfo"
    INPUT_SUFFIX = "Input"
    LIST_SUFFIX = "List"


# Route prefixes
API_VERSION_PREFIX = "/api/v1"
DEFAULT_ROUTE_PREFIX = ""

# Route tags
DEFAULT_TAG = "default"

# URL path components
URL_PATH_SEPARATOR = "/"
URL_PLURAL_SUFFIX = "s"
URL_ID_PARAMETER = "instance_id"
URL_ID_PATH_SEGMENT = "{instance_id}"

# =============================================================================
# CLI INIT CONSTANTS
# =============================================================================


class TemplateType(StrEnum):
    """Available project templates for init command."""

    BASIC = "basic"
    BLOG = "blog"
    ECOMMERCE = "ecommerce"
    CUSTOM = "custom"


# Init command defaults
DEFAULT_PROJECT_NAME = "my-mockapi-server"
DEFAULT_MODELS_FILENAME = "models.py"
DEFAULT_CONFIG_FILENAME = "mockapi-server.yml"
DEFAULT_README_FILENAME = "README.md"
DEFAULT_GITIGNORE_FILENAME = ".gitignore"

# Project name validation (alphanumeric, hyphens, underscores)
PROJECT_NAME_PATTERN = r"^[a-zA-Z0-9_-]+$"
