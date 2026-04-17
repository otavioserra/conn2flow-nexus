# 14. Python Ecosystem & Tooling

This module covers the tools, workflows, and ecosystem around Python development — everything that's **not** the language itself but is essential for professional work.

---

## Package Management — pip & venv

### PHP Equivalent
| PHP | Python |
|-----|--------|
| Composer | pip |
| `composer.json` | `pyproject.toml` or `requirements.txt` |
| `composer.lock` | `requirements.txt` (pinned) |
| `vendor/` | `.venv/lib/` |
| `composer require pkg` | `pip install pkg` |
| `composer install` | `pip install -r requirements.txt` |

### Virtual Environments
```bash
# Create virtual environment
python -m venv .venv

# Activate (Linux/macOS)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Verify
which python  # Should point to .venv/bin/python
python --version

# Install dependencies
pip install -r requirements.txt

# Deactivate
deactivate
```

**Why venv?** Each project gets its own isolated Python + packages. No global pollution. Like PHP's `vendor/` but for the entire Python interpreter.

### Requirements Files
```
# requirements.txt (production)
fastapi==0.136.0
uvicorn[standard]==0.34.3
pydantic==2.12.5
pydantic-settings==2.13.1
aiokafka==0.13.0
redis[hiredis]==5.3.0
litellm==1.83.9
langgraph==1.1.7
httpx==0.28.1
orjson==3.11.0

# requirements-dev.txt
-r requirements.txt
pytest==8.4.2
pytest-asyncio==0.26.0
```

```bash
pip install -r requirements.txt       # Production
pip install -r requirements-dev.txt   # Development (includes prod)
```

---

## `pyproject.toml` — Modern Config

```toml
[project]
name = "conn2flow-nexus-ai"
version = "0.1.0"
requires-python = ">=3.11"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP"]

[tool.mypy]
python_version = "3.11"
strict = true
```

`pyproject.toml` is the modern standard — replaces `setup.py`, `setup.cfg`, `tox.ini`, `.flake8`, etc. One file for everything.

---

## Linters — Code Quality

### Ruff (Recommended — Fast!)
```bash
pip install ruff

# Check for issues
ruff check .

# Auto-fix
ruff check --fix .

# Format code (like black)
ruff format .
```

Ruff replaces flake8, isort, pyflakes, and more. Written in Rust, extremely fast.

### Flake8 (Legacy, still widely used)
```bash
pip install flake8
flake8 src/ tests/
```

### PHP comparison:
| PHP | Python |
|-----|--------|
| PHP_CodeSniffer | flake8 / ruff |
| PHPCS Fixer | black / ruff format |
| PHPStan / Psalm | mypy / pyright |

---

## Formatters — Consistent Style

### Black (The Standard)
```bash
pip install black

# Format a file
black src/main.py

# Format entire project
black src/ tests/

# Check only (CI)
black --check src/ tests/
```

Black is **opinionated** — few configuration options. "Any color you want, as long as it's black."

### Ruff Format (Alternative)
```bash
ruff format src/ tests/
```

Ruff format is Black-compatible but faster.

---

## Type Checkers — Static Analysis

### Mypy
```bash
pip install mypy

# Check types
mypy src/

# Strict mode
mypy src/ --strict
```

```python
# mypy catches this:
def greet(name: str) -> str:
    return 42  # ❌ error: Incompatible return value type (got "int", expected "str")
```

### Pyright (VS Code built-in)
VS Code's Pylance extension uses Pyright. It type-checks as you type — no command needed.

---

## Docker Integration

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Run
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose
```yaml
# docker-compose.yml
services:
  nexus-ai:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      kafka:
        condition: service_healthy
      redis:
        condition: service_healthy

  kafka:
    image: apache/kafka:latest
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      # KRaft mode — no ZooKeeper!
    healthcheck:
      test: ["CMD", "/opt/kafka/bin/kafka-topics.sh", "--bootstrap-server", "localhost:9092", "--list"]

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
```

### Key Docker Concepts:
- **Layer caching:** `COPY requirements.txt` before `COPY src/` — dependencies are cached unless requirements change
- **`depends_on` + healthcheck:** Ensure services are ready before app starts
- **`env_file`:** Load `.env` into the container
- **KRaft mode:** Kafka without ZooKeeper (simpler setup)

---

## CI/CD Integration

### GitHub Actions (Example)
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements-dev.txt
      - run: python -m pytest tests/ -v
      - run: ruff check src/
      - run: mypy src/
```

---

## Useful CLI Tools

```bash
# Package management
pip list                    # Installed packages
pip show fastapi            # Package info
pip freeze                  # All packages with versions (for requirements.txt)
pip install --upgrade pkg   # Update a package

# Virtual environment
python -m venv .venv        # Create
source .venv/bin/activate   # Activate
deactivate                  # Deactivate
which python                # Verify active Python

# Running
python -m pytest            # Run tests
python -m uvicorn src.main:app  # Run app
python -c "import sys; print(sys.version)"  # Quick Python command

# Debugging
python -i script.py         # Run then drop into REPL
python -m pdb script.py     # Debugger
```

---

## Project Structure Convention

```
conn2flow-nexus/
├── .env                    # Environment variables (not in git!)
├── .env.example            # Template for .env
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml          # Project config + tool settings
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Dev dependencies
├── README.md
├── src/                    # Source code
│   ├── __init__.py
│   ├── main.py             # App entry point
│   ├── config/
│   │   └── settings.py
│   ├── api/
│   │   ├── router.py
│   │   ├── endpoints/
│   │   └── schemas/
│   ├── core/
│   │   ├── kafka_producer.py
│   │   ├── kafka_consumer.py
│   │   ├── redis_client.py
│   │   └── llm_router.py
│   ├── models/
│   │   └── events.py
│   └── workers/
│       ├── task_processor.py
│       └── delivery_worker.py
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_graph.py
│   └── ...
└── docs/
    ├── en/
    └── pt-br/
```

### Convention vs PHP:
| PHP | Python |
|-----|--------|
| `App\Http\Controllers\` | `src/api/endpoints/` |
| `App\Models\` | `src/models/` |
| `App\Services\` | `src/core/` |
| `config/` | `src/config/` |
| `tests/Feature/` | `tests/` |
| `routes/api.php` | `src/api/router.py` |

---

## Essential VS Code Extensions

- **Pylance** — IntelliSense, type checking, auto-imports
- **Python** — Debugging, testing, venv management
- **Ruff** — Linting and formatting
- **Even Better TOML** — `pyproject.toml` support
- **Docker** — Dockerfile and compose support

---

## Previous: [← Design Patterns](13-design-patterns.md) | Back to: [Course Index](README.md)
