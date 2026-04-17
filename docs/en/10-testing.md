# 10. Testing — Pytest, Mocking and TestClient

## Testing Philosophy in the Project

The project uses **unit tests** with mocking — we test each component **in isolation**, without depending on external services (Kafka, Redis, LLM APIs).

### Tools

| Tool | Usage |
|------|-------|
| **pytest** | Python testing framework |
| **pytest-asyncio** | Support for async tests (`async def test_*`) |
| **unittest.mock** | Dependency mocking (from the Python stdlib) |
| **FastAPI TestClient** | Simulates HTTP requests without a real server |

---

## Configuration: `pyproject.toml`

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
```

**`asyncio_mode = "auto"`** → pytest-asyncio automatically detects `async def` tests and runs them in the event loop. Without this, we'd need to decorate each test with `@pytest.mark.asyncio`.

---

## Fixtures: `tests/conftest.py`

```python
@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("C2F_API_KEY", "test-api-key")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
```

### Key Concepts:

**`@pytest.fixture`**
- A fixture is a **setup function** that prepares the environment for tests
- Can be injected into tests by parameter name

**`autouse=True`**
- The fixture runs **automatically** in all tests of the same scope
- Doesn't need to be declared as a parameter of each test
- Useful for global setup like environment variables

**`monkeypatch`**
- A built-in pytest fixture for temporarily modifying objects/variables
- `monkeypatch.setenv("KEY", "value")` → sets an environment variable **only during the test**
- After the test, the original value is automatically restored
- Safe: doesn't affect other tests

---

## TestClient — Testing the HTTP API

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

**Concept: `TestClient`**
- Simulates an **in-memory** HTTP server — no port, network, or uvicorn needed
- `client.get("/api/v1/health")` → makes a real GET to the API
- `client.post("/api/v1/tasks/submit", json={...})` → makes a POST with JSON body
- Internally, uses HTTPX to simulate requests

**Concept: `patch()` as Context Manager**
```python
with patch("src.main.start_redis", new_callable=AsyncMock):
```
- `patch()` temporarily replaces an object with a mock
- `"src.main.start_redis"` → the path **where it's used**, not where it's defined
- `AsyncMock` → a mock that works with `await` (returns coroutine)
- When exiting the `with`, the original object is restored

**Why mock Kafka/Redis?**
- Unit tests should **not** depend on external services
- If Kafka were down, the test would fail due to timeout, not a bug
- Mocks ensure tests are **fast**, **deterministic**, and **isolated**

---

## Testing Endpoints

### Health Check

```python
def test_health_returns_200(self, client):
    with patch("src.core.redis_client.get_redis") as mock_redis:
        mock_r = AsyncMock()
        mock_r.ping = AsyncMock(return_value=True)
        mock_redis.return_value = mock_r
        resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert data["service"] == "conn2flow-nexus-ai"
```

**Concept: Mock Chain**
- `mock_redis.return_value = mock_r` → when `get_redis()` is called, returns `mock_r`
- `mock_r.ping = AsyncMock(return_value=True)` → when `mock_r.ping()` is called, returns `True`
- This simulates: `get_redis().ping()` → `True`, without real Redis

### Task Submit

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
    mock_send.assert_called_once()   # Verified it published to Kafka
    mock_status.assert_called_once() # Verified it saved to Redis
```

**Concept: `@patch` as Decorator**
- When used as a decorator, mocks are passed as **parameters** to the test
- Order: decorators bottom to top → parameters left to right
- `mock_send.assert_called_once()` → verifies the function was called **exactly once**

---

## Testing Async Code

### LangGraph

```python
@pytest.mark.asyncio
@patch("src.graphs.base_graph.call_llm", new_callable=AsyncMock)
async def test_successful_graph_execution(self, mock_llm):
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

**Concept: `@pytest.mark.asyncio`**
- Tells pytest-asyncio that this test is a coroutine
- With `asyncio_mode = "auto"`, it's detected automatically (but keeping it is good practice)

**LLM Mock:**
- `mock_llm.return_value = {...}` → when `call_llm()` is called, returns the dict
- No real API call — instant and deterministic return
- We can test scenarios impossible to reproduce with a real API

### Testing Failures

```python
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

**Concept: `side_effect`**
- `side_effect = RuntimeError(...)` → instead of returning a value, **raises an exception**
- Allows testing how the code handles errors
- Essential for validating that the graph catches exceptions correctly

---

## Testing Schemas (Pydantic)

```python
def test_empty_messages_fails(self):
    with pytest.raises(ValidationError):
        TaskRequest(messages=[])

def test_temperature_out_of_range(self):
    with pytest.raises(ValidationError):
        TaskRequest(messages=[...], temperature=3.0)
```

**Concept: `pytest.raises()`**
- Verifies that the code inside the block **raises** the expected exception
- If the exception is **not** raised, the test **fails**
- Ensures Pydantic validations are working

---

## Running Tests

```bash
# All tests
python -m pytest tests/ -v

# Only one file
python -m pytest tests/test_api.py -v

# Only one test
python -m pytest tests/test_api.py::TestHealthEndpoint::test_health_returns_200 -v

# With detailed failure output
python -m pytest tests/ -v --tb=long
```

---

## Previous: [← Docker](09-docker.md) | Next: [Security →](11-security.md)
