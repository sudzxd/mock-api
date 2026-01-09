# Testing Guide

Testing practices and guidelines for mock-api.

## Quick Start

```bash
make test          # Tests with coverage
make test-fast     # Fast (no coverage)
make benchmark     # Performance benchmarks
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── fixtures/                # Test data models
├── test_*.py                # Unit tests
└── benchmarks/              # Performance tests
```

## Test Naming

```
test_<component>_<scenario>_<expected>
```

**Examples:**

```python
def test_parser_with_valid_models_extracts_all_fields():
    """Parser should extract all fields from valid Pydantic models."""
    pass

def test_generator_with_email_field_creates_valid_email():
    """Generator should create valid email for fields named 'email'."""
    pass
```

## Writing Tests

### Basic Structure

```python
def test_feature():
    """Test description."""
    # Arrange
    parser = SchemaParser()

    # Act
    result = parser.parse_file("test.py")

    # Assert
    assert result is not None
    assert "User" in result
```

### Parametrized Tests

```python
import pytest

@pytest.mark.parametrize("field_name,field_type", [
    ("email", str),
    ("age", int),
    ("active", bool),
])
def test_field_types(field_name, field_type):
    """Test field type extraction."""
    # Test implementation
    pass
```

### Testing Exceptions

```python
def test_parser_with_missing_file_raises_error():
    """Parser should raise FileNotFoundError."""
    parser = SchemaParser()

    with pytest.raises(FileNotFoundError):
        parser.parse_file("nonexistent.py")
```

## Running Tests

### Make Commands

```bash
make test          # Tests with coverage
make test-fast     # Fast (no coverage)
make test-unit     # Unit tests only
make test-cov      # View HTML coverage report
make benchmark     # Run benchmarks
```

## Coverage

### Targets

| Component | Target |
| --------- | ------ |
| Parser    | 95%    |
| Generator | 90%    |
| Store     | 100%   |
| Router    | 95%    |
| Overall   | 90%    |

### Checking Coverage

```bash
pytest --cov=mock_api --cov-report=term-missing
pytest --cov=mock_api --cov-report=html
open htmlcov/index.html
```

## Benchmarks

```bash
make benchmark           # Run benchmarks
make benchmark-compare   # Compare with baseline
make benchmark-save      # Save new baseline
```

### Writing Benchmarks

```python
def test_parser_performance(benchmark):
    """Parser should parse 10 models in < 10ms."""
    parser = SchemaParser()
    result = benchmark(parser.parse_file, "tests/fixtures/benchmark_models.py")
    assert len(result) == 10
```

## Best Practices

### DO

- Write tests first (TDD for bugs)
- Test one thing per test
- Use descriptive names
- Keep tests fast (< 100ms)
- Test edge cases

### DON'T

- Test implementation details
- Create test dependencies
- Skip tests without reason
- Use sleep() for timing

## CI Integration

Tests run on every push and PR. CI runs:

```bash
make ci
```

Includes:

1. Format check
2. Linting
3. Type checking
4. Tests with coverage
5. Coverage threshold (90%)

## References

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [pytest-benchmark](https://pytest-benchmark.readthedocs.io/)
