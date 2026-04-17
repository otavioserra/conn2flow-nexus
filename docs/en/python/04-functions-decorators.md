# 04. Functions, Closures & Decorators

## Functions in Python

### Basic Syntax

```python
# PHP
# function greet(string $name): string {
#     return "Hello, {$name}!";
# }

# Python
def greet(name: str) -> str:
    return f"Hello, {name}!"
```

Key differences:
- `def` keyword instead of `function`
- No braces `{}` — indentation defines the body
- Colon `:` after the signature
- Type hints are optional (but recommended)

### Default Arguments

```python
# PHP: function connect($host = 'localhost', $port = 3306) { ... }

def connect(host: str = "localhost", port: int = 3306) -> None:
    print(f"Connecting to {host}:{port}")

connect()                    # localhost:3306
connect("db.example.com")   # db.example.com:3306
connect(port=5432)          # localhost:5432 (keyword argument)
```

### From our codebase (`src/core/llm_router.py`):
```python
async def call_llm(
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.7,        # Default
    max_tokens: int | None = None,    # Default None
    **kwargs: Any,                    # Catch-all keywords
) -> dict[str, Any]:
```

---

## Positional vs Keyword Arguments

```python
def create_user(name: str, email: str, age: int = 0) -> dict:
    return {"name": name, "email": email, "age": age}

# Positional
create_user("Alice", "alice@test.com", 30)

# Keyword (order doesn't matter)
create_user(email="alice@test.com", name="Alice", age=30)

# Mixed (positional must come first)
create_user("Alice", age=30, email="alice@test.com")
```

### Enforcing Argument Types with `/` and `*`

```python
# Arguments before / are positional-only
# Arguments after * are keyword-only
def process(data: bytes, /, *, encoding: str = "utf-8") -> str:
    return data.decode(encoding)

process(b"hello")                     # ✅ positional
process(b"hello", encoding="latin-1") # ✅ keyword
process(data=b"hello")                # ❌ TypeError! (positional-only)
process(b"hello", "latin-1")          # ❌ TypeError! (keyword-only)
```

---

## `*args` and `**kwargs`

### `*args` — Variable Positional Arguments
```python
def add(*numbers: int) -> int:
    """Accept any number of positional arguments."""
    return sum(numbers)

add(1, 2, 3)      # 6
add(1, 2, 3, 4, 5) # 15

# numbers is a tuple: (1, 2, 3)
```

PHP equivalent: `function add(int ...$numbers): int { return array_sum($numbers); }`

### `**kwargs` — Variable Keyword Arguments
```python
def configure(**options: Any) -> dict:
    """Accept any number of keyword arguments."""
    return options

configure(host="localhost", port=8000, debug=True)
# {"host": "localhost", "port": 8000, "debug": True}
```

### Combined
```python
def flexible(required: str, *args: Any, **kwargs: Any) -> None:
    print(f"required: {required}")
    print(f"args: {args}")       # Tuple of extra positional args
    print(f"kwargs: {kwargs}")   # Dict of extra keyword args

flexible("hello", 1, 2, 3, debug=True, verbose=False)
# required: hello
# args: (1, 2, 3)
# kwargs: {"debug": True, "verbose": False}
```

### From our codebase — `**kwargs` passthrough:
```python
# src/core/llm_router.py
async def call_llm(
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int | None = None,
    **kwargs: Any,  # Extra args passed to LiteLLM
) -> dict[str, Any]:
    response = await litellm.acompletion(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs,  # Unpacked and forwarded
    )
```

Pattern: Accept `**kwargs` and forward with `**kwargs` — transparent passthrough. In PHP, you'd use `...$args` but it's less elegant for named parameters.

---

## Lambda Functions

```python
# PHP: $double = fn($x) => $x * 2;  (arrow functions, PHP 7.4+)

# Python lambda
double = lambda x: x * 2
double(5)  # 10

# Multi-argument
add = lambda x, y: x + y
add(3, 4)  # 7

# Common use: sorting key
users = [{"name": "Charlie"}, {"name": "Alice"}, {"name": "Bob"}]
users.sort(key=lambda u: u["name"])
# [{"name": "Alice"}, {"name": "Bob"}, {"name": "Charlie"}]
```

### From our codebase:
```python
# src/core/kafka_producer.py
key_serializer=lambda k: k.encode("utf-8") if isinstance(k, str) else k
```

**Limitation:** Lambdas can only contain a **single expression** — no statements, no assignments, no multi-line logic. For anything complex, use a regular `def`.

---

## Functions as First-Class Objects

In Python, functions are objects — they can be assigned to variables, passed as arguments, and returned from other functions.

```python
def square(x):
    return x ** 2

def cube(x):
    return x ** 3

# Function as variable
operation = square
operation(4)  # 16

# Function as argument
def apply(func, value):
    return func(value)

apply(square, 4)  # 16
apply(cube, 3)    # 27

# Function in a dict (strategy pattern)
operations = {
    "square": square,
    "cube": cube,
}
operations["square"](4)  # 16
```

---

## Closures

A closure is a function that remembers the variables from its enclosing scope:

```python
def make_multiplier(factor: int):
    def multiply(x: int) -> int:
        return x * factor  # 'factor' is captured from outer scope
    return multiply

double = make_multiplier(2)
triple = make_multiplier(3)

double(5)   # 10
triple(5)   # 15
```

PHP equivalent:
```php
function make_multiplier(int $factor): Closure {
    return fn(int $x): int => $x * $factor;
    // or: return function(int $x) use ($factor): int { return $x * $factor; };
}
```

**Note:** PHP requires `use ($var)` to capture variables (or arrow functions capture automatically). Python captures automatically from the enclosing scope.

---

## Decorators — The Python Superpower

Decorators are **the most important Python feature** you'll use daily. They wrap functions to add behavior — like PHP middleware or annotations.

### Basic Decorator
```python
def log_call(func):
    """Decorator that logs function calls."""
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"{func.__name__} returned {result}")
        return result
    return wrapper

@log_call
def add(a, b):
    return a + b

add(3, 4)
# Output:
# Calling add
# add returned 7
```

**`@log_call` is syntactic sugar for:** `add = log_call(add)`

### Decorator with Arguments
```python
def retry(max_attempts: int = 3):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        raise
                    print(f"Attempt {attempt} failed: {e}")
        return wrapper
    return decorator

@retry(max_attempts=5)
def unreliable_operation():
    ...
```

### `functools.wraps` — Preserving Function Metadata
```python
from functools import wraps

def log_call(func):
    @wraps(func)  # Preserves __name__, __doc__, etc.
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper
```

Without `@wraps`, `add.__name__` would return `"wrapper"` instead of `"add"`.

---

## Decorators in Our Codebase

### `@pytest.fixture` — Test Setup
```python
# tests/conftest.py
@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    ...
```

### `@router.get()` / `@router.post()` — Route Registration
```python
# src/api/endpoints/health.py
@router.get("/health")
async def health_check():
    ...

# src/api/endpoints/tasks.py
@router.post(
    "/submit",
    response_model=TaskAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submits an AI task for asynchronous processing",
)
async def submit_task(payload: TaskRequest, settings: Settings = Depends(verify_api_key)):
    ...
```

### `@property` — Computed Attribute
```python
# src/config/settings.py
@property
def is_production(self) -> bool:
    return self.app_env == "production"

# Usage: settings.is_production (no parentheses!)
```

### `@model_validator` — Pydantic Validation Hook
```python
# src/config/settings.py
@model_validator(mode="after")
def _warn_missing_keys(self) -> "Settings":
    has_any = any([self.openai_api_key, self.anthropic_api_key, ...])
    if not has_any and self.is_production:
        raise ValueError("At least one LLM API key must be set")
    return self
```

### `@abstractmethod` — Abstract Interface
```python
# src/core/kafka_consumer.py
from abc import ABC, abstractmethod

class BaseKafkaConsumer(ABC):
    @abstractmethod
    async def process_message(self, payload: dict[str, Any]) -> None:
        ...
```

### `@lru_cache` — Memoization/Singleton
```python
# src/config/settings.py
from functools import lru_cache

@lru_cache
def get_settings() -> Settings:
    return Settings()

# First call: creates Settings()
# Second call: returns cached instance (singleton!)
```

### `@patch` — Test Mocking
```python
# tests/test_api.py
@patch("src.api.endpoints.tasks.set_task_status", new_callable=AsyncMock)
@patch("src.api.endpoints.tasks.send_event", new_callable=AsyncMock)
def test_submit_returns_202(self, mock_send, mock_status, client):
    ...
```

### `@pytest.mark.asyncio` — Async Test Marker
```python
@pytest.mark.asyncio
@patch("src.graphs.base_graph.call_llm", new_callable=AsyncMock)
async def test_successful_graph_execution(self, mock_llm):
    ...
```

---

## Stacking Decorators

Decorators are applied **bottom to top**:

```python
@decorator_a
@decorator_b
@decorator_c
def my_function():
    pass

# Equivalent to:
my_function = decorator_a(decorator_b(decorator_c(my_function)))
```

From our tests:
```python
@pytest.mark.asyncio           # Applied 2nd (outermost)
@patch("src.graphs.base_graph.call_llm", new_callable=AsyncMock)  # Applied 1st (innermost)
async def test_successful_graph_execution(self, mock_llm):
    ...
```

The `@patch` decorator wraps the function first, injecting `mock_llm`. Then `@pytest.mark.asyncio` marks it as an async test.

---

## `functools` Module — Essential Function Tools

```python
from functools import lru_cache, partial, wraps, reduce

# lru_cache — Memoize function results
@lru_cache(maxsize=128)
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

fibonacci(100)  # Instant! Without cache: would take forever

# partial — Pre-fill some arguments
def power(base, exponent):
    return base ** exponent

square = partial(power, exponent=2)
cube = partial(power, exponent=3)
square(5)  # 25
cube(3)    # 27

# reduce — Fold a sequence
from functools import reduce
reduce(lambda acc, x: acc + x, [1, 2, 3, 4, 5])  # 15
# PHP: array_reduce($arr, fn($carry, $item) => $carry + $item, 0)
```

---

## Docstrings — Function Documentation

```python
def calculate_total(
    price: float,
    quantity: int,
    discount: float = 0.0,
) -> float:
    """Calculates the total price with optional discount.

    Args:
        price: Unit price of the item.
        quantity: Number of items.
        discount: Percentage discount (0.0 to 1.0).

    Returns:
        The total price after discount.

    Raises:
        ValueError: If discount is not between 0 and 1.

    Examples:
        >>> calculate_total(10.0, 3)
        30.0
        >>> calculate_total(10.0, 3, 0.1)
        27.0
    """
    if not 0 <= discount <= 1:
        raise ValueError("Discount must be between 0 and 1")
    return price * quantity * (1 - discount)
```

From our codebase — docstrings are used everywhere:
```python
async def send_event(topic: str, value: Any, key: str | None = None) -> None:
    """Publishes an event to the specified Kafka topic.

    Args:
        topic: Kafka topic name.
        value: Payload (Pydantic model, dict or bytes).
        key: Optional key for partitioning.
    """
```

---

## Previous: [← Data Structures](03-data-structures.md) | Next: [OOP in Python →](05-oop.md)
