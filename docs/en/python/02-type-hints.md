# 02. Type Hints & The Type System

## Why Type Hints?

PHP got typed properties in 7.4 and union types in 8.0. Python's type hints (PEP 484+) are similar in spirit but fundamentally different: they're **optional annotations** that don't affect runtime. Python remains dynamically typed — hints are used by tools (mypy, Pyright, IDEs) for static analysis.

```python
# Without hints (valid Python)
def greet(name):
    return f"Hello, {name}"

# With hints (also valid Python — same runtime behavior)
def greet(name: str) -> str:
    return f"Hello, {name}"
```

**Key insight:** Type hints in Python are like PHPDoc on steroids — they're part of the language syntax but don't enforce types at runtime (unless you use Pydantic/dataclasses).

---

## Basic Type Annotations

### PHP
```php
function calculateTotal(float $price, int $quantity): float {
    return $price * $quantity;
}
```

### Python
```python
def calculate_total(price: float, quantity: int) -> float:
    return price * quantity
```

### Variable annotations
```python
name: str = "Conn2Flow"
version: int = 1
price: float = 9.99
is_active: bool = True
items: list = []
```

---

## Built-in Types

| Python Type | PHP Equivalent | Example |
|-------------|---------------|---------|
| `str` | `string` | `name: str = "hello"` |
| `int` | `int` | `count: int = 42` |
| `float` | `float` | `price: float = 9.99` |
| `bool` | `bool` | `active: bool = True` |
| `None` | `null` (as type) | `result: None = None` |
| `bytes` | (no direct equiv) | `data: bytes = b"hello"` |
| `list` | `array` | `items: list = [1, 2, 3]` |
| `dict` | `array` (assoc) | `data: dict = {"a": 1}` |
| `tuple` | (no direct equiv) | `point: tuple = (1, 2)` |
| `set` | (no direct equiv) | `tags: set = {"a", "b"}` |

---

## Generic Types (Parameterized)

### Modern Syntax (Python 3.9+)
```python
# List of strings
names: list[str] = ["Alice", "Bob"]

# Dict with string keys and int values
scores: dict[str, int] = {"Alice": 95, "Bob": 87}

# List of dicts (like our message format)
messages: list[dict[str, str]] = [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi!"},
]

# Set of integers
ids: set[int] = {1, 2, 3}

# Tuple with fixed types
point: tuple[float, float] = (1.5, 2.3)

# Tuple with variable length
values: tuple[int, ...] = (1, 2, 3, 4)  # Any number of ints
```

### From our codebase (`src/core/llm_router.py`):
```python
FALLBACK_MAP: dict[str, list[str]] = {
    "gpt-4o": ["gpt-4o-mini", "claude-3-5-sonnet-20241022"],
    "gpt-4o-mini": ["gpt-4o", "claude-3-5-haiku-20241022"],
}
```
This is `dict[str, list[str]]` — a dictionary where keys are strings and values are lists of strings.

### Legacy Syntax (Python 3.5-3.8)
```python
from typing import List, Dict, Set, Tuple

names: List[str] = ["Alice", "Bob"]
scores: Dict[str, int] = {"Alice": 95}
```
You'll still see this in older code. The `typing` module versions are now deprecated in favor of the built-in lowercase versions (`list`, `dict`, etc.).

---

## Optional & Union Types

### PHP 8.0+
```php
function find(int $id): ?User {  // ?User means User|null
    // ...
}

function process(string|int $value): string|false {
    // ...
}
```

### Python — Modern Union Syntax (3.10+)
```python
# Python 3.10+ (pipe syntax)
def find(id: int) -> User | None:
    ...

def process(value: str | int) -> str | bool:
    ...
```

### Python — Compatible Syntax (3.9+)
```python
from typing import Optional, Union

# Optional[X] is shorthand for X | None
def find(id: int) -> Optional[User]:  # Same as User | None
    ...

def process(value: Union[str, int]) -> Union[str, bool]:
    ...
```

### From our codebase — `str | None` everywhere:

```python
# src/api/endpoints/tasks.py
async def verify_api_key(
    x_c2f_api_key: str | None = Header(None),  # Can be string or None
    settings: Settings = Depends(get_settings),
) -> Settings:
```

```python
# src/api/schemas/requests.py
max_tokens: int | None = Field(
    default=None,
    gt=0,
    le=128000,
    description="Maximum number of tokens in the response",
)
webhook_url: str | None = Field(
    default=None,
    description="Callback URL to deliver the result",
)
```

```python
# src/core/kafka_producer.py
_producer: AIOKafkaProducer | None = None

async def send_event(topic: str, value: Any, key: str | None = None) -> None:
```

**Pattern:** `X | None` means "this can be X or None" — equivalent to PHP's `?X` nullable type.

---

## The `Any` Type

```python
from typing import Any

def process(data: Any) -> Any:
    # data can be literally anything
    # No type checking is performed
    ...
```

`Any` is the **escape hatch** — it disables type checking for that value. Use sparingly.

From our codebase (`src/api/schemas/responses.py`):
```python
from typing import Any

class TaskStatusResponse(BaseModel):
    result: dict[str, Any] | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)
```
Here `dict[str, Any]` means "dict with string keys and values of any type".

---

## `TypedDict` — Typed Dictionaries

When you need a dict with specific keys and value types:

```python
from typing import TypedDict

class TaskGraphState(TypedDict):
    """Shared state between graph nodes."""
    task_id: str
    model: str
    messages: list[dict[str, str]]
    temperature: float
    max_tokens: int | None
    llm_response: dict[str, Any] | None
    error: str | None
    status: str
```

From our codebase (`src/graphs/base_graph.py`), `TypedDict` defines the **shape** of a dictionary. Unlike a regular class, it's still a plain `dict` at runtime — but type checkers know what keys and types to expect.

**PHP equivalent concept:**
```php
// PHP has no direct equivalent. Closest is a class or an interface.
// Or in PHPStan: @phpstan-type TaskState = array{task_id: string, model: string, ...}
```

---

## `__future__` Annotations

```python
from __future__ import annotations
```

This import (must be the **first** line after docstring) makes all annotations **lazy** — they're stored as strings and not evaluated at import time. Benefits:
1. Forward references work (refer to a class before it's defined)
2. Slightly faster import times
3. Allows `"Settings"` as a type before the class is defined

From our codebase (`src/core/kafka_producer.py`):
```python
from __future__ import annotations

# Now we can reference types that aren't defined yet
_producer: AIOKafkaProducer | None = None
```

Without this import in Python 3.9, you'd need:
```python
_producer: "AIOKafkaProducer | None" = None  # String annotation
```

---

## Callable Types

```python
from typing import Callable

# A function that takes (str, int) and returns bool
validator: Callable[[str, int], bool]

# A function that takes no args and returns None
callback: Callable[[], None]

# From our codebase — serializer functions:
key_serializer=lambda k: k.encode("utf-8") if isinstance(k, str) else k
# Type would be: Callable[[Any], bytes]
```

---

## Type Aliases

```python
# Simple alias
UserId = str
Metadata = dict[str, Any]
Messages = list[dict[str, str]]

# Now use them for clarity
def process_task(
    task_id: UserId,
    messages: Messages,
    metadata: Metadata,
) -> None:
    ...

# Python 3.12+ has explicit TypeAlias
from typing import TypeAlias
Messages: TypeAlias = list[dict[str, str]]
```

---

## `@property` Type Hints

```python
class Settings(BaseSettings):
    app_env: str = "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"
```

The return type hint on `@property` tells tools and IDEs that `settings.is_production` is a `bool`.

---

## Type Hints in Practice — Codebase Patterns

### Pattern 1: Return type with exceptions
```python
# Function either returns a value or raises an exception
# The return type only reflects the happy path
async def get_task_status(task_id: str) -> dict[str, Any] | None:
    """Returns None if task not found (don't raise, let caller decide)."""
    r = get_redis()
    raw = await r.get(f"{PREFIX_TASK}{task_id}")
    if raw is None:
        return None
    return orjson.loads(raw)
```

### Pattern 2: Global singleton with None
```python
# Module-level singleton, starts as None
_redis: aioredis.Redis | None = None

def get_redis() -> aioredis.Redis:
    """Returns the active Redis instance."""
    if _redis is None:
        raise RuntimeError("Redis not initialized.")
    return _redis  # Type narrowed: guaranteed not None
```

### Pattern 3: `**kwargs` type hint
```python
async def call_llm(
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int | None = None,
    **kwargs: Any,  # Catch-all for extra keyword arguments
) -> dict[str, Any]:
```

---

## When Python DOES Enforce Types

Type hints alone don't enforce anything. But these tools do:

| Tool | Enforcement |
|------|------------|
| **Pydantic** | Runtime validation on model creation |
| **dataclasses** | Type hints define fields (no validation) |
| **FastAPI** | Uses Pydantic for request/response validation |
| **mypy** | Static analysis (pre-commit, CI) |
| **Pyright** | Static analysis (built into VS Code/Pylance) |

From our codebase — Pydantic enforces types:
```python
class TaskRequest(BaseModel):
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    messages: list[dict[str, str]] = Field(..., min_length=1)

# This raises ValidationError at runtime:
TaskRequest(messages=[], temperature=3.0)
# ❌ messages: min_length=1, temperature: <= 2.0
```

---

## Previous: [← Fundamentals](01-fundamentals.md) | Next: [Data Structures →](03-data-structures.md)
