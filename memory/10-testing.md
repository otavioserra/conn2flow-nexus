# SPEC-10: Testing

> **Status**: ✅ Approved
> **Version**: 1.0.0
> **Created**: 2025-07-16
> **Last updated**: 2025-07-16

---

## 1. Testing Strategy

| Aspect | Value |
|--------|-------|
| **Framework** | pytest 8.x |
| **Async** | pytest-asyncio 0.26+ |
| **HTTP** | httpx (AsyncClient) |
| **Mocking** | unittest.mock (patch, AsyncMock, MagicMock) |
| **Coverage** | pytest-cov |
| **Approach** | Unit tests with external dependencies fully mocked |

**Rule**: All tests run WITHOUT Docker, WITHOUT Kafka, WITHOUT Redis, WITHOUT real LLM APIs.

## 2. Test Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── test_config.py                 # Settings tests
├── test_health.py                 # GET /health tests
├── test_main.py                   # FastAPI app tests
├── test_models.py                 # Pydantic model tests
├── test_security.py               # Auth and HMAC tests
├── test_submit.py                 # POST /tasks/submit tests
├── test_status.py                 # GET /tasks/status/{id} tests
├── test_redis_store.py            # RedisTaskStore tests
├── test_kafka_producer_service.py # KafkaProducerService tests
├── test_task_worker.py            # TaskWorker tests
└── test_delivery_worker.py        # DeliveryWorker tests
```

## 3. Fixtures (conftest.py)

### `mock_settings`
Provides a consistent `Settings` instance for all tests:

```python
@pytest.fixture
def mock_settings():
    return Settings(
        app_name="Test App",
        app_env="development",
        app_debug=True,
        kafka_bootstrap_servers="localhost:9092",
        redis_url="redis://localhost:6379/0",
    )
```

### `test_client`
HTTP client with overridden dependencies:

```python
@pytest.fixture
def test_client(mock_settings):
    app.dependency_overrides[get_settings] = lambda: mock_settings
    app.dependency_overrides[verify_api_key] = lambda: mock_settings
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
```

### `async_client`
Async HTTP client for async tests:

```python
@pytest.fixture
async def async_client(mock_settings):
    app.dependency_overrides[get_settings] = lambda: mock_settings
    app.dependency_overrides[verify_api_key] = lambda: mock_settings
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
    app.dependency_overrides.clear()
```

## 4. Test Suite (Summary)

### test_config.py (Settings)

| # | Test | Validates |
|---|------|----------|
| 1 | Default values | All defaults are correct |
| 2 | `is_production` / `is_development` | Derived properties |
| 3 | `cors_origins` per environment | `["*"]` in dev, `[]` in prod |
| 4 | `get_settings()` singleton | Returns same instance |

### test_health.py

| # | Test | Validates |
|---|------|----------|
| 1 | `GET /health` → 200 | Returns `{"status": "ok"}` |

### test_main.py

| # | Test | Validates |
|---|------|----------|
| 1 | App metadata | Title, version, docs_url |
| 2 | CORS middleware | Middleware is registered |
| 3 | Routes exist | All expected routes are registered |

### test_models.py

| # | Test | Validates |
|---|------|----------|
| 1 | Valid TaskSubmitRequest | Accepts valid data |
| 2 | Empty messages | Rejects `messages=[]` |
| 3 | Invalid temperature | Rejects `temperature > 2.0` |
| 4 | Default values | Defaults are applied correctly |
| 5 | TaskSubmitResponse | Response has `task_id` and `status` |
| 6 | TaskStatusResponse | All status fields are present |

### test_security.py

| # | Test | Validates |
|---|------|----------|
| 1 | Valid API key | Accepted in production |
| 2 | Invalid API key | Returns 401 |
| 3 | Missing API key | Returns 401 |
| 4 | Development bypass | Auth skipped |
| 5 | HMAC generation | Correct signature |
| 6 | HMAC empty secret | Returns empty string |

### test_submit.py

| # | Test | Validates |
|---|------|----------|
| 1 | Successful submission | Returns 202 + task_id |
| 2 | Invalid body | Returns 422 |
| 3 | Redis failure | Returns 500 |
| 4 | Kafka failure | Returns 500 |

### test_status.py

| # | Test | Validates |
|---|------|----------|
| 1 | Found task | Returns 200 + full data |
| 2 | Not found | Returns 404 |
| 3 | Redis failure | Returns 500 |

### test_redis_store.py

| # | Test | Validates |
|---|------|----------|
| 1 | `save_task()` | Calls `redis.set()` with TTL |
| 2 | `get_task()` found | Returns parsed dict |
| 3 | `get_task()` not found | Returns `None` |
| 4 | `update_task()` | Merges with existing data |

### test_kafka_producer_service.py

| # | Test | Validates |
|---|------|----------|
| 1 | `start()` and `stop()` | Lifecycle of AIOKafkaProducer |
| 2 | `send_message()` | Serialization and dispatch |

### test_task_worker.py

| # | Test | Validates |
|---|------|----------|
| 1 | Successful processing | LLM call + Redis update + Kafka publish |
| 2 | LLM failure | Error handling and status update |

### test_delivery_worker.py

| # | Test | Validates |
|---|------|----------|
| 1 | Successful delivery | HTTP POST with HMAC |
| 2 | HTTP failure | Retry logic and error status |

## 5. Mock Patterns

### Redis Mock

```python
mock_redis = AsyncMock()
mock_redis.set = AsyncMock(return_value=True)
mock_redis.get = AsyncMock(return_value='{"task_id": "abc", "status": "pending"}')
```

### Kafka Mock

```python
mock_producer = AsyncMock()
mock_producer.start = AsyncMock()
mock_producer.stop = AsyncMock()
mock_producer.send_and_wait = AsyncMock()
```

### LiteLLM Mock

```python
with patch("src.workers.task_worker.acompletion") as mock_llm:
    mock_llm.return_value = mock_response
```

### httpx Mock

```python
with patch("src.workers.delivery_worker.httpx.AsyncClient") as mock_client:
    mock_client.return_value.__aenter__.return_value.post = AsyncMock(
        return_value=Response(200)
    )
```

## 6. Running Tests

```bash
# Run all tests
pytest

# With verbose output
pytest -v

# With coverage
pytest --cov=src --cov-report=term-missing

# Specific file
pytest tests/test_submit.py

# Specific test
pytest tests/test_submit.py::test_submit_success -v
```

## 7. Future Test Roadmap

| Phase | Tests |
|-------|-------|
| v0.2 | Integration tests with Docker Compose |
| v0.3 | Performance/load tests with Locust |
| v0.4 | E2E tests with real LLM (controlled budget) |
# SPEC-10: Testing

> **Status**: ✅ Aprovada
> **Versão**: 1.0.0
> **Criada em**: 2025-07-16
> **Última atualização**: 2025-07-16

---

## 1. Estratégia de Testes

| Tipo | Framework | Propósito | Cobertura |
|------|-----------|-----------|-----------|
| **Unit Tests** | pytest + pytest-asyncio | Testar componentes isolados | Schemas, settings, API, LLM router, graph |
| **Integration Tests** | (futuro) | Testar fluxo completo com Kafka/Redis reais | End-to-end |

### Configuração

**`pyproject.toml`**:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

**Regras**:
- `asyncio_mode = "auto"` — funções `async def test_xxx` são automaticamente tratadas como testes assíncronos
- Todos os testes ficam em `tests/`
- Fixtures globais em `tests/conftest.py`

## 2. Fixtures

### `conftest.py` — Fixture de Isolamento

```python
@pytest.fixture(autouse=True)
def _isolate_settings(monkeypatch):
    """Fixa variáveis de ambiente e limpa o cache de settings entre testes."""
    monkeypatch.setenv("APP_NAME", "test-app")
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    get_settings.cache_clear()
```

**Regras**:
- `autouse=True` — aplicada a TODOS os testes automaticamente
- Fixa variáveis de ambiente para valores de teste
- Limpa o `@lru_cache` do `get_settings()` entre testes
- Garante isolamento: um teste não afeta outro

## 3. Suíte de Testes Atual

### 3.1. `test_schemas.py` — 18 testes

Testa a validação Pydantic dos schemas de request/response e eventos.

| Teste | O que valida |
|-------|-------------|
| Criação de `TaskRequest` com defaults | Valores default corretos |
| `TaskRequest` com todos os campos | Todos os campos aceitos |
| `TaskRequest` sem messages | Erro de validação (`min_length=1`) |
| `TaskRequest` com messages vazio | Erro de validação |
| `TaskRequest` com temperature inválida | `>2.0` ou `<0.0` rejeitado |
| `TaskRequest` com max_tokens inválido | `≤0` ou `>128000` rejeitado |
| `TaskAcceptedResponse` | Campos obrigatórios |
| `TaskStatusResponse` com resultado | `result` presente |
| `TaskStatusResponse` com erro | `error` presente |
| `TaskEvent` | Serialização + `created_at` auto |
| `TaskResultEvent` sucesso | `status="completed"` |
| `TaskResultEvent` falha | `status="failed"` + `error` |
| Serialização JSON dos events | `model_dump(mode="json")` funciona |

### 3.2. `test_settings.py` — 5 testes

| Teste | O que valida |
|-------|-------------|
| Settings com defaults | Valores default da classe |
| `is_production` property | `True` quando `app_env="production"` |
| `is_production` em dev | `False` quando `app_env="development"` |
| Validação de LLM keys em produção | `ValueError` sem keys em prod |
| Settings com LLM key em produção | Aceita quando pelo menos 1 key existe |

### 3.3. `test_api.py` — 7 testes

Usa `TestClient` do FastAPI (síncrono).

| Teste | O que valida |
|-------|-------------|
| `GET /health` | Retorna 200 com status |
| `POST /tasks/submit` válido | Retorna 202 com task_id |
| `POST /tasks/submit` sem messages | Retorna 422 |
| `POST /tasks/submit` com messages vazio | Retorna 422 |
| `GET /tasks/status/{id}` existente | Retorna 200 com dados |
| `GET /tasks/status/{id}` inexistente | Retorna 404 |
| API key em produção | Retorna 401 sem key válida |

**Mocks**: Kafka producer e Redis client são mockados para testes de API.

### 3.4. `test_llm_router.py` — 6 testes

| Teste | O que valida |
|-------|-------------|
| `call_llm` com resposta válida | Retorna dict com content, model_used, usage |
| `call_llm` com fallback | Fallback funciona quando modelo principal falha |
| `_configure_api_keys` | Keys são injetadas no `os.environ` |
| `FALLBACK_MAP` structure | Mapa contém os modelos esperados |
| Tratamento de `AuthenticationError` | Exceção é re-raised |
| Tratamento de `RateLimitError` | Exceção é re-raised |

**Mocks**: `litellm.acompletion` é mockado.

### 3.5. `test_graph.py` — 4 testes

| Teste | O que valida |
|-------|-------------|
| `validate_input` com messages válidas | Retorna `status="processing"` |
| `validate_input` sem messages | Retorna error |
| `validate_input` sem role user | Retorna error |
| `run_task_graph` completo | Grafo executa do início ao fim |

**Mocks**: `call_llm` é mockado para isolar o grafo.

## 4. Total de Testes

| Módulo | Quantidade |
|--------|-----------|
| `test_schemas.py` | 18 |
| `test_settings.py` | 5 |
| `test_api.py` | 7 |
| `test_llm_router.py` | 6 |
| `test_graph.py` | 4 |
| **Total** | **40** |

## 5. Como Executar

```bash
# Todos os testes
pytest

# Com output verboso
pytest -v

# Módulo específico
pytest tests/test_api.py

# Teste específico
pytest tests/test_api.py::test_submit_task_valid

# Com cobertura (futuro - precisa pytest-cov)
pytest --cov=src --cov-report=html
```

## 6. Padrões de Mock

### Kafka Producer

```python
@pytest.fixture
def mock_kafka(monkeypatch):
    async def fake_send(*args, **kwargs):
        pass
    monkeypatch.setattr("src.core.kafka_producer.send_event", fake_send)
```

### Redis Client

```python
@pytest.fixture
def mock_redis(monkeypatch):
    store = {}
    async def fake_set(task_id, status, data=None, ttl=None):
        store[task_id] = {"status": status, **(data or {})}
    async def fake_get(task_id):
        return store.get(task_id)
    monkeypatch.setattr("src.core.redis_client.set_task_status", fake_set)
    monkeypatch.setattr("src.core.redis_client.get_task_status", fake_get)
```

### LiteLLM

```python
from unittest.mock import AsyncMock
mock_completion = AsyncMock(return_value=MockResponse(...))
monkeypatch.setattr("litellm.acompletion", mock_completion)
```

## 7. Testes Futuros (Roadmap)

| Área | Tipo | Descrição |
|------|------|-----------|
| Workers | Integration | Testar TaskProcessorWorker com Kafka real |
| Delivery | Integration | Testar DeliveryWorker com httpx mock server |
| HMAC | Unit | Verificar assinatura e validação |
| End-to-end | E2E | Submit → Process → Deliver com Docker Compose |
| Performance | Load | Benchmark com locust ou k6 |
| Coverage | Metric | Meta: ≥80% de cobertura de código |
