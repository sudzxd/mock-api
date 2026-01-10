# CLI Reference

Complete reference for all mockapi-server commands.

## Global Options

```bash
mockapi-server --version  # Show version
mockapi-server --help     # Show help
```

## Commands

### init

Initialize a new mock API project with scaffolding.

#### Usage

```bash
mockapi-server init [OPTIONS]
```

#### Options

| Option           | Type   | Default       | Description                              |
| ---------------- | ------ | ------------- | ---------------------------------------- |
| `--project-name` | TEXT   | `my-mockapi-server` | Project name                             |
| `--template`     | CHOICE | -             | Template: basic, blog, ecommerce, custom |
| `--models-file`  | TEXT   | `models.py`   | Models file path                         |
| `--seed-count`   | INT    | `10`          | Initial seed data count (1-10000)        |
| `--port`         | INT    | `3000`        | Server port (1024-65535)                 |
| `--force`        | FLAG   | False         | Overwrite existing files                 |

#### Examples

```bash
# Interactive mode (prompts for all options)
mockapi-server init

# Non-interactive with all options
mockapi-server init \
  --template blog \
  --project-name my-blog \
  --seed-count 50 \
  --port 8000

# Use custom models file location
mockapi-server init --models-file src/models.py

# Force overwrite existing files
mockapi-server init --template basic --force
```

#### Created Files

- `models.py` - Pydantic model definitions
- `mockapi-server.yml` - Configuration file
- `README.md` - Project documentation
- `.gitignore` - Git ignore rules

---

### serve

Start the development server.

#### Usage

```bash
mockapi-server serve --models MODELS_FILE [OPTIONS]
```

#### Options

| Option               | Short | Type | Default   | Description            |
| -------------------- | ----- | ---- | --------- | ---------------------- |
| `--models`           | `-m`  | PATH | Required  | Path to models file    |
| `--host`             | `-h`  | TEXT | `0.0.0.0` | Host to bind server    |
| `--port`             | `-p`  | INT  | `3000`    | Port to bind server    |
| `--reload`           | -     | FLAG | False     | Enable auto-reload     |
| `--no-reload`        | -     | FLAG | -         | Disable auto-reload    |
| `--generate-data`    | -     | FLAG | False     | Pre-populate with data |
| `--no-generate-data` | -     | FLAG | -         | Skip data generation   |
| `--data-count`       | `-c`  | INT  | `10`      | Instances per model    |
| `--prefix`           | -     | TEXT | `/api/v1` | API route prefix       |
| `--config`           | -     | PATH | -         | Config file path       |

#### Examples

```bash
# Basic server start
mockapi-server serve --models models.py

# With data generation
mockapi-server serve --models models.py --generate-data --data-count 50

# Custom host and port
mockapi-server serve -m models.py --host localhost --port 8000

# With auto-reload for development
mockapi-server serve -m models.py --reload

# Custom API prefix
mockapi-server serve -m models.py --prefix /v2/api

# Using config file
mockapi-server serve --models models.py --config custom-config.yml
```

#### Server URLs

Once started, access:

- **API Base**: `http://{host}:{port}/api/v1`
- **Swagger Docs**: `http://{host}:{port}/docs`
- **ReDoc**: `http://{host}:{port}/redoc`

---

### generate

Generate mock data files without starting a server.

#### Usage

```bash
mockapi-server generate --models MODELS_FILE [OPTIONS]
```

#### Options

| Option     | Short | Type   | Default  | Description          |
| ---------- | ----- | ------ | -------- | -------------------- |
| `--models` | `-m`  | PATH   | Required | Path to models file  |
| `--output` | `-o`  | PATH   | `data`   | Output directory     |
| `--count`  | `-c`  | INT    | `10`     | Instances per model  |
| `--format` | `-f`  | CHOICE | `json`   | Output format (json) |
| `--config` | -     | PATH   | -        | Config file path     |

#### Examples

```bash
# Generate data to default directory
mockapi-server generate --models models.py

# Generate 100 instances per model
mockapi-server generate -m models.py --count 100

# Custom output directory
mockapi-server generate -m models.py --output ./fixtures

# Using config file
mockapi-server generate --models models.py --config my-config.yml
```

#### Output

Creates one JSON file per model:

```
data/
├── user.json
├── post.json
└── comment.json
```

Example output format:

```json
[
  {
    "id": 1,
    "name": "Alice Johnson",
    "email": "alice.johnson@example.com",
    "created_at": "2025-01-10T10:30:00Z"
  },
  {
    "id": 2,
    "name": "Bob Smith",
    "email": "bob.smith@example.com",
    "created_at": "2025-01-09T14:22:00Z"
  }
]
```

---

### validate

Validate Pydantic models file.

#### Usage

```bash
mockapi-server validate --models MODELS_FILE [OPTIONS]
```

#### Options

| Option      | Short | Type | Default  | Description         |
| ----------- | ----- | ---- | -------- | ------------------- |
| `--models`  | `-m`  | PATH | Required | Path to models file |
| `--verbose` | `-v`  | FLAG | False    | Show detailed info  |

#### Examples

```bash
# Basic validation
mockapi-server validate --models models.py

# Verbose output with field details
mockapi-server validate -m models.py --verbose
```

#### Output

Basic:

```
🔍 Validating models file...
📁 File: models.py

✅ Valid! Found 3 model(s):

  📦 User
  📦 Post
  📦 Comment

💡 Use --verbose for detailed model information
```

Verbose:

```
🔍 Validating models file...
📁 File: models.py

✅ Valid! Found 3 model(s):

  📦 User
     Fields: 5
       - id: int
       - name: str
       - email: str
       - age: int (optional)
       - created_at: datetime

  📦 Post
     Fields: 5
       - id: int
       - title: str
       - content: str
       - author_id: int → User
       - published: bool
     Relationships: 1
       - author → User (many_to_one)

  📦 Comment
     Fields: 4
       - id: int
       - text: str
       - post_id: int → Post
       - user_id: int → User
     Relationships: 2
       - post → Post (many_to_one)
       - user → User (many_to_one)
```

---

## Configuration File

Create `mockapi-server.yml` to avoid repeating options:

```yaml
# Server settings
host: 0.0.0.0
port: 3000
auto_reload: false

# Data generation
seed_count: 50

# Logging
log_level: INFO # DEBUG, INFO, WARNING, ERROR

# CORS
cors_enabled: true
cors_origins:
  - "*"
  - "http://localhost:3001"
```

CLI options override config file values:

```bash
# Port from config: 3000
mockapi-server serve --models models.py --config mockapi-server.yml

# Port from CLI: 8000 (overrides config)
mockapi-server serve --models models.py --config mockapi-server.yml --port 8000
```

---

## Exit Codes

| Code | Meaning                                         |
| ---- | ----------------------------------------------- |
| `0`  | Success                                         |
| `1`  | Error (file not found, validation failed, etc.) |

---

## Environment Variables

Currently, mockapi-server does not use environment variables. All configuration is done via CLI options or config files.

---

## Tips

- Use `--reload` during development for automatic restarts
- Use `--generate-data` to start with realistic test data
- Use config files for project-specific settings
- Use `validate --verbose` to understand detected relationships
- Generate data files once, reuse in tests
