# 10. Testes — Pytest, Mocking e TestClient

## Filosofia de Testes no Projeto

O projeto usa **testes unitários** com mocking — testamos cada componente **isoladamente**, sem depender de serviços externos (Kafka, Redis, APIs de LLM).

### Ferramentas

| Ferramenta | Uso |
|------------|-----|
| **pytest** | Framework de testes Python |
| **pytest-asyncio** | Suporte para testes async (`async def test_*`) |
| **unittest.mock** | Mocking de dependências (da stdlib do Python) |
| **FastAPI TestClient** | Simula requests HTTP sem servidor real |

---

## Configuração: `pyproject.toml`

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
```

**`asyncio_mode = "auto"`** → pytest-asyncio detecta automaticamente testes `async def` e os roda no event loop. Sem isso, precisaríamos decorar cada teste com `@pytest.mark.asyncio`.

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

### Conceitos-Chave:

**`@pytest.fixture`**
- Uma fixture é uma **função de setup** que prepara o ambiente para testes
- Pode ser injetada em testes pelo nome do parâmetro

**`autouse=True`**
- A fixture roda **automaticamente** em todos os testes do mesmo escopo
- Não precisa ser declarada como parâmetro de cada teste
- Útil para setup global como variáveis de ambiente

**`monkeypatch`**
- Fixture built-in do pytest para modificar temporariamente objetos/variáveis
- `monkeypatch.setenv("KEY", "value")` → define variável de ambiente **apenas durante o teste**
- Após o teste, o valor original é restaurado automaticamente
- Seguro: não afeta outros testes

---

## TestClient — Testando a API HTTP

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

**Conceito: `TestClient`**
- Simula um servidor HTTP **em memória** — não precisa de porta, rede ou uvicorn
- `client.get("/api/v1/health")` → faz um GET real na API
- `client.post("/api/v1/tasks/submit", json={...})` → faz um POST com body JSON
- Internamente, usa HTTPX para simular requests

**Conceito: `patch()` como Context Manager**
```python
with patch("src.main.start_redis", new_callable=AsyncMock):
```
- `patch()` substitui temporariamente um objeto por um mock
- `"src.main.start_redis"` → o path **onde é usado**, não onde é definido
- `AsyncMock` → mock que funciona com `await` (retorna coroutine)
- Ao sair do `with`, o objeto original é restaurado

**Por que mock o Kafka/Redis?**
- Testes unitários **não** devem depender de serviços externos
- Se Kafka estivesse fora, o teste falharia por timeout, não por bug
- Mocks garantem testes **rápidos**, **determinísticos** e **isolados**

---

## Testando Endpoints

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

**Conceito: Mock Chain**
- `mock_redis.return_value = mock_r` → quando `get_redis()` é chamado, retorna `mock_r`
- `mock_r.ping = AsyncMock(return_value=True)` → quando `mock_r.ping()` é chamado, retorna `True`
- Isso simula: `get_redis().ping()` → `True`, sem Redis real

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
    mock_send.assert_called_once()   # Verificou que publicou no Kafka
    mock_status.assert_called_once() # Verificou que salvou no Redis
```

**Conceito: `@patch` como Decorator**
- Quando usado como decorator, os mocks são passados como **parâmetros** do teste
- Ordem: decorators de baixo para cima → parâmetros da esquerda para direita
- `mock_send.assert_called_once()` → verifica que a função foi chamada **exatamente 1 vez**

---

## Testando Código Async

### LangGraph

```python
@pytest.mark.asyncio
@patch("src.graphs.base_graph.call_llm", new_callable=AsyncMock)
async def test_successful_graph_execution(self, mock_llm):
    mock_llm.return_value = {
        "content": "Resposta do LLM",
        "model_used": "gpt-4o-mini",
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        "finish_reason": "stop",
    }

    result = await run_task_graph(
        task_id="test-1",
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Olá"}],
    )

    assert result["status"] == "completed"
    assert result["llm_response"]["content"] == "Resposta do LLM"
```

**Conceito: `@pytest.mark.asyncio`**
- Diz ao pytest-asyncio que este teste é uma coroutine
- Com `asyncio_mode = "auto"`, é detectado automaticamente (mas manter é boa prática)

**Mock do LLM:**
- `mock_llm.return_value = {...}` → quando `call_llm()` for chamado, retorna o dict
- Não faz chamada real à API — retorno instantâneo e determinístico
- Podemos testar cenários impossíveis de reproduzir com API real

### Testando Falhas

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

**Conceito: `side_effect`**
- `side_effect = RuntimeError(...)` → em vez de retornar valor, **lança exceção**
- Permite testar como o código lida com erros
- Essencial para validar que o grafo captura exceções corretamente

---

## Testando Schemas (Pydantic)

```python
def test_empty_messages_fails(self):
    with pytest.raises(ValidationError):
        TaskRequest(messages=[])

def test_temperature_out_of_range(self):
    with pytest.raises(ValidationError):
        TaskRequest(messages=[...], temperature=3.0)
```

**Conceito: `pytest.raises()`**
- Verifica que o código dentro do bloco **lança** a exceção esperada
- Se a exceção **não** for lançada, o teste **falha**
- Garante que validações do Pydantic estão funcionando

---

## Rodando os Testes

```bash
# Todos os testes
python -m pytest tests/ -v

# Apenas um arquivo
python -m pytest tests/test_api.py -v

# Apenas um teste
python -m pytest tests/test_api.py::TestHealthEndpoint::test_health_returns_200 -v

# Com output detalhado de falhas
python -m pytest tests/ -v --tb=long
```

---

## Anterior: [← Docker](09-docker.md) | Próximo: [Segurança →](11-seguranca.md)
