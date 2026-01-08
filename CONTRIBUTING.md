# Contributing to Mock API

## Ways to Contribute

- Report bugs via GitHub issues
- Suggest features or enhancements
- Submit pull requests with bug fixes or new features
- Improve documentation
- Write tests

## Development Setup

### Prerequisites

- Python 3.11 or higher
- uv package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/sudzxd/mock-api
cd mock-api

# Install dependencies and CLI tool
make dev
```

## Running Tests

```bash
# Run all tests with coverage
make test

# Run tests without coverage (faster)
make test-fast

# Run specific test file
uv run pytest tests/test_parser.py -v
```

## Code Quality

### Linting and Formatting

```bash
# Check code style
make lint

# Auto-fix linting issues
make lint-fix

# Format code
make format
```

### Type Checking

```bash
# Run type checker
make type-check
```

### Running All Checks

```bash
# Run all quality checks (lint, type-check, test)
make check

# Run pre-commit checks (fast)
make pre-commit
```

## Code Style Guidelines

- Follow the project style guide in `docs/development/style-guide.md`
- Use Google-style docstrings
- Use modern type hints: `list[str]` not `List[str]`, `T | None` not `Optional[T]`
- Maximum line length: 88 characters
- Use American English spelling
- Write clear, self-documenting code

## Git Workflow

### Branch Naming Convention

All branches should be created off of `develop` and follow this naming pattern:

```
<type>/<initials>/<issue-number>-<description>
```

Components:
- **type**: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
- **initials**: Your initials (e.g., `ss` for Sudarshan Satyendra Sagar)
- **issue-number**: GitHub issue number
- **description**: Short kebab-case description

Examples:
```bash
feat/ss/1-add-config
fix/ss/5-typescript-parser
docs/ss/4-getting-started
refactor/ss/10-store-optimization
test/ss/23-performance-benchmarks
```

### Development Workflow

1. Create a branch off `develop`:
```bash
git checkout develop
git pull origin develop
git checkout -b feat/ss/1-add-config
```

2. Make your changes following the code style guidelines

3. Run quality checks:
```bash
make check
```

4. Commit your changes with conventional commit messages

5. Push your branch:
```bash
git push origin feat/ss/1-add-config
```

6. Create a pull request targeting `develop` branch

7. After PR approval and merge, delete your feature branch

### Commit Messages

Follow the conventional commits format:

```
<type>: <description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
```
feat: add TypeScript model generator
fix: handle nested optional fields correctly
docs: update CLI reference for new options
```

## Questions or Problems

- Check existing issues and discussions
- Open a new issue if your question hasn't been answered
- Provide as much context as possible

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
