# Release Guide

Guide for creating and publishing releases (maintainers only).

## Quick Reference

```bash
make ci          # Run all CI checks
make build       # Build packages
make publish     # Publish to PyPI
```

## Versioning

### Semantic Versioning

Format: `vMAJOR.MINOR.PATCH[{a|b|rc}N]`

**Components:**

- **MAJOR** - Breaking changes
- **MINOR** - New features (backwards compatible)
- **PATCH** - Bug fixes

**Pre-release:** `aN` (alpha), `bN` (beta), `rcN` (release candidate)

**Examples:**

```
v0.1.0a1    # Alpha
v0.1.0b1    # Beta
v0.1.0rc1   # Release candidate
v0.1.0      # Stable release
v0.1.1      # Patch
v0.2.0      # Minor
v1.0.0      # Major
```

## Release Process

### 1. Pre-release Checks

```bash
git checkout develop
git pull origin develop
make ci  # Must pass
```

### 2. Create Release Branch

```bash
git checkout -b release/v0.1.0
```

### 3. Update Version

Update `pyproject.toml`:

```toml
[project]
version = "0.1.0"
```

Commit:

```bash
git add pyproject.toml
git commit -m "chore: bump version to v0.1.0"
```

### 4. Update Changelog

Update `CHANGELOG.md`:

```markdown
## [0.1.0] - 2026-01-10

### Added

- Initial release features

### Fixed

- Bug fixes from beta

### Changed

- API improvements
```

Commit:

```bash
git add CHANGELOG.md
git commit -m "docs: update changelog for v0.1.0"
```

### 5. Create PR and Merge

```bash
# Rebase on main
git fetch origin main
git rebase origin/main

# Create PR
gh pr create --base main --title "Release v0.1.0"

# Merge with merge commit (NOT squash)
gh pr merge --merge
```

### 6. Tag Release

```bash
git checkout main
git pull
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0  # Triggers PyPI release
```

### 7. Merge Back to Develop

```bash
git checkout develop
git merge main
git push origin develop
```

### 8. Cleanup

```bash
git branch -d release/v0.1.0
```

## Building Packages

```bash
make clean       # Clean previous builds
make build       # Build distribution
make check-package  # Verify package
```

## Publishing

### Test PyPI (Recommended First)

```bash
make publish-test
pip install --index-url https://test.pypi.org/simple/ mockapi-server
mockapi-server --version
```

### Production PyPI

```bash
make publish  # Or: uv run twine upload dist/*
```

## Changelog Format

Follow [Keep a Changelog](https://keepachangelog.com/):

```markdown
## [Unreleased]

### Added

- New features in progress

## [0.1.0] - 2026-01-10

### Added

- Feature list

### Changed

- Changes to existing features

### Fixed

- Bug fixes

### Removed

- Deprecated features
```

**Categories:** Added, Changed, Deprecated, Removed, Fixed, Security

## Hotfix Releases

For urgent bug fixes:

```bash
# Create from main
git checkout main
git checkout -b hotfix/v0.1.1

# Fix bug and update version
# Create PR, merge, tag

git tag -a v0.1.1 -m "Hotfix v0.1.1"
git push origin v0.1.1

# Merge to develop
git checkout develop
git merge main
git push
```

## Release Checklist

**Before:**

- [ ] All tests pass
- [ ] CI pipeline green
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Version bumped

**After:**

- [ ] Tag pushed
- [ ] PyPI published
- [ ] Merged to develop
- [ ] Branch deleted

## GitHub Actions

Releases are automated via GitHub Actions on tag push (`v*.*.*`).

Manual release if automation fails:

```bash
make build
make check-package
uv run twine upload dist/*
```

## Communication

Post on GitHub Releases:

```markdown
# Release v0.1.0

## Highlights

- Feature 1
- Feature 2

## Installation

pip install mockapi-server==0.1.0

## Documentation

https://github.com/sudzxd/mockapi-server
```

## References

- [Semantic Versioning](https://semver.org/)
- [PEP 440](https://peps.python.org/pep-0440/)
- [Keep a Changelog](https://keepachangelog.com/)
