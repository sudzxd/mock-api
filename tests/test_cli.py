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


# =============================================================================
# TESTS: Init Command
# =============================================================================


def test_init_help(runner: CliRunner) -> None:
    """Test init command shows help."""
    result = runner.invoke(cli, ["init", "--help"])

    assert result.exit_code == 0
    assert "Initialize a new mock API project" in result.output
    assert "--project-name" in result.output
    assert "--template" in result.output
    assert "--models-file" in result.output
    assert "--seed-count" in result.output
    assert "--port" in result.output
    assert "--force" in result.output


def test_init_basic_template(runner: CliRunner) -> None:
    """Test init with basic template in non-interactive mode."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "init",
                "--template",
                "basic",
                "--project-name",
                "test-basic",
                "--models-file",
                "models.py",
                "--seed-count",
                "10",
                "--port",
                "3000",
            ],
        )

        assert result.exit_code == 0
        assert "Project initialized successfully" in result.output

        # Check all files were created
        assert Path("models.py").exists()
        assert Path("mock-api.yml").exists()
        assert Path("README.md").exists()
        assert Path(".gitignore").exists()

        # Verify models.py content
        models = Path("models.py").read_text()
        assert "class User(BaseModel):" in models
        assert "id: int" in models
        assert "email: str" in models

        # Verify config content
        config = Path("mock-api.yml").read_text()
        assert "seed_count: 10" in config
        assert "port: 3000" in config

        # Verify README content
        readme = Path("README.md").read_text()
        assert "test-basic" in readme
        assert "3000" in readme


def test_init_blog_template(runner: CliRunner) -> None:
    """Test init with blog template."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "init",
                "--template",
                "blog",
                "--project-name",
                "my-blog",
                "--models-file",
                "models.py",
                "--seed-count",
                "20",
                "--port",
                "8000",
            ],
        )

        assert result.exit_code == 0

        # Verify models.py has all blog models
        models = Path("models.py").read_text()
        assert "class User(BaseModel):" in models
        assert "class Post(BaseModel):" in models
        assert "class Comment(BaseModel):" in models
        assert "author_id: int" in models  # FK relationship
        assert "post_id: int" in models  # FK relationship


def test_init_ecommerce_template(runner: CliRunner) -> None:
    """Test init with ecommerce template."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "init",
                "--template",
                "ecommerce",
                "--project-name",
                "my-shop",
                "--models-file",
                "models.py",
                "--seed-count",
                "10",
                "--port",
                "3000",
            ],
        )

        assert result.exit_code == 0

        # Verify models.py has ecommerce models
        models = Path("models.py").read_text()
        assert "class Category(BaseModel):" in models
        assert "class Product(BaseModel):" in models
        assert "class Customer(BaseModel):" in models
        assert "class Order(BaseModel):" in models
        assert "OrderStatus" in models  # Enum


def test_init_custom_template(runner: CliRunner) -> None:
    """Test init with custom template."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "init",
                "--template",
                "custom",
                "--project-name",
                "custom-api",
                "--models-file",
                "models.py",
                "--seed-count",
                "10",
                "--port",
                "3000",
            ],
        )

        assert result.exit_code == 0

        # Verify models.py has guidance comments
        models = Path("models.py").read_text()
        assert "Define your Pydantic models here" in models
        assert "class Example(BaseModel):" in models


def test_init_interactive_mode(runner: CliRunner) -> None:
    """Test init in interactive mode with user input."""
    with runner.isolated_filesystem():
        # Simulate user input: project name, template choice, models file,
        # seed count, port, confirm
        user_input = "test-project\n1\nmodels.py\n15\n4000\ny\n"

        result = runner.invoke(cli, ["init"], input=user_input)

        assert result.exit_code == 0
        assert "Project name" in result.output
        assert "Choose a template:" in result.output
        assert "Continue?" in result.output
        assert "Project initialized successfully" in result.output

        # Verify files were created
        assert Path("models.py").exists()
        assert Path("mock-api.yml").exists()


def test_init_file_exists_error(runner: CliRunner) -> None:
    """Test init fails when files already exist without --force."""
    with runner.isolated_filesystem():
        # Create existing file
        Path("models.py").write_text("# existing content")

        result = runner.invoke(
            cli,
            [
                "init",
                "--template",
                "basic",
                "--project-name",
                "test",
                "--models-file",
                "models.py",
                "--seed-count",
                "10",
                "--port",
                "3000",
            ],
        )

        assert result.exit_code != 0
        assert "Files already exist" in result.output


def test_init_force_overwrite(runner: CliRunner) -> None:
    """Test init with --force overwrites existing files."""
    with runner.isolated_filesystem():
        # Create existing file
        Path("models.py").write_text("# existing content")

        result = runner.invoke(
            cli,
            [
                "init",
                "--template",
                "basic",
                "--project-name",
                "test",
                "--models-file",
                "models.py",
                "--seed-count",
                "10",
                "--port",
                "3000",
                "--force",
            ],
        )

        assert result.exit_code == 0
        assert "Project initialized successfully" in result.output

        # Verify file was overwritten
        models = Path("models.py").read_text()
        assert "class User(BaseModel):" in models
        assert "# existing content" not in models


def test_init_invalid_project_name(runner: CliRunner) -> None:
    """Test init fails with invalid project name."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "init",
                "--template",
                "basic",
                "--project-name",
                "my project!",  # Invalid: contains space and !
            ],
        )

        assert result.exit_code != 0
        assert "Invalid project name" in result.output


def test_init_custom_models_file_path(runner: CliRunner) -> None:
    """Test init with custom models file path."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "init",
                "--template",
                "basic",
                "--project-name",
                "test",
                "--models-file",
                "custom_models.py",
                "--seed-count",
                "10",
                "--port",
                "3000",
            ],
        )

        assert result.exit_code == 0

        # Verify custom file name was used
        assert Path("custom_models.py").exists()
        assert not Path("models.py").exists()


def test_init_generated_files_work_with_validate(runner: CliRunner) -> None:
    """Test generated files work with validate command."""
    with runner.isolated_filesystem():
        # Initialize project
        init_result = runner.invoke(
            cli,
            [
                "init",
                "--template",
                "blog",
                "--project-name",
                "test",
                "--models-file",
                "models.py",
                "--seed-count",
                "10",
                "--port",
                "3000",
            ],
        )
        assert init_result.exit_code == 0

        # Validate generated models
        validate_result = runner.invoke(cli, ["validate", "--models", "models.py"])

        assert validate_result.exit_code == 0
        assert "Valid!" in validate_result.output
        assert "User" in validate_result.output
        assert "Post" in validate_result.output
        assert "Comment" in validate_result.output


def test_init_generated_files_work_with_generate(runner: CliRunner) -> None:
    """Test generated files work with generate command."""
    with runner.isolated_filesystem():
        # Initialize project
        init_result = runner.invoke(
            cli,
            [
                "init",
                "--template",
                "basic",
                "--project-name",
                "test",
                "--models-file",
                "models.py",
                "--seed-count",
                "10",
                "--port",
                "3000",
            ],
        )
        assert init_result.exit_code == 0

        # Generate data using created models
        generate_result = runner.invoke(
            cli, ["generate", "--models", "models.py", "--count", "3"]
        )

        assert generate_result.exit_code == 0
        assert "Successfully generated" in generate_result.output

        # Verify generated data file
        assert Path("data/user.json").exists()
        with Path("data/user.json").open() as f:
            users = json.load(f)
            assert len(users) == 3


def test_init_seed_count_validation(runner: CliRunner) -> None:
    """Test init validates seed count range."""
    with runner.isolated_filesystem():
        # Test minimum bound
        result = runner.invoke(
            cli,
            [
                "init",
                "--template",
                "basic",
                "--project-name",
                "test",
                "--seed-count",
                "0",  # Invalid: below MIN_SEED_COUNT (1)
            ],
        )
        # Click's IntRange will fail before our code runs
        assert result.exit_code != 0


def test_init_port_validation(runner: CliRunner) -> None:
    """Test init validates port range."""
    with runner.isolated_filesystem():
        # Test minimum bound
        result = runner.invoke(
            cli,
            [
                "init",
                "--template",
                "basic",
                "--project-name",
                "test",
                "--port",
                "0",  # Invalid: below MIN_PORT (1)
            ],
        )
        # Click's IntRange will fail before our code runs
        assert result.exit_code != 0


def test_init_all_templates_accessible(runner: CliRunner) -> None:
    """Test all template types can be initialized."""
    templates = ["basic", "blog", "ecommerce", "custom"]

    for template in templates:
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                [
                    "init",
                    "--template",
                    template,
                    "--project-name",
                    f"test-{template}",
                    "--models-file",
                    "models.py",
                    "--seed-count",
                    "10",
                    "--port",
                    "3000",
                ],
            )

            assert result.exit_code == 0, f"Template {template} failed"
            assert Path("models.py").exists()


def test_init_gitignore_created(runner: CliRunner) -> None:
    """Test init creates .gitignore file."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "init",
                "--template",
                "basic",
                "--project-name",
                "test",
                "--models-file",
                "models.py",
                "--seed-count",
                "10",
                "--port",
                "3000",
            ],
        )

        assert result.exit_code == 0

        # Verify .gitignore exists and has Python patterns
        gitignore = Path(".gitignore").read_text()
        assert "__pycache__/" in gitignore
        assert "*.py[cod]" in gitignore  # Covers .pyc, .pyo, .pyd
        assert "venv/" in gitignore


def test_init_command_listed_in_help(runner: CliRunner) -> None:
    """Test init command is listed in main CLI help."""
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "init" in result.output


def test_init_interactive_cancel(runner: CliRunner) -> None:
    """Test init can be cancelled in interactive mode."""
    with runner.isolated_filesystem():
        # Simulate user input: accept all prompts but decline at confirmation
        user_input = "test-project\n1\nmodels.py\n10\n3000\nn\n"

        result = runner.invoke(cli, ["init"], input=user_input)

        # Should exit successfully but not create files
        assert result.exit_code == 0
        assert "Initialization cancelled" in result.output
        assert not Path("models.py").exists()
