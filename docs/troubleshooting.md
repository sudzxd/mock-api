# Troubleshooting

Solutions to common issues.

## Setup Issues

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'pydantic'`

**Solution:** Install dependencies:

```bash
pip install -e ".[dev]"
# or
make dev
```

### Test Failures

**Problem:** Tests fail after fresh clone

**Solution:**

```bash
make clean
make dev
pytest -v
```

### Type Errors

**Problem:** Pyright reports errors

**Solution:**

```bash
pyright mock_api/  # Check all errors
# Fix imports and type hints
```

### Pre-commit Hook Failures

**Problem:** Hooks fail on commit

**Solution:**

```bash
# Run manually to see errors
pre-commit run --all-files

# Fix issues
make format
make lint-fix

# Skip hooks (not recommended)
git commit --no-verify
```

## Runtime Issues

### Server Won't Start

**Problem:** `FileNotFoundError: models.py not found`

**Solution:** Use correct path:

```bash
# Relative path
mockapi-server serve --models ./path/to/models.py

# Absolute path
mockapi-server serve --models /full/path/to/models.py

# Verify file exists
ls -la models.py
```

**Problem:** `ModuleNotFoundError: No module named 'pydantic'`

**Solution:**

```bash
pip install pydantic
```

**Problem:** Port already in use

**Solution:** Use different port or kill process:

```bash
# Use different port
mockapi-server serve --models models.py --port 8000

# Find and kill process
lsof -i :3000
kill -9 <PID>
```

### Validation Errors

**Problem:** 422 validation errors when creating/updating

**Solution:** Ensure request matches Pydantic model exactly:

```python
class User(BaseModel):
    id: int       # Required
    name: str     # Required
    email: str    # Required
```

All required fields must be present in request. Check `/docs` for exact schema.

### CORS Errors

**Problem:** Browser shows CORS policy errors

**Solution:** Enable CORS in config:

```yaml
# mockapi-server.yml
cors_enabled: true
cors_origins:
  - "*" # Allow all (dev only)
  - "http://localhost:3001" # Specific origin
```

```bash
mockapi-server serve --models models.py --config mockapi-server.yml
```

### Foreign Key Issues

**Problem:** `author_id` references non-existent users

**Solution:** Use `--generate-data` flag for automatic relationship handling:

```bash
mockapi-server serve --models models.py --generate-data
```

Or create parent records first when manually creating data:

```bash
# 1. Create user first
curl -X POST http://localhost:3000/api/v1/users ...

# 2. Then create post with valid author_id
curl -X POST http://localhost:3000/api/v1/posts \
  -d '{"author_id": 1, ...}'
```

## Build/Release Issues

### Build Fails

**Problem:** `uv build` fails

**Solution:**

```bash
make clean
make build
uv run twine check dist/*
```

### Upload Fails

**Problem:** `twine upload` fails

**Solution:** Check PyPI credentials:

```bash
# Verify ~/.pypirc
cat ~/.pypirc

# Regenerate token on PyPI if needed
# Try verbose upload
uv run twine upload dist/* --verbose
```

### Tag Conflicts

**Problem:** Tag already exists

**Solution:**

```bash
# Delete local tag
git tag -d v0.1.0

# Delete remote tag
git push origin --delete v0.1.0

# Re-create
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

## Getting Help

Still stuck? Try:

1. Check [FAQ](faq.md) for common questions
2. Search [existing issues](https://github.com/sudzxd/mockapi-server/issues)
3. Open a new issue with:
   - Error message
   - Steps to reproduce
   - Environment (OS, Python version)
   - Relevant code snippets
