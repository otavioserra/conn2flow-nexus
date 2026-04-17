# 09. Error Handling & Exceptions

## PHP vs Python Exception Handling

The concepts are almost identical — both use try/catch(except)/finally. The syntax differs slightly.

### PHP
```php
try {
    $result = riskyOperation();
} catch (InvalidArgumentException $e) {
    echo "Bad input: " . $e->getMessage();
} catch (RuntimeException | LogicException $e) {
    echo "Error: " . $e->getMessage();
} catch (Exception $e) {
    echo "Generic: " . $e->getMessage();
} finally {
    cleanup();
}
```

### Python
```python
try:
    result = risky_operation()
except ValueError as e:
    print(f"Bad input: {e}")
except (RuntimeError, TypeError) as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"Generic: {e}")
finally:
    cleanup()
```

### Key Differences:

| Feature | PHP | Python |
|---------|-----|--------|
| Keyword | `catch` | `except` |
| Multiple types | `catch (A \| B $e)` | `except (A, B) as e:` |
| Get message | `$e->getMessage()` | `str(e)` or `e.args[0]` |
| Get type | `get_class($e)` | `type(e).__name__` |
| Re-throw | `throw $e;` or `throw;` | `raise` or `raise e` |
| Base exception | `Exception` | `Exception` |
| Base of everything | `Throwable` | `BaseException` |

---

## Exception Hierarchy

```
BaseException              ← Never catch this (includes SystemExit, KeyboardInterrupt)
├── SystemExit             ← sys.exit()
├── KeyboardInterrupt      ← Ctrl+C
├── GeneratorExit          ← Generator cleanup
└── Exception              ← Catch this as the broadest level
    ├── ValueError         ← Invalid value (wrong type/range)
    ├── TypeError          ← Wrong type
    ├── KeyError           ← Dict key not found
    ├── IndexError         ← List index out of range
    ├── AttributeError     ← Object has no attribute
    ├── FileNotFoundError  ← File not found
    ├── RuntimeError       ← Generic runtime error
    ├── ConnectionError    ← Network connection failed
    ├── TimeoutError       ← Operation timed out
    ├── ImportError         ← Module not found
    │   └── ModuleNotFoundError
    ├── OSError            ← OS-level error
    │   ├── FileNotFoundError
    │   ├── PermissionError
    │   └── FileExistsError
    └── StopIteration      ← Iterator exhausted
```

**Rule:** Always catch the most **specific** exception first, then broader ones.

---

## From Our Codebase — Exception Patterns

### Pattern 1: Catch and wrap (`src/graphs/base_graph.py`)
```python
async def invoke_llm(state: TaskGraphState) -> dict[str, Any]:
    if state.get("error"):
        return {}  # Skip if already failed

    try:
        result = await call_llm(
            model=state["model"],
            messages=state["messages"],
            temperature=state.get("temperature", 0.7),
        )
        return {"llm_response": result, "status": "completed"}

    except Exception as exc:
        logger.exception("[graph] LLM failed — task=%s", state["task_id"])
        return {
            "error": f"LLM error: {type(exc).__name__}: {exc}",
            "status": "failed",
        }
```

**`type(exc).__name__`** → Gets the exception class name (e.g., `"RuntimeError"`)
**`logger.exception()`** → Logs the message + full traceback (more info than `logger.error()`)

### Pattern 2: Specific exception handling (`src/core/llm_router.py`)
```python
try:
    response = await litellm.acompletion(model=model, messages=messages, ...)
    return result

except litellm.AuthenticationError:
    logger.error("LLM authentication failed for model=%s", model)
    raise  # Re-raise as-is

except litellm.RateLimitError:
    logger.warning("LLM rate limited for model=%s", model)
    raise  # Re-raise as-is

except Exception:
    logger.exception("LLM call failed — model=%s", model)
    raise  # Re-raise as-is
```

**Pattern:** Catch specific exceptions for specific logging, then `raise` to propagate. The caller (`invoke_llm`) catches the broad `Exception`.

### Pattern 3: Guard clause with `raise` (`src/core/kafka_producer.py`)
```python
async def send_event(topic: str, value: Any, key: str | None = None) -> None:
    if _producer is None:
        raise RuntimeError("Kafka producer not initialized. Call start_producer() first.")
    metadata = await _producer.send_and_wait(topic, value=value, key=key)
```

### Pattern 4: Worker error resilience (`src/core/kafka_consumer.py`)
```python
async def run(self) -> None:
    await self.start()
    try:
        async for msg in self._consumer:
            try:
                await self.process_message(msg.value)
            except Exception:
                logger.exception("Error processing message at offset=%d", msg.offset)
                await self.handle_error(msg.value)
    except asyncio.CancelledError:
        logger.info("Consumer cancelled")
    finally:
        await self.stop()
```

**Nested try/except:** The inner `try` catches per-message errors (so one bad message doesn't kill the worker). The outer `try` catches consumer-level errors. `finally` ensures cleanup.

### Pattern 5: Retry with exception handling (`src/workers/delivery_worker.py`)
```python
for attempt in range(1, MAX_RETRIES + 1):
    try:
        response = await client.post(webhook_url, content=body_bytes, headers=headers)
        if response.status_code < 300:
            delivered = True
            break
        last_error = f"HTTP {response.status_code}"

    except httpx.TimeoutException:
        last_error = "Timeout"

    except httpx.RequestError as exc:
        last_error = str(exc)

    if attempt < MAX_RETRIES:
        await asyncio.sleep(RETRY_BASE_DELAY ** attempt)
```

---

## `raise` — Throwing Exceptions

```python
# Raise a new exception
raise ValueError("Temperature must be positive")

# Raise with no arguments (re-raise current exception)
except SomeError:
    logger.error("Something went wrong")
    raise  # Preserves the original traceback

# Raise from another exception (exception chaining)
try:
    data = json.loads(raw_input)
except json.JSONDecodeError as e:
    raise ValueError("Invalid payload format") from e
    # The original JSONDecodeError is preserved as __cause__
```

### From our codebase:
```python
# src/config/settings.py
@model_validator(mode="after")
def _warn_missing_keys(self) -> "Settings":
    has_any = any([self.openai_api_key, self.anthropic_api_key, ...])
    if not has_any and self.is_production:
        raise ValueError(
            "At least one LLM API key must be set in production"
        )
    return self
```

---

## Custom Exceptions

```python
# Simple custom exception
class TaskNotFoundError(Exception):
    """Raised when a task ID doesn't exist in Redis."""
    pass

# Custom exception with data
class WebhookDeliveryError(Exception):
    """Raised when webhook delivery fails after all retries."""
    def __init__(self, task_id: str, attempts: int, last_error: str):
        self.task_id = task_id
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(
            f"Failed to deliver task {task_id} after {attempts} attempts: {last_error}"
        )

# Usage:
try:
    deliver_webhook(task_id)
except WebhookDeliveryError as e:
    print(e.task_id)      # Access structured data
    print(e.attempts)
    print(e.last_error)
```

### PHP comparison:
```php
class TaskNotFoundError extends RuntimeException {
    public function __construct(string $taskId) {
        parent::__construct("Task $taskId not found");
    }
}
```

---

## `HTTPException` — FastAPI-Specific

FastAPI uses `HTTPException` to return error HTTP responses:

```python
from fastapi import HTTPException, status

# From src/api/endpoints/tasks.py
async def verify_api_key(x_c2f_api_key: str | None = Header(None), ...):
    if settings.is_production and settings.c2f_api_key:
        if not x_c2f_api_key or x_c2f_api_key != settings.c2f_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key",
            )

# 404 Not Found
async def get_task_status_endpoint(task_id: str, ...):
    data = await get_task_status(task_id)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
```

`HTTPException` is caught by FastAPI's middleware and converted to an HTTP response with the appropriate status code and JSON body.

---

## Testing Exceptions

### `pytest.raises()` — Assert Exception is Raised
```python
# tests/test_schemas.py
def test_empty_messages_fails(self):
    with pytest.raises(ValidationError):
        TaskRequest(messages=[])

def test_temperature_out_of_range(self):
    with pytest.raises(ValidationError):
        TaskRequest(messages=[{"role": "user", "content": "Hi"}], temperature=3.0)

# tests/test_settings.py
def test_production_requires_api_key(self, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(Exception, match="LLM API key"):
        Settings()
```

**`match="LLM API key"`** — Uses regex to match the exception message. Ensures the **right** exception is raised, not just any exception.

### `side_effect` — Mock Raising Exceptions
```python
# tests/test_graph.py
@patch("src.graphs.base_graph.call_llm", new_callable=AsyncMock)
async def test_llm_error_caught(self, mock_llm):
    mock_llm.side_effect = RuntimeError("API exploded")

    result = await run_task_graph(
        task_id="test-4",
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Explode"}],
    )

    assert result["status"] == "failed"
    assert "API exploded" in result["error"]
```

---

## Best Practices

1. **Catch specific exceptions** — never bare `except:` (catches everything including `KeyboardInterrupt`)
2. **Use `raise` without arguments** to re-raise — preserves traceback
3. **Use `raise X from Y`** for exception chaining — preserves cause
4. **Log with `logger.exception()`** — includes traceback automatically
5. **Don't use exceptions for flow control** — exceptions are for exceptional cases
6. **Create custom exceptions** for domain-specific errors
7. **Always clean up** — use `finally` or context managers

---

## Previous: [← Context Managers](08-context-managers.md) | Next: [Pydantic →](10-pydantic.md)
