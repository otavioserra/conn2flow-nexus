# 12. Testing with Pytest

## PHP Testing vs Python Testing

| PHP (PHPUnit) | Python (pytest) |
|---------------|-----------------|
| `class FooTest extends TestCase` | `class TestFoo:` (no base class needed!) |
| `$this->assertEquals(a, b)` | `assert a == b` (plain assert) |
| `$this->expectException(E::class)` | `with pytest.raises(E):` |
| `setUp()` / `tearDown()` | Fixtures (`@pytest.fixture`) |
| `@dataProvider` | `@pytest.mark.parametrize` |
| `$this->createMock()` | `unittest.mock.patch()` / `MagicMock` |
| `phpunit.xml` | `pyproject.toml` ([tool.pytest]) |

---

## Configuration

### `pyproject.toml`
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"      # Auto-detect async tests
testpaths = ["tests"]       # Where to find tests
python_files = ["test_*.py"]  # Test file pattern
python_functions = ["test_*"]  # Test function pattern
```

### Running Tests
```bash
# All tests
python -m pytest tests/ -v

# One file
python -m pytest tests/test_api.py -v

# One test class
python -m pytest tests/test_api.py::TestHealthEndpoint -v

# One test method
python -m pytest tests/test_api.py::TestHealthEndpoint::test_health_returns_200 -v

# With output capture disabled (see print statements)
python -m pytest tests/ -v -s

# With detailed failure info
python -m pytest tests/ -v --tb=long

# Stop on first failure
python -m pytest tests/ -v -x
```

---

## Test Discovery

pytest automatically discovers tests by convention:
- Files named `test_*.py` or `*_test.py`
- Classes named `Test*` (no base class required!)
- Functions/methods named `test_*`

```python
# tests/test_schemas.py
class TestTaskRequest:           # Class groups related tests
    def test_valid_minimal(self):    # Test method
        ...

    def test_empty_messages_fails(self):
        ...

# Or standalone functions (no class needed):
def test_something():
    ...
```

**PHP comparison:** In PHPUnit, tests must extend `TestCase`. In pytest, they're plain classes/functions — much less boilerplate.

---

## Assertions — Plain `assert`

```python
# PHPUnit: $this->assertEquals(200, $response->getStatusCode());
# pytest:
assert response.status_code == 200

# PHPUnit: $this->assertContains('task_id', $data);
assert "task_id" in data

# PHPUnit: $this->assertTrue($result);
assert result is True

# PHPUnit: $this->assertNull($value);
assert value is None

# PHPUnit: $this->assertIsInstance($obj, User::class);
assert isinstance(obj, User)

# PHPUnit: $this->assertCount(3, $items);
assert len(items) == 3
```

**Why plain `assert`?** pytest rewrites assert statements to provide **detailed failure messages**:
```
assert resp.status_code == 200
>       AssertionError: assert 404 == 200
>         where 404 = <Response [404]>.status_code
```

---

## Fixtures — Setup & Teardown

### PHP (PHPUnit)
```php
class UserTest extends TestCase {
    private PDO $db;

    protected function setUp(): void {
        $this->db = new PDO('sqlite::memory:');
    }

    protected function tearDown(): void {
        $this->db = null;
    }
}
```

### Python (pytest)
```python
import pytest

@pytest.fixture
def db():
    """Create a test database connection."""
    connection = create_connection("sqlite:///:memory:")
    yield connection  # yield = setUp done, provide to test
    connection.close()  # After yield = tearDown

def test_query(db):  # db is automatically injected!
    result = db.execute("SELECT 1")
    assert result is not None
```

### `yield` vs `return`:
- `return` — fixture provides a value, no cleanup needed
- `yield` — fixture provides a value AND runs cleanup after the test

### `autouse=True` — Apply to ALL Tests

```python
# tests/conftest.py
@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch):
    """Runs automatically for every test."""
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("C2F_API_KEY", "test-api-key")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
```

**No need to declare as parameter** — `autouse=True` means it runs for every test in scope.

### Fixture Scopes
```python
@pytest.fixture(scope="function")  # Default: run per test
@pytest.fixture(scope="class")     # Run once per class
@pytest.fixture(scope="module")    # Run once per file
@pytest.fixture(scope="session")   # Run once per test session
```

---

## `conftest.py` — Shared Fixtures

`conftest.py` is a special file that pytest auto-discovers. Fixtures defined here are available to all tests in the same directory (and subdirectories).

```
tests/
├── conftest.py        # Shared fixtures (env vars, clients)
├── test_api.py        # Can use fixtures from conftest.py
├── test_graph.py
├── test_schemas.py
└── test_settings.py
```

No need to import — pytest handles it automatically.

---

## `monkeypatch` — Temporary Modifications

```python
def test_production_settings(monkeypatch):
    # Set env var (restored after test)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-prod-key")

    s = Settings()
    assert s.is_production is True

def test_missing_key(monkeypatch):
    # Delete env var (restored after test)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    # Set attribute on object
    monkeypatch.setattr(settings, "app_debug", True)

    # Set dict item
    monkeypatch.setitem(os.environ, "KEY", "value")
```

**PHP comparison:** PHPUnit has `$_ENV` manipulation, but Python's `monkeypatch` is more powerful — it restores EVERYTHING automatically.

---

## Mocking — `unittest.mock`

### `patch()` — Replace a Module-Level Object
```python
from unittest.mock import patch, MagicMock, AsyncMock

# As decorator
@patch("src.api.endpoints.tasks.send_event", new_callable=AsyncMock)
def test_submit(mock_send):
    # send_event is now a mock
    ...
    mock_send.assert_called_once()

# As context manager
with patch("src.core.redis_client.get_redis") as mock_redis:
    mock_r = AsyncMock()
    mock_r.ping = AsyncMock(return_value=True)
    mock_redis.return_value = mock_r
    # Now get_redis() returns mock_r, and mock_r.ping() returns True
```

### Key Rule: Patch WHERE IT'S USED, Not WHERE IT'S DEFINED

```python
# ❌ Wrong: patching where send_event is defined
@patch("src.core.kafka_producer.send_event", ...)

# ✅ Correct: patching where send_event is imported/used
@patch("src.api.endpoints.tasks.send_event", ...)
```

Because `tasks.py` does `from src.core.kafka_producer import send_event`, the name `send_event` lives in the `tasks` module's namespace.

### `MagicMock` vs `AsyncMock`
```python
# Synchronous mock
mock = MagicMock()
mock.some_method()  # Works
mock.return_value = 42

# Async mock (for async functions)
mock = AsyncMock()
await mock.some_method()  # Works with await
mock.return_value = 42

# Mock chain
mock_redis = MagicMock()
mock_r = AsyncMock()
mock_r.ping = AsyncMock(return_value=True)
mock_redis.return_value = mock_r
# Now: mock_redis() returns mock_r
# And: await mock_r.ping() returns True
```

### `side_effect` — Raise Exceptions or Dynamic Returns
```python
# Raise exception
mock.side_effect = RuntimeError("API exploded")
await mock()  # ❌ Raises RuntimeError

# Dynamic return based on input
mock.side_effect = lambda x: x * 2
mock(5)  # Returns 10

# Different returns on sequential calls
mock.side_effect = [1, 2, 3]
mock()  # 1
mock()  # 2
mock()  # 3
```

### Assertion Methods
```python
mock.assert_called_once()
mock.assert_called_once_with(arg1, arg2)
mock.assert_called_with(arg1, arg2)  # Last call
mock.assert_not_called()
assert mock.call_count == 3
```

---

## From Our Codebase — Test Examples

### TestClient Fixture
```python
@pytest.fixture
def client():
    """TestClient with mocked Kafka and Redis."""
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

Why mock startup/shutdown?
- Tests shouldn't need Kafka/Redis running
- Isolation: tests are fast and deterministic
- The mocks prevent real connections during TestClient init

### Endpoint Test
```python
@patch("src.api.endpoints.tasks.set_task_status", new_callable=AsyncMock)
@patch("src.api.endpoints.tasks.send_event", new_callable=AsyncMock)
def test_submit_returns_202(self, mock_send, mock_status, client):
    resp = client.post(
        "/api/v1/tasks/submit",
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )
    assert resp.status_code == 202
    assert "task_id" in resp.json()
    mock_send.assert_called_once()   # Kafka publish was called
    mock_status.assert_called_once() # Redis save was called
```

### Async Test
```python
@pytest.mark.asyncio
@patch("src.graphs.base_graph.call_llm", new_callable=AsyncMock)
async def test_successful_graph_execution(self, mock_llm):
    from src.graphs.base_graph import run_task_graph

    mock_llm.return_value = {
        "content": "LLM Response",
        "model_used": "gpt-4o-mini",
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        "finish_reason": "stop",
    }

    result = await run_task_graph(
        task_id="test-1",
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello"}],
    )

    assert result["status"] == "completed"
    assert result["llm_response"]["content"] == "LLM Response"
```

---

## `pytest.raises()` — Testing Exceptions

```python
# Assert exception is raised
with pytest.raises(ValidationError):
    TaskRequest(messages=[])

# Assert exception message matches
with pytest.raises(Exception, match="LLM API key"):
    Settings()  # In production without API keys

# Capture the exception for inspection
with pytest.raises(ValidationError) as exc_info:
    TaskRequest(messages=[], temperature=3.0)
assert "min_length" in str(exc_info.value)
```

---

## `@pytest.mark.parametrize` — Data-Driven Tests

```python
@pytest.mark.parametrize("temperature,valid", [
    (0.0, True),
    (0.7, True),
    (2.0, True),
    (-0.1, False),
    (2.1, False),
    (100, False),
])
def test_temperature_validation(temperature, valid):
    if valid:
        req = TaskRequest(
            messages=[{"role": "user", "content": "Hi"}],
            temperature=temperature,
        )
        assert req.temperature == temperature
    else:
        with pytest.raises(ValidationError):
            TaskRequest(
                messages=[{"role": "user", "content": "Hi"}],
                temperature=temperature,
            )
```

**PHP comparison:** PHPUnit's `@dataProvider`:
```php
/** @dataProvider temperatureProvider */
public function testTemperatureValidation(float $temp, bool $valid): void { ... }
public static function temperatureProvider(): array {
    return [[0.0, true], [0.7, true], [2.1, false]];
}
```

---

## Previous: [← FastAPI](11-fastapi.md) | Next: [Design Patterns →](13-design-patterns.md)
