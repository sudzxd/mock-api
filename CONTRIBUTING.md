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

### Release Workflow

Releases are handled by maintainers. When ready to release a new version:

1. **Create release branch** off `develop`:
```bash
git checkout develop
git pull origin develop
git checkout -b release/vX.Y.Z
```

2. **Rebase on main** to ensure a clean history:
```bash
git fetch origin main
git rebase origin/main
```

3. **Create PR to main**:
```bash
gh pr create --base main --head release/vX.Y.Z \
  --title "Release vX.Y.Z" \
  --body "Release vX.Y.Z"
```

4. **Merge using merge commit** (not squash):
```bash
gh pr merge --merge
```

5. **Tag the release** after merge:
```bash
git checkout main
git pull origin main
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```

6. **Merge back to develop**:
```bash
git checkout develop
git pull origin develop
git merge main
git push origin develop
```

7. **Delete release branch**:
```bash
git branch -d release/vX.Y.Z
git push origin --delete release/vX.Y.Z
```

**Note**: Pushing a tag automatically triggers PyPI release via GitHub Actions.

### Tagging Strategy

We follow **semantic versioning** with **PEP 440** pre-release format:

**Format**: `vMAJOR.MINOR.PATCH[{a|b|rc}N]`

**Version Components**:
- **MAJOR**: Breaking changes (incompatible API changes)
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

**Pre-release Identifiers** (PEP 440):
- **aN**: Alpha releases (early development, unstable)
- **bN**: Beta releases (feature complete, testing phase)
- **rcN**: Release candidates (final testing before stable)

**Examples**:
```bash
# Alpha releases (early development)
v0.1.0a1
v0.1.0a2
v0.1.0a3

# Beta releases (feature complete, testing)
v0.1.0b1
v0.1.0b2

# Release candidates (final testing)
v0.1.0rc1
v0.1.0rc2

# Stable release
v0.1.0

# Patch releases
v0.1.1
v0.1.2

# Minor releases with pre-releases
v0.2.0a1  # Alpha for v0.2.0
v0.2.0b1  # Beta for v0.2.0
v0.2.0rc1 # RC for v0.2.0
v0.2.0    # Stable v0.2.0

# Major releases
v1.0.0rc1 # RC for v1.0.0
v1.0.0    # Stable v1.0.0
```

**Release Types**:
- **Patch** (X.Y.Z → X.Y.Z+1): Bug fixes, documentation
- **Minor** (X.Y.Z → X.Y+1.0): New features, backwards compatible
- **Major** (X.Y.Z → X+1.0.0): Breaking changes

**Release Process**:
- All tags are created on the `main` branch after merging
- Pushing a tag automatically triggers PyPI release
- Pre-releases (a, b, rc) are published to PyPI as pre-releases
- Stable releases have no pre-release identifier

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
