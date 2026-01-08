"""Tests for CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from mock_api.cli.main import cli

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def runner() -> CliRunner:
    """Create Click test runner."""
    return CliRunner()


@pytest.fixture
def models_file() -> str:
    """Path to test models fixture file."""
    return str(Path(__file__).parent / "fixtures" / "generator_models.py")


# =============================================================================
# TESTS: CLI Group
# =============================================================================


def test_cli_help(runner: CliRunner) -> None:
    """Test CLI shows help message."""
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "Mock API" in result.output
    assert "serve" in result.output
    assert "generate" in result.output
    assert "validate" in result.output


def test_cli_version(runner: CliRunner) -> None:
    """Test CLI shows version."""
    result = runner.invoke(cli, ["--version"])

    assert result.exit_code == 0
    assert "1.0.0" in result.output


# =============================================================================
# TESTS: Serve Command
# =============================================================================


def test_serve_help(runner: CliRunner) -> None:
    """Test serve command shows help."""
    result = runner.invoke(cli, ["serve", "--help"])

    assert result.exit_code == 0
    assert "Start the development server" in result.output
    assert "--models" in result.output
    assert "--host" in result.output
    assert "--port" in result.output


def test_serve_requires_models(runner: CliRunner) -> None:
    """Test serve requires --models option."""
    result = runner.invoke(cli, ["serve"])

    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output.lower()


def test_serve_with_nonexistent_file(runner: CliRunner) -> None:
    """Test serve with nonexistent models file."""
    result = runner.invoke(cli, ["serve", "--models", "/nonexistent/models.py"])

    assert result.exit_code != 0


# =============================================================================
# TESTS: Generate Command
# =============================================================================


def test_generate_help(runner: CliRunner) -> None:
    """Test generate command shows help."""
    result = runner.invoke(cli, ["generate", "--help"])

    assert result.exit_code == 0
    assert "Generate mock data files" in result.output
    assert "--models" in result.output
    assert "--output" in result.output
    assert "--count" in result.output


def test_generate_requires_models(runner: CliRunner) -> None:
    """Test generate requires --models option."""
    result = runner.invoke(cli, ["generate"])

    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output.lower()


def test_generate_creates_json_files(runner: CliRunner, models_file: str) -> None:
    """Test generate creates JSON files for each model."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "generate",
                "--models",
                models_file,
                "--output",
                "test_output",
                "--count",
                "5",
            ],
        )

        assert result.exit_code == 0
        assert "Generating mock data" in result.output
        assert "Successfully generated" in result.output

        # Check that output directory was created
        output_dir = Path("test_output")
        assert output_dir.exists()

        # Check that JSON files were created
        assert (output_dir / "contact.json").exists()
        assert (output_dir / "author.json").exists()

        # Verify JSON content
        with (output_dir / "contact.json").open() as f:
            contacts = json.load(f)
            assert len(contacts) == 5
            assert all("id" in c for c in contacts)
            assert all("email" in c for c in contacts)


def test_generate_custom_count(runner: CliRunner, models_file: str) -> None:
    """Test generate with custom count."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, ["generate", "--models", models_file, "--count", "3"]
        )

        assert result.exit_code == 0

        # Verify count
        with Path("data/contact.json").open() as f:
            contacts = json.load(f)
            assert len(contacts) == 3


def test_generate_default_output_dir(runner: CliRunner, models_file: str) -> None:
    """Test generate uses default output directory."""
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["generate", "--models", models_file])

        assert result.exit_code == 0

        # Check default "data" directory
        assert Path("data").exists()
        assert (Path("data") / "contact.json").exists()


def test_generate_with_nonexistent_file(runner: CliRunner) -> None:
    """Test generate with nonexistent models file."""
    result = runner.invoke(cli, ["generate", "--models", "/nonexistent/models.py"])

    assert result.exit_code != 0


# =============================================================================
# TESTS: Validate Command
# =============================================================================


def test_validate_help(runner: CliRunner) -> None:
    """Test validate command shows help."""
    result = runner.invoke(cli, ["validate", "--help"])

    assert result.exit_code == 0
    assert "Validate Pydantic models" in result.output
    assert "--models" in result.output
    assert "--verbose" in result.output


def test_validate_requires_models(runner: CliRunner) -> None:
    """Test validate requires --models option."""
    result = runner.invoke(cli, ["validate"])

    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output.lower()


def test_validate_valid_models(runner: CliRunner, models_file: str) -> None:
    """Test validate with valid models file."""
    result = runner.invoke(cli, ["validate", "--models", models_file])

    assert result.exit_code == 0
    assert "Validating models file" in result.output
    assert "Valid!" in result.output
    assert "Contact" in result.output
    assert "Author" in result.output


def test_validate_verbose(runner: CliRunner, models_file: str) -> None:
    """Test validate with verbose flag."""
    result = runner.invoke(cli, ["validate", "--models", models_file, "--verbose"])

    assert result.exit_code == 0
    assert "Fields:" in result.output
    assert "Relationships:" in result.output


def test_validate_with_nonexistent_file(runner: CliRunner) -> None:
    """Test validate with nonexistent models file."""
    result = runner.invoke(cli, ["validate", "--models", "/nonexistent/models.py"])

    assert result.exit_code != 0


# =============================================================================
# TESTS: Integration
# =============================================================================


def test_cli_all_commands_accessible(runner: CliRunner) -> None:
    """Test all commands are accessible from CLI."""
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0

    # All commands should be listed
    commands = ["serve", "generate", "validate"]
    for cmd in commands:
        assert cmd in result.output


def test_generate_all_models(runner: CliRunner, models_file: str) -> None:
    """Test generate creates files for all models."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, ["generate", "--models", models_file, "--count", "2"]
        )

        assert result.exit_code == 0

        # Expected model files
        expected_files = [
            "contact.json",
            "location.json",
            "article.json",
            "author.json",
            "book.json",
            "review.json",
            "product.json",
            "node.json",
        ]

        output_dir = Path("data")
        for file_name in expected_files:
            file_path = output_dir / file_name
            assert file_path.exists(), f"{file_name} should exist"

            # Verify each file has data
            with file_path.open() as f:
                data = json.load(f)
                assert len(data) == 2, f"{file_name} should have 2 items"
