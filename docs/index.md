# mockapi-server Documentation

Professional mock REST API server that generates fully-functional APIs from schema definitions.

## Overview

**mockapi-server** parses schema files (Pydantic, OpenAPI, GraphQL), generates realistic test data using Faker, and serves complete REST APIs with CRUD operations, filtering, sorting, pagination, and relationship handling.

**Tech Stack:** Python 3.11+ | Pydantic v2 | FastAPI | Faker | Click CLI

## User Guide

### Getting Started

- **[Getting Started](getting-started.md)** - Installation and first API in 5 minutes
- **[CLI Reference](cli-reference.md)** - Complete command-line interface reference
- **[API Reference](api-reference.md)** - REST endpoint documentation and Python API
- **[Examples](examples.md)** - Common patterns and usage scenarios

### Help & Resources

- **[FAQ](faq.md)** - Frequently asked questions and answers
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
- **[Architecture](architecture.md)** - DDD architecture and design patterns

## Developer Guide

### Contributing

- **[Development Setup](development/setup.md)** - Local environment configuration
- **[Guidelines](development/guidelines.md)** - Code standards, Git workflow, SOLID principles
- **[Testing](development/testing.md)** - Test strategy and coverage requirements
- **[Releasing](development/releasing.md)** - Version management and release process

### External Resources

- **GitHub:** [github.com/sudzxd/mockapi-server](https://github.com/sudzxd/mockapi-server)
- **Issues:** [github.com/sudzxd/mockapi-server/issues](https://github.com/sudzxd/mockapi-server/issues)
- **PyPI:** [pypi.org/project/mockapi-server](https://pypi.org/project/mockapi-server/)

## Quick Reference

**Installation:**
```bash
pip install mockapi-server
```

**Basic Usage:**
```bash
mockapi-server init
mockapi-server serve models.py --generate-data
```

**Interactive Documentation:** `http://localhost:3000/docs`

## Project Status

Active development. Production-ready for development and testing environments.
