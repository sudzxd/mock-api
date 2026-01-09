# Makefile for mock-api development
# Follows project style guide conventions
# Uses: uv, ruff, pyright, pytest

.PHONY: help install dev test lint format type-check security clean build publish docs

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

##@ General

help: ## Display this help message
	@echo "$(BLUE)mock-api development commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(GREEN)<target>$(NC)\n"} \
		/^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 } \
		/^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Installation

install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	uv sync --no-dev

dev: ## Install all dependencies (including dev) and CLI tool
	@echo "$(BLUE)Installing all dependencies...$(NC)"
	uv sync --all-extras
	@echo "$(BLUE)Installing CLI tool (editable)...$(NC)"
	uv tool install --editable . --force
	@echo "$(GREEN)✓ Dependencies installed$(NC)"
	@echo "$(GREEN)✓ mock-api command available$(NC)"

##@ Development

run: ## Run example server (examples/blog/models.py)
	@echo "$(BLUE)Starting mock API server...$(NC)"
	uv run python -m mock_api.cli.main serve --models examples/basic/models.py --generate-data --port 8000

shell: ## Start interactive Python shell with project loaded
	@echo "$(BLUE)Starting Python shell...$(NC)"
	uv run python

##@ Testing

test: ## Run all tests with coverage
	@echo "$(BLUE)Running tests...$(NC)"
	uv run pytest --cov=mock_api --cov-report=term-missing --cov-report=html --cov-report=xml -v

test-fast: ## Run tests without coverage (fast)
	@echo "$(BLUE)Running tests (fast mode)...$(NC)"
	uv run pytest -v

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	uv run pytest-watch

test-unit: ## Run only unit tests
	@echo "$(BLUE)Running unit tests...$(NC)"
	uv run pytest tests/test_*.py -v

test-cov: ## Show coverage report in browser
	@echo "$(BLUE)Opening coverage report...$(NC)"
	open htmlcov/index.html

##@ Code Quality

lint: ## Run ruff linter
	@echo "$(BLUE)Running ruff linter...$(NC)"
	uv run ruff check .

lint-fix: ## Run ruff linter with auto-fix
	@echo "$(BLUE)Running ruff linter (auto-fix)...$(NC)"
	uv run ruff check --fix .

format: ## Format code with ruff
	@echo "$(BLUE)Formatting code...$(NC)"
	uv run ruff format .

format-check: ## Check code formatting without changes
	@echo "$(BLUE)Checking code formatting...$(NC)"
	uv run ruff format --check .

type-check: ## Run pyright type checker
	@echo "$(BLUE)Running type checker...$(NC)"
	uv run pyright

##@ Security

security: ## Run security checks (bandit + pip-audit)
	@echo "$(BLUE)Running security checks...$(NC)"
	uv run bandit -r mock_api/ -ll
	uv run pip-audit

##@ Quality Gates

check: lint type-check test ## Run all quality checks (lint, type-check, test)
	@echo "$(GREEN)✓ All quality checks passed!$(NC)"

pre-commit: format lint type-check test-fast ## Run pre-commit checks (fast)
	@echo "$(GREEN)✓ Pre-commit checks passed!$(NC)"

ci: format-check lint type-check test ## Run CI pipeline checks
	@echo "$(GREEN)✓ CI checks passed!$(NC)"

##@ Cleaning

clean: ## Remove build artifacts and cache files
	@echo "$(BLUE)Cleaning up...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "$(GREEN)✓ Cleaned$(NC)"

clean-all: clean ## Remove all generated files including venv
	@echo "$(BLUE)Removing virtual environment...$(NC)"
	rm -rf .venv/
	@echo "$(GREEN)✓ Deep clean complete$(NC)"

##@ Building & Publishing

build: clean ## Build distribution packages
	@echo "$(BLUE)Building package...$(NC)"
	uv build
	@echo "$(GREEN)✓ Build complete$(NC)"
	@ls -lh dist/

check-package: build ## Check package with twine
	@echo "$(BLUE)Checking package...$(NC)"
	uv run twine check dist/*

publish-test: build check-package ## Publish to TestPyPI
	@echo "$(YELLOW)Publishing to TestPyPI...$(NC)"
	uv run twine upload --repository testpypi dist/*
	@echo "$(GREEN)✓ Published to TestPyPI$(NC)"
	@echo "Test install: pip install --index-url https://test.pypi.org/simple/ mock-api"

publish: build check-package ## Publish to PyPI (PRODUCTION)
	@echo "$(RED)WARNING: Publishing to production PyPI!$(NC)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ]
	uv run twine upload dist/*
	@echo "$(GREEN)✓ Published to PyPI$(NC)"

##@ Documentation

docs: ## Build documentation
	@echo "$(BLUE)Building documentation...$(NC)"
	@echo "$(YELLOW)⚠ mkdocs not configured yet$(NC)"

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation...$(NC)"
	@echo "$(YELLOW)⚠ mkdocs not configured yet$(NC)"

##@ Git Hooks

hooks-install: ## Install pre-commit hooks
	@echo "$(BLUE)Installing pre-commit hooks...$(NC)"
	pre-commit install
	@echo "$(GREEN)✓ Pre-commit hooks installed$(NC)"

hooks-update: ## Update pre-commit hooks
	@echo "$(BLUE)Updating pre-commit hooks...$(NC)"
	pre-commit autoupdate

hooks-run: ## Run pre-commit hooks on all files
	@echo "$(BLUE)Running pre-commit hooks...$(NC)"
	pre-commit run --all-files

##@ Information

info: ## Show project information
	@echo "$(BLUE)Project Information$(NC)"
	@echo "-------------------"
	@echo "Project: mock-api"
	@echo "Python: $$(python --version)"
	@echo "uv: $$(uv --version)"
	@echo "Path: $$(pwd)"
	@echo ""
	@echo "$(BLUE)Installed Packages:$(NC)"
	@uv pip list | head -20

version: ## Show version information
	@echo "$(BLUE)Version Information$(NC)"
	@echo "-------------------"
	@uv run python -c "import mock_api; print(f'mock-api: {mock_api.__version__ if hasattr(mock_api, \"__version__\") else \"dev\"}')" 2>/dev/null || echo "mock-api: dev"
	@echo "Python: $$(python --version)"
	@echo "uv: $$(uv --version)"
	@echo "ruff: $$(uv run ruff --version)"
	@echo "pyright: $$(uv run pyright --version)"
	@echo "pytest: $$(uv run pytest --version)"

deps: ## Show dependency tree
	@echo "$(BLUE)Dependency Tree$(NC)"
	@echo "---------------"
	@uv pip tree

##@ Benchmarking

benchmark: ## Run performance benchmarks
	@echo "$(BLUE)Running benchmarks...$(NC)"
	uv run pytest tests/benchmarks/ --benchmark-only -v

benchmark-compare: ## Run benchmarks with comparison to baseline
	@echo "$(BLUE)Running benchmarks with comparison...$(NC)"
	uv run pytest tests/benchmarks/ --benchmark-only --benchmark-compare -v

benchmark-save: ## Run benchmarks and save as new baseline
	@echo "$(BLUE)Running benchmarks and saving baseline...$(NC)"
	uv run pytest tests/benchmarks/ --benchmark-only --benchmark-autosave -v

benchmark-report: ## Generate benchmark histogram report
	@echo "$(BLUE)Generating benchmark report...$(NC)"
	uv run pytest tests/benchmarks/ --benchmark-only --benchmark-histogram -v
	@echo "$(GREEN)Report saved to .benchmarks/$(NC)"

##@ Examples

example-basic: ## Run basic example
	@echo "$(BLUE)Running basic example...$(NC)"
	uv run python -m mock_api.cli.main validate --models examples/basic/models.py --verbose || \
		echo "$(YELLOW)⚠ Create examples/basic/models.py first$(NC)"

example-blog: ## Run blog example
	@echo "$(BLUE)Running blog example...$(NC)"
	uv run python -m mock_api.cli.main serve --models examples/blog/models.py --generate-data --data-count 20 || \
		echo "$(YELLOW)⚠ Create examples/blog/models.py first$(NC)"

##@ Workflow Shortcuts

all: clean dev lint type-check test ## Clean, install, and run all checks
	@echo "$(GREEN)✓ Full workflow complete!$(NC)"

quick: lint-fix test-fast ## Quick check (format + fast tests)
	@echo "$(GREEN)✓ Quick check complete!$(NC)"

release: ci build publish ## Full release workflow (CI + build + publish)
	@echo "$(GREEN)✓ Release complete!$(NC)"
