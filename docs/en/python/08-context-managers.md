# 08. Context Managers & Resource Handling

## What Are Context Managers?

Context managers ensure resources are properly **acquired and released**, even if errors occur. PHP doesn't have a direct equivalent — you use `try/finally` everywhere.

### PHP Pattern
```php
$file = fopen('data.txt', 'r');
try {
    $content = fread($file, filesize('data.txt'));
} finally {
    fclose($file);
}

// Or PDO with transactions:
$pdo->beginTransaction();
try {
    $pdo->exec("INSERT INTO ...");
    $pdo->commit();
} catch (Exception $e) {
    $pdo->rollback();
    throw $e;
}
```

### Python — `with` Statement
```python
# File automatically closed, even if exception occurs
with open("data.txt", "r") as f:
    content = f.read()
# f is closed here, guaranteed

# Multiple resources
with open("input.txt") as fin, open("output.txt", "w") as fout:
    fout.write(fin.read())
```

---

## How Context Managers Work — The Protocol

A context manager implements two dunder methods:

```python
class ManagedResource:
    def __enter__(self):
        """Called when entering the `with` block. Returns the resource."""
        print("Acquiring resource")
        return self  # This becomes the `as` variable

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Called when exiting the `with` block (always, even on error)."""
        print("Releasing resource")
        # Return True to suppress the exception, False/None to propagate
        return False

with ManagedResource() as resource:
    print("Using resource")
    # If exception here → __exit__ still called
```

Output:
```
Acquiring resource
Using resource
Releasing resource
```

### `__exit__` Parameters:
| Parameter | Value (no error) | Value (with error) |
|-----------|-------------------|---------------------|
| `exc_type` | `None` | Exception class (e.g., `ValueError`) |
| `exc_val` | `None` | Exception instance |
| `exc_tb` | `None` | Traceback object |

---

## `@contextmanager` — Simpler Syntax

Instead of writing a class with `__enter__` and `__exit__`, use a generator:

```python
from contextlib import contextmanager

@contextmanager
def timer(label: str):
    """Measures execution time of a block."""
    import time
    start = time.perf_counter()
    yield  # Everything before yield = __enter__, after = __exit__
    elapsed = time.perf_counter() - start
    print(f"{label}: {elapsed:.3f}s")

with timer("Database query"):
    # ... your code here ...
    pass
# Prints: "Database query: 0.123s"
```

### With error handling:
```python
@contextmanager
def transaction(connection):
    """Database transaction context manager."""
    connection.begin()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise  # Re-raise the exception
```

---

## `@asynccontextmanager` — Async Version

### From our codebase (`src/main.py`):
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application startup and shutdown lifecycle."""
    settings = get_settings()
    app.state.settings = settings

    # --- Startup (before yield) ---
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    logger.info("Starting Conn2Flow Nexus AI v%s", settings.app_version)
    await start_redis()      # Async setup
    await start_producer()   # Async setup
    logger.info("All services initialized")

    yield  # Application is running and handling requests

    # --- Shutdown (after yield) ---
    logger.info("Shutting down...")
    await stop_producer()    # Async cleanup
    await stop_redis()       # Async cleanup
    logger.info("Shutdown complete")
```

**How it works:**
1. FastAPI calls the lifespan context manager at startup
2. Everything **before** `yield` runs during startup
3. The `yield` suspends — the app handles requests
4. Everything **after** `yield` runs during shutdown
5. Even if the app crashes, the cleanup code runs

This replaces the older `@app.on_event("startup")` / `@app.on_event("shutdown")` pattern.

---

## `with` in Our Codebase

### TestClient (tests/test_api.py)
```python
@pytest.fixture
def client():
    with (
        patch("src.main.start_redis", new_callable=AsyncMock),
        patch("src.main.stop_redis", new_callable=AsyncMock),
        patch("src.main.start_producer", new_callable=AsyncMock),
        patch("src.main.stop_producer", new_callable=AsyncMock),
    ):
        from src.main import app
        with TestClient(app) as c:
            yield c
```

**Multiple context managers** with Python 3.10+ parenthesized syntax. Each `patch()` is a context manager that:
1. Replaces the function with a mock (`__enter__`)
2. Restores the original function when done (`__exit__`)

### httpx AsyncClient (src/workers/delivery_worker.py)
```python
async with httpx.AsyncClient(timeout=30) as client:
    for attempt in range(1, MAX_RETRIES + 1):
        response = await client.post(webhook_url, content=body_bytes, headers=headers)
```

`async with httpx.AsyncClient() as client`:
1. `__aenter__`: Creates the HTTP client and connection pool
2. `__aexit__`: Closes all connections and cleans up

### pytest.raises (tests/test_schemas.py)
```python
with pytest.raises(ValidationError):
    TaskRequest(messages=[])
```

`pytest.raises()` is a context manager that:
1. `__enter__`: Captures exceptions
2. `__exit__`: Asserts the expected exception was raised. If not → test fails

---

## `async with` — The Async Protocol

```python
class AsyncResource:
    async def __aenter__(self):
        """Async setup."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async cleanup."""
        await self.disconnect()
        return False

async def main():
    async with AsyncResource() as resource:
        await resource.do_work()
```

Used by: `httpx.AsyncClient`, `aioredis`, `AIOKafkaProducer`, `AIOKafkaConsumer`

---

## Common Context Manager Patterns

### Temporary Change
```python
@contextmanager
def temporary_env(key: str, value: str):
    """Temporarily set an environment variable."""
    old = os.environ.get(key)
    os.environ[key] = value
    try:
        yield
    finally:
        if old is None:
            del os.environ[key]
        else:
            os.environ[key] = old

with temporary_env("DEBUG", "true"):
    # DEBUG is "true" here
    pass
# DEBUG is restored to original value
```

### Suppress Exceptions
```python
from contextlib import suppress

# Instead of try/except/pass:
with suppress(FileNotFoundError):
    os.remove("temp.txt")
# If file doesn't exist, exception is silently suppressed
```

### Redirect Output
```python
from contextlib import redirect_stdout
import io

f = io.StringIO()
with redirect_stdout(f):
    print("captured output")

output = f.getvalue()  # "captured output\n"
```

---

## Why Context Managers Matter

They eliminate an entire class of bugs: **resource leaks**.

Without context managers:
```python
# ❌ If process_data() raises, file is never closed!
f = open("data.txt")
data = f.read()
process_data(data)  # Exception here!
f.close()  # Never reached
```

With context managers:
```python
# ✅ File is ALWAYS closed, even on exception
with open("data.txt") as f:
    data = f.read()
    process_data(data)  # Exception here? File still closed!
```

---

## Previous: [← Async/Await](07-async-await.md) | Next: [Error Handling →](09-error-handling.md)
