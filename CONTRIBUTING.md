# Contributing to Mock API

Thanks for your interest in contributing!

## Quick Start

```bash
git clone https://github.com/sudzxd/mock-api
cd mock-api
make dev
make hooks-install
make check
```

## Ways to Contribute

- Report bugs via GitHub issues
- Suggest features or enhancements
- Submit pull requests
- Improve documentation
- Write tests

## Development Workflow

1. **Create branch** off `develop` (see [guidelines](docs/development/guidelines.md))
2. **Make changes** following [code standards](docs/development/guidelines.md#code-style)
3. **Run checks:** `make check`
4. **Commit** with [conventional format](docs/development/guidelines.md#commit-messages)
5. **Push and create PR:** `gh pr create --base develop`

## Before Submitting

- [ ] Tests pass (`make test`)
- [ ] Code formatted (`make format`)
- [ ] Linting passes (`make lint`)
- [ ] Type checking passes (`make type-check`)
- [ ] Documentation updated
- [ ] Commit messages follow conventions

Quick check: `make pre-commit`

## Documentation

See comprehensive guides:
- [Development Setup](docs/development/setup.md)
- [Guidelines](docs/development/guidelines.md)
- [Testing](docs/development/testing.md)

## Getting Help

- Check existing [issues](https://github.com/sudzxd/mock-api/issues)
- Read [documentation](docs/)
- Open a new issue with details

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
