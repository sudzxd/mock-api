"""Tests for configuration management."""

from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library
import json
import os
from collections.abc import Generator
from pathlib import Path

# Third-party
import pytest
from _pytest.monkeypatch import MonkeyPatch

# Local
from mock_api.core.config import (
    Config,
    find_config_file,
    get_config,
    get_global_config,
    load_config_file,
    load_from_env,
    reset_global_config,
)
from mock_api.core.constants import (
    DEFAULT_AUTO_RELOAD,
    DEFAULT_CORS_ENABLED,
    DEFAULT_CORS_ORIGINS,
    DEFAULT_HOST,
    DEFAULT_LOG_LEVEL,
    DEFAULT_PORT,
    DEFAULT_SEED_COUNT,
    DEFAULT_STRICT_MODE,
)
from mock_api.core.exceptions import ConfigFileNotFoundError, ConfigParseError
from pydantic import ValidationError

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def clean_env(monkeypatch: MonkeyPatch) -> None:
    """Clean environment variables."""
    # Remove all MOCK_API_* env vars
    for key in list(os.environ.keys()):
        if key.startswith("MOCK_API_"):
            monkeypatch.delenv(key, raising=False)


@pytest.fixture
def temp_config_yaml(tmp_path: Path) -> Path:
    """Create temporary YAML config file."""
    config_file = tmp_path / "mockapi-server.yml"
    config_file.write_text("""
seed_count: 20
port: 8000
log_level: DEBUG
cors_origins:
  - http://localhost:3000
  - http://example.com
""")
    return config_file


@pytest.fixture
def temp_config_json(tmp_path: Path) -> Path:
    """Create temporary JSON config file."""
    config_file = tmp_path / "mockapi-server.json"
    config_data = {
        "seed_count": 30,
        "port": 9000,
        "log_level": "WARNING",
        "cors_enabled": False,
    }
    config_file.write_text(json.dumps(config_data))
    return config_file


@pytest.fixture(autouse=True)
def reset_config() -> Generator[None, None, None]:
    """Reset global config before and after each test."""
    reset_global_config()
    yield
    reset_global_config()


# =============================================================================
# CONFIG CLASS TESTS
# =============================================================================


def test_config_defaults():
    """Test that Config uses correct default values."""
    config = Config()

    assert config.seed_count == DEFAULT_SEED_COUNT
    assert config.port == DEFAULT_PORT
    assert config.host == DEFAULT_HOST
    assert config.locale == "en_US"
    assert config.log_level == DEFAULT_LOG_LEVEL
    assert config.cors_enabled == DEFAULT_CORS_ENABLED
    assert config.cors_origins == DEFAULT_CORS_ORIGINS
    assert config.auto_reload == DEFAULT_AUTO_RELOAD
    assert config.strict_mode == DEFAULT_STRICT_MODE


def test_config_custom_values():
    """Test creating Config with custom values."""
    config = Config(
        seed_count=50,
        port=5000,
        host="127.0.0.1",
        log_level="ERROR",
        cors_enabled=False,
    )

    assert config.seed_count == 50
    assert config.port == 5000
    assert config.host == "127.0.0.1"
    assert config.log_level == "ERROR"
    assert config.cors_enabled is False


def test_config_port_validation():
    """Test port validation."""
    # Valid ports
    Config(port=1)
    Config(port=8080)
    Config(port=65535)

    # Invalid ports
    with pytest.raises(ValidationError):
        Config(port=0)

    with pytest.raises(ValidationError):
        Config(port=65536)

    with pytest.raises(ValidationError):
        Config(port=-1)


def test_config_seed_count_validation():
    """Test seed count validation."""
    # Valid counts
    Config(seed_count=1)
    Config(seed_count=100)
    Config(seed_count=10000)

    # Invalid counts
    with pytest.raises(ValidationError):
        Config(seed_count=0)

    with pytest.raises(ValidationError):
        Config(seed_count=10001)

    with pytest.raises(ValidationError):
        Config(seed_count=-1)


def test_config_log_level_validation():
    """Test log level validation."""
    # Valid levels
    for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        config = Config(log_level=level)
        assert config.log_level == level

    # Case insensitive
    config = Config(log_level="debug")
    assert config.log_level == "DEBUG"

    # Invalid level
    with pytest.raises(ValidationError):
        Config(log_level="INVALID")


def test_config_locale_validation():
    """Test locale validation."""
    # Valid locales
    Config(locale="en_US")
    Config(locale="fr_FR")
    Config(locale="en")

    # Invalid locales
    with pytest.raises(ValidationError):
        Config(locale="invalid_locale_format")


def test_config_cors_origins_validation():
    """Test CORS origins validation."""
    # Valid
    Config(cors_origins=["*"])
    Config(cors_origins=["http://localhost", "https://example.com"])

    # Invalid - empty list
    with pytest.raises(ValidationError):
        Config(cors_origins=[])


def test_config_extra_fields_forbidden():
    """Test that extra fields are forbidden."""
    with pytest.raises(ValidationError):
        Config(unknown_field="value")  # type: ignore


def test_config_get_log_level_int():
    """Test converting log level to integer."""
    import logging

    config = Config(log_level="DEBUG")
    assert config.get_log_level_int() == logging.DEBUG

    config = Config(log_level="INFO")
    assert config.get_log_level_int() == logging.INFO

    config = Config(log_level="ERROR")
    assert config.get_log_level_int() == logging.ERROR


# =============================================================================
# PAGINATION CONFIG TESTS
# =============================================================================


def test_pagination_config_defaults():
    """Test default pagination configuration values."""
    from mock_api.core.config import PaginationConfig

    pagination = PaginationConfig()

    assert pagination.strategy == "page"
    assert pagination.default_page_size == 20
    assert pagination.default_limit == 20
    assert pagination.max_page_size == 100
    assert pagination.max_limit == 100
    assert pagination.min_page_size == 1
    assert pagination.min_limit == 1


def test_pagination_config_custom_values():
    """Test pagination config with custom values."""
    from mock_api.core.config import PaginationConfig

    pagination = PaginationConfig(
        strategy="offset",
        default_limit=15,
        max_limit=200,
        min_limit=5,
    )

    assert pagination.strategy == "offset"
    assert pagination.default_limit == 15
    assert pagination.max_limit == 200
    assert pagination.min_limit == 5


def test_pagination_config_invalid_strategy():
    """Test validation of invalid pagination strategy."""
    from mock_api.core.config import PaginationConfig

    with pytest.raises(ValidationError, match="Invalid pagination strategy"):
        PaginationConfig(strategy="invalid")


def test_pagination_config_in_main_config():
    """Test pagination config as part of main Config."""
    config = Config()

    assert hasattr(config, "pagination")
    assert config.pagination.strategy == "page"
    assert config.pagination.default_page_size == 20


def test_pagination_config_from_yaml(tmp_path: Path):
    """Test loading pagination config from YAML file."""
    config_file = tmp_path / "mockapi-server.yml"
    config_file.write_text(
        """
pagination:
  strategy: offset
  default_limit: 15
  max_limit: 200
"""
    )

    config = get_config(config_file=config_file)

    assert config.pagination.strategy == "offset"
    assert config.pagination.default_limit == 15
    assert config.pagination.max_limit == 200


def test_pagination_config_from_json(tmp_path: Path):
    """Test loading pagination config from JSON file."""
    config_file = tmp_path / "mockapi-server.json"
    config_file.write_text(
        """
{
  "pagination": {
    "strategy": "offset",
    "default_limit": 25,
    "max_page_size": 150
  }
}
"""
    )

    config = get_config(config_file=config_file)

    assert config.pagination.strategy == "offset"
    assert config.pagination.default_limit == 25
    assert config.pagination.max_page_size == 150


# =============================================================================
# FILE LOADING TESTS
# =============================================================================


def test_load_config_file_yaml(temp_config_yaml: Path) -> None:
    """Test loading configuration from YAML file."""
    config_data = load_config_file(temp_config_yaml)

    assert config_data["seed_count"] == 20
    assert config_data["port"] == 8000
    assert config_data["log_level"] == "DEBUG"
    assert config_data["cors_origins"] == [
        "http://localhost:3000",
        "http://example.com",
    ]


def test_load_config_file_json(temp_config_json: Path) -> None:
    """Test loading configuration from JSON file."""
    config_data = load_config_file(temp_config_json)

    assert config_data["seed_count"] == 30
    assert config_data["port"] == 9000
    assert config_data["log_level"] == "WARNING"
    assert config_data["cors_enabled"] is False


def test_load_config_file_not_found():
    """Test loading non-existent config file."""
    with pytest.raises(ConfigFileNotFoundError):
        load_config_file(Path("nonexistent.yml"))


def test_load_config_file_invalid_json(tmp_path: Path) -> None:
    """Test loading invalid JSON file."""
    config_file = tmp_path / "invalid.json"
    config_file.write_text("{invalid json")

    with pytest.raises(ConfigParseError, match="Invalid JSON"):
        load_config_file(config_file)


def test_load_config_file_invalid_yaml(tmp_path: Path) -> None:
    """Test loading invalid YAML file."""
    pytest.importorskip("yaml")

    config_file = tmp_path / "invalid.yml"
    config_file.write_text("invalid: yaml: syntax:")

    with pytest.raises(ConfigParseError, match="Invalid YAML"):
        load_config_file(config_file)


def test_load_config_file_unsupported_format(tmp_path: Path) -> None:
    """Test loading file with unsupported extension."""
    config_file = tmp_path / "config.txt"
    config_file.write_text("some content")

    with pytest.raises(ConfigParseError, match="Unsupported format"):
        load_config_file(config_file)


def test_load_config_file_yaml_import_error(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Test YAML loading when PyYAML is not installed."""
    config_file = tmp_path / "config.yml"
    config_file.write_text("seed_count: 20")

    # Mock yaml import to fail
    import sys

    monkeypatch.setitem(sys.modules, "yaml", None)

    with pytest.raises(ImportError, match="PyYAML is required"):
        load_config_file(config_file)


# =============================================================================
# ENVIRONMENT VARIABLE TESTS
# =============================================================================


def test_load_from_env_empty(clean_env: None) -> None:
    """Test loading from empty environment."""
    config = load_from_env()
    assert config == {}


def test_load_from_env_integers(clean_env: None, monkeypatch: MonkeyPatch) -> None:
    """Test loading integer values from environment."""
    monkeypatch.setenv("MOCK_API_SEED_COUNT", "25")
    monkeypatch.setenv("MOCK_API_PORT", "7000")

    config = load_from_env()

    assert config["seed_count"] == 25
    assert config["port"] == 7000


def test_load_from_env_booleans(clean_env: None, monkeypatch: MonkeyPatch) -> None:
    """Test loading boolean values from environment."""
    # Test various truthy values
    for value in ["true", "True", "TRUE", "1", "yes", "on"]:
        monkeypatch.setenv("MOCK_API_CORS_ENABLED", value)
        config = load_from_env()
        assert config["cors_enabled"] is True

    # Test falsy values
    for value in ["false", "False", "0", "no", "off"]:
        monkeypatch.setenv("MOCK_API_AUTO_RELOAD", value)
        config = load_from_env()
        assert config["auto_reload"] is False


def test_load_from_env_strings(clean_env: None, monkeypatch: MonkeyPatch) -> None:
    """Test loading string values from environment."""
    monkeypatch.setenv("MOCK_API_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("MOCK_API_HOST", "localhost")

    config = load_from_env()

    assert config["log_level"] == "DEBUG"
    assert config["host"] == "localhost"


def test_load_from_env_lists(clean_env: None, monkeypatch: MonkeyPatch) -> None:
    """Test loading list values from environment."""
    monkeypatch.setenv("MOCK_API_CORS_ORIGINS", "http://localhost,https://example.com")

    config = load_from_env()

    assert config["cors_origins"] == ["http://localhost", "https://example.com"]


def test_load_from_env_ignores_other_vars(
    clean_env: None, monkeypatch: MonkeyPatch
) -> None:
    """Test that non-MOCK_API variables are ignored."""
    monkeypatch.setenv("OTHER_VAR", "value")
    monkeypatch.setenv("MOCK_API_PORT", "8000")

    config = load_from_env()

    assert "OTHER_VAR" not in config
    assert config["port"] == 8000


# =============================================================================
# FIND CONFIG FILE TESTS
# =============================================================================


def test_find_config_file_current_dir(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Test finding config file in current directory."""
    monkeypatch.chdir(tmp_path)

    # Test YAML
    config_file = tmp_path / "mockapi-server.yml"
    config_file.write_text("seed_count: 10")

    found = find_config_file()
    assert found == config_file


def test_find_config_file_parent_dir(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Test finding config file in parent directory."""
    # Create config in parent
    config_file = tmp_path / "mockapi-server.yml"
    config_file.write_text("seed_count: 10")

    # Change to subdirectory
    sub_dir = tmp_path / "subdir"
    sub_dir.mkdir()
    monkeypatch.chdir(sub_dir)

    found = find_config_file()
    assert found == config_file


def test_find_config_file_priority(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Test config file search priority (yml > yaml > json)."""
    monkeypatch.chdir(tmp_path)

    # Create all formats
    yml_file = tmp_path / "mockapi-server.yml"
    yaml_file = tmp_path / "mockapi-server.yaml"
    json_file = tmp_path / "mockapi-server.json"

    yml_file.write_text("seed_count: 1")
    yaml_file.write_text("seed_count: 2")
    json_file.write_text('{"seed_count": 3}')

    # Should find .yml first
    found = find_config_file()
    assert found == yml_file


def test_find_config_file_not_found(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Test when no config file exists."""
    monkeypatch.chdir(tmp_path)

    found = find_config_file()
    assert found is None


# =============================================================================
# GET CONFIG TESTS
# =============================================================================


def test_get_config_defaults(clean_env: None) -> None:
    """Test get_config with only defaults."""
    config = get_config()

    assert config.seed_count == DEFAULT_SEED_COUNT
    assert config.port == DEFAULT_PORT


def test_get_config_from_file(temp_config_yaml: Path) -> None:
    """Test get_config loading from explicit file."""
    config = get_config(config_file=temp_config_yaml)

    assert config.seed_count == 20
    assert config.port == 8000
    assert config.log_level == "DEBUG"


def test_get_config_from_env(clean_env: None, monkeypatch: MonkeyPatch) -> None:
    """Test get_config with environment variables."""
    monkeypatch.setenv("MOCK_API_PORT", "5000")
    monkeypatch.setenv("MOCK_API_LOG_LEVEL", "WARNING")

    config = get_config()

    assert config.port == 5000
    assert config.log_level == "WARNING"


def test_get_config_priority(temp_config_yaml: Path, monkeypatch: MonkeyPatch) -> None:
    """Test configuration priority: env > file > defaults."""
    # File has port=8000
    # Env overrides to port=9000
    monkeypatch.setenv("MOCK_API_PORT", "9000")

    config = get_config(config_file=temp_config_yaml)

    # Env should win
    assert config.port == 9000
    # File value used when no env override
    assert config.seed_count == 20


def test_get_config_auto_discover(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Test automatic config file discovery."""
    monkeypatch.chdir(tmp_path)

    # Create config file
    config_file = tmp_path / "mockapi-server.yml"
    config_file.write_text("seed_count: 15")

    config = get_config()

    assert config.seed_count == 15


# =============================================================================
# GLOBAL CONFIG TESTS
# =============================================================================


def test_get_global_config():
    """Test global config singleton."""
    config1 = get_global_config()
    config2 = get_global_config()

    assert config1 is config2


def test_reset_global_config():
    """Test resetting global config."""
    config1 = get_global_config()
    reset_global_config()
    config2 = get_global_config()

    assert config1 is not config2
