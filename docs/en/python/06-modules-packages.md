# 06. Modules, Packages & Virtual Environments

## PHP vs Python — File Organization

In PHP, you use `require`, `include`, or autoloading (PSR-4/Composer) to load classes. Python has a **module/package system** based on files and directories.

| Concept | PHP | Python |
|---------|-----|--------|
| Single file | `require 'file.php'` | `import module` |
| Namespace | `namespace App\Models;` | Folder/file structure |
| Autoloader | Composer PSR-4 | Built-in import system |
| Package manager | Composer | pip |
| Lock file | `composer.lock` | `requirements.txt` (or `poetry.lock`) |
| Package registry | Packagist | PyPI (Python Package Index) |

---

## Modules — A File Is a Module

Every `.py` file is a module. The filename (minus `.py`) is the module name.

```
src/
├── main.py           → module: src.main
├── config/
│   ├── __init__.py   → module: src.config
│   └── settings.py   → module: src.config.settings
├── core/
│   ├── __init__.py   → module: src.core
│   ├── redis_client.py  → module: src.core.redis_client
│   └── kafka_producer.py → module: src.core.kafka_producer
```

---

## `__init__.py` — The Package Marker

A directory with `__init__.py` is a **package** (directory module). Without it, Python won't recognize the directory as a package.

```python
# src/core/__init__.py (can be empty)
# Just having this file makes `src.core` a valid package

# Or it can re-export symbols:
from src.core.redis_client import get_redis, start_redis, stop_redis
from src.core.kafka_producer import send_event
```

**PHP comparison:** `__init__.py` is like a `namespace` declaration file combined with Composer's autoload configuration.

---

## Import Syntax

### Absolute Imports (recommended)
```python
# Import the module
import src.config.settings
s = src.config.settings.get_settings()  # Full path

# Import specific names from a module
from src.config.settings import Settings, get_settings
s = get_settings()  # Direct access

# Import with alias
from src.config.settings import Settings as AppSettings
import numpy as np  # Common convention
```

### From our codebase:
```python
# src/main.py
from src.api.router import api_router
from src.config.settings import get_settings
from src.core.kafka_producer import start_producer, stop_producer
from src.core.redis_client import start_redis, stop_redis

# src/core/kafka_producer.py
from __future__ import annotations  # Must be first
import logging
from typing import Any
import orjson
from aiokafka import AIOKafkaProducer
from pydantic import BaseModel
from src.config.settings import get_settings
```

### Import Organization Convention (PEP 8):
```python
# 1. Standard library imports
import logging
import os
import asyncio
from typing import Any

# 2. Third-party library imports
from fastapi import FastAPI
from pydantic import BaseModel
import orjson

# 3. Local/project imports
from src.config.settings import get_settings
from src.core.redis_client import start_redis
```

Each group separated by a blank line. Tools like `isort` enforce this automatically.

### Relative Imports
```python
# Inside src/api/endpoints/tasks.py
from ..schemas.requests import TaskRequest  # Go up 2 levels
from ..schemas.responses import TaskAcceptedResponse
```

**Note:** Our project uses **absolute imports** everywhere (e.g., `from src.config.settings import ...`). This is the recommended practice — clearer and less error-prone than relative imports.

---

## `PYTHONPATH` and Module Resolution

When you write `from src.config.settings import Settings`, Python looks for `src/config/settings.py` in its search path:

1. Current directory
2. `PYTHONPATH` environment variable
3. Standard library paths
4. Site-packages (installed packages)

From our `Dockerfile`:
```dockerfile
ENV PYTHONPATH=/app
```

This tells Python: "look for modules starting from `/app`". So `from src.config.settings import ...` finds `/app/src/config/settings.py`.

From `pyproject.toml` (for tests):
```toml
# Not shown but typically:
[tool.pytest.ini_options]
pythonpath = ["."]
```

---

## Virtual Environments — Isolation

### The Problem (same as PHP without Composer's `vendor/`)
Without isolation, packages install **globally** — project A needs `requests==2.28` but project B needs `requests==2.31`. Conflict!

### The Solution: `venv`
```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/macOS)
source .venv/bin/activate

# Your prompt changes:
(.venv) $ python --version  # Uses venv Python
(.venv) $ pip install fastapi  # Installs in .venv only

# Deactivate
deactivate
```

**PHP comparison:**
- `venv` = Composer's `vendor/` directory
- `pip install` = `composer require`
- `requirements.txt` = `composer.json`
- Activation = Composer's autoloader

### `.venv` in `.gitignore`
```gitignore
# Virtual environment
.venv/
venv/
```

---

## pip — The Package Manager

```bash
# Install a package
pip install fastapi

# Install specific version
pip install fastapi==0.115.0

# Install with version range
pip install "fastapi>=0.115.0,<1.0.0"

# Install from requirements file
pip install -r requirements.txt

# List installed packages
pip list

# Show package info
pip show fastapi

# Freeze current versions (generate lock)
pip freeze > requirements.txt

# Uninstall
pip uninstall fastapi
```

### Our `requirements.txt`:
```
# --- Web Framework ---
fastapi>=0.115.0,<1.0.0
uvicorn[standard]>=0.30.0,<1.0.0

# --- Data Validation & Settings ---
pydantic>=2.10.0,<3.0.0
pydantic-settings>=2.6.0,<3.0.0

# --- Multi-LLM Abstraction ---
litellm>=1.50.0,<2.0.0

# --- Agent Orchestration (LangGraph) ---
langgraph>=1.0.0,<2.0.0
langgraph-checkpoint>=2.0.0,<3.0.0

# --- Kafka (Async) ---
aiokafka>=0.11.0,<1.0.0

# --- Redis (Checkpointing & Cache) ---
redis>=5.0.0,<8.0.0

# --- HTTP Client (Webhook Delivery) ---
httpx>=0.27.0,<1.0.0

# --- Utilities ---
python-dotenv>=1.0.0,<2.0.0
orjson>=3.10.0,<4.0.0

# --- Testing ---
pytest>=8.0.0,<9.0.0
pytest-asyncio>=0.24.0,<1.0.0
```

**Version specifiers:**
| Syntax | Meaning |
|--------|---------|
| `==1.0.0` | Exact version |
| `>=1.0.0` | Minimum version |
| `<2.0.0` | Below version |
| `>=1.0.0,<2.0.0` | Range (common) |
| `~=1.0.0` | Compatible release (>=1.0.0, <1.1.0) |

---

## `pyproject.toml` — Modern Configuration

`pyproject.toml` is the **modern standard** (PEP 518/621) for Python project configuration. It replaces `setup.py`, `setup.cfg`, and individual tool configs.

```toml
# Our pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
```

A full `pyproject.toml` can include:
```toml
[project]
name = "conn2flow-nexus-ai"
version = "0.1.0"
description = "AI Gateway"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "pydantic>=2.10.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"

[tool.mypy]
python_version = "3.11"
strict = true

[tool.ruff]
line-length = 100
```

**PHP comparison:** `pyproject.toml` is like `composer.json` — it defines the project metadata, dependencies, and tool configurations all in one file.

---

## Project Structure — Our Codebase

```
conn2flow-nexus/
├── .env                  # Environment variables (not in git)
├── .env.example          # Template for .env
├── .gitignore
├── .venv/                # Virtual environment (not in git)
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml        # Project config
├── requirements.txt      # Dependencies
├── README.md
├── docs/                 # Documentation
├── sdd/                  # SDD specifications
├── src/                  # Application source code
│   ├── __init__.py
│   ├── main.py           # Entry point
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── endpoints/
│   │   │   ├── __init__.py
│   │   │   ├── health.py
│   │   │   └── tasks.py
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── requests.py
│   │       └── responses.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── kafka_consumer.py
│   │   ├── kafka_producer.py
│   │   ├── llm_router.py
│   │   └── redis_client.py
│   ├── graphs/
│   │   ├── __init__.py
│   │   └── base_graph.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── events.py
│   └── workers/
│       ├── __init__.py
│       ├── delivery_worker.py
│       └── task_processor.py
└── tests/
    ├── conftest.py       # Shared fixtures
    ├── test_api.py
    ├── test_graph.py
    ├── test_llm_router.py
    ├── test_schemas.py
    └── test_settings.py
```

### Why this structure?
- **`src/` as top-level package** — all code under one namespace
- **Subpackages by domain** — `api/`, `core/`, `graphs/`, `models/`, `workers/`
- **`tests/` separate** — not part of the `src/` package
- **`conftest.py`** — pytest automatically discovers fixtures here

**PHP comparison:**
```
gestor/                          conn2flow-nexus/
├── controladores/    →          ├── src/api/endpoints/
├── modulos/          →          ├── src/graphs/ + src/workers/
├── bibliotecas/      →          ├── src/core/
├── config.php        →          ├── src/config/settings.py
├── vendor/           →          ├── .venv/
└── composer.json     →          └── requirements.txt
```

---

## `if __name__ == "__main__"` — Script Guard

```python
# src/workers/task_processor.py
async def main() -> None:
    """Worker entry point."""
    settings = get_settings()
    ...

if __name__ == "__main__":
    asyncio.run(main())
```

### What does this mean?

When Python runs a file directly (`python task_processor.py`), it sets `__name__` to `"__main__"`. When the file is imported by another module, `__name__` is the module name (e.g., `"src.workers.task_processor"`).

```python
# Run directly: python script.py
# __name__ == "__main__" → True → runs main()

# Imported: from src.workers.task_processor import TaskProcessorWorker
# __name__ == "src.workers.task_processor" → False → skips main()
```

**PHP comparison:** No direct equivalent. In PHP, every included file executes everything. In Python, you can make a file both importable AND directly executable.

---

## Previous: [← OOP](05-oop.md) | Next: [Async/Await →](07-async-await.md)
