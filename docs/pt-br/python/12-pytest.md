# 12. Testes com Pytest

## Testes PHP vs Python

| PHP (PHPUnit) | Python (pytest) |
|---------------|-----------------|
| `class FooTest extends TestCase` | `class TestFoo:` (sem classe base!) |
| `$this->assertEquals(a, b)` | `assert a == b` (assert puro) |
| `$this->expectException(E::class)` | `with pytest.raises(E):` |
| `setUp()` / `tearDown()` | Fixtures (`@pytest.fixture`) |
| `@dataProvider` | `@pytest.mark.parametrize` |
| `$this->createMock()` | `unittest.mock.patch()` / `MagicMock` |
| `phpunit.xml` | `pyproject.toml` ([tool.pytest]) |

---

## Configuração

### `pyproject.toml`
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"      # Auto-detecta testes async
testpaths = ["tests"]       # Onde encontrar testes
python_files = ["test_*.py"]  # Padrão de arquivos de teste
python_functions = ["test_*"]  # Padrão de funções de teste
```

### Executando Testes
```bash
# Todos os testes
python -m pytest tests/ -v

# Um arquivo
python -m pytest tests/test_api.py -v

# Uma classe
python -m pytest tests/test_api.py::TestHealthEndpoint -v

# Um método específico
python -m pytest tests/test_api.py::TestHealthEndpoint::test_health_returns_200 -v

# Com saída de print (sem captura)
python -m pytest tests/ -v -s

# Parar na primeira falha
python -m pytest tests/ -v -x
```

---

## Descoberta de Testes

pytest descobre testes automaticamente por convenção:
- Arquivos chamados `test_*.py` ou `*_test.py`
- Classes chamadas `Test*` (sem classe base!)
- Funções/métodos chamados `test_*`

```python
# tests/test_schemas.py
class TestTaskRequest:           # Classe agrupa testes relacionados
    def test_valid_minimal(self):    # Método de teste
        ...

    def test_empty_messages_fails(self):
        ...

# Ou funções standalone (sem classe):
def test_something():
    ...
```

**Comparação PHP:** No PHPUnit, testes devem estender `TestCase`. No pytest, são classes/funções simples — muito menos boilerplate.

---

## Assertions — `assert` Puro

```python
# PHPUnit: $this->assertEquals(200, $response->getStatusCode());
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

**Por que `assert` puro?** pytest reescreve statements de assert para fornecer **mensagens de falha detalhadas**:
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
    """Cria uma conexão de banco de teste."""
    connection = create_connection("sqlite:///:memory:")
    yield connection  # yield = setUp pronto, entrega ao teste
    connection.close()  # Depois do yield = tearDown

def test_query(db):  # db é injetado automaticamente!
    result = db.execute("SELECT 1")
    assert result is not None
```

### `yield` vs `return`:
- `return` — fixture entrega um valor, sem cleanup
- `yield` — fixture entrega um valor E executa cleanup depois do teste

### `autouse=True` — Aplica a TODOS os Testes

```python
# tests/conftest.py
@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch):
    """Executa automaticamente para cada teste."""
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("C2F_API_KEY", "test-api-key")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
```

### Escopos de Fixture
```python
@pytest.fixture(scope="function")  # Padrão: executa por teste
@pytest.fixture(scope="class")     # Uma vez por classe
@pytest.fixture(scope="module")    # Uma vez por arquivo
@pytest.fixture(scope="session")   # Uma vez por sessão de teste
```

---

## `conftest.py` — Fixtures Compartilhadas

`conftest.py` é um arquivo especial que o pytest descobre automaticamente. Fixtures definidas aqui ficam disponíveis para todos os testes no mesmo diretório (e subdiretórios).

```
tests/
├── conftest.py        # Fixtures compartilhadas (env vars, clients)
├── test_api.py        # Pode usar fixtures do conftest.py
├── test_graph.py
├── test_schemas.py
└── test_settings.py
```

Sem necessidade de import — pytest resolve automaticamente.

---

## `monkeypatch` — Modificações Temporárias

```python
def test_production_settings(monkeypatch):
    # Define env var (restaurada após o teste)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-prod-key")

    s = Settings()
    assert s.is_production is True

def test_missing_key(monkeypatch):
    # Remove env var (restaurada após o teste)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
```

**Comparação PHP:** PHPUnit tem manipulação de `$_ENV`, mas o `monkeypatch` do Python é mais poderoso — restaura TUDO automaticamente.

---

## Mocking — `unittest.mock`

### `patch()` — Substitui um Objeto a Nível de Módulo
```python
from unittest.mock import patch, MagicMock, AsyncMock

# Como decorator
@patch("src.api.endpoints.tasks.send_event", new_callable=AsyncMock)
def test_submit(mock_send):
    # send_event agora é um mock
    ...
    mock_send.assert_called_once()

# Como context manager
with patch("src.core.redis_client.get_redis") as mock_redis:
    mock_r = AsyncMock()
    mock_r.ping = AsyncMock(return_value=True)
    mock_redis.return_value = mock_r
```

### Regra-chave: Patch ONDE É USADO, Não Onde É Definido

```python
# ❌ Errado: patching onde send_event é definido
@patch("src.core.kafka_producer.send_event", ...)

# ✅ Correto: patching onde send_event é importado/usado
@patch("src.api.endpoints.tasks.send_event", ...)
```

### `MagicMock` vs `AsyncMock`
```python
# Mock síncrono
mock = MagicMock()
mock.some_method()  # Funciona

# Mock assíncrono (para funções async)
mock = AsyncMock()
await mock.some_method()  # Funciona com await
```

### `side_effect` — Lançar Exceções ou Retornos Dinâmicos
```python
# Lançar exceção
mock.side_effect = RuntimeError("API explodiu")

# Retornos sequenciais
mock.side_effect = [1, 2, 3]
mock()  # 1
mock()  # 2
mock()  # 3
```

### Métodos de Verificação
```python
mock.assert_called_once()
mock.assert_called_once_with(arg1, arg2)
mock.assert_not_called()
assert mock.call_count == 3
```

---

## Do Nosso Código — Exemplos de Teste

### Fixture TestClient
```python
@pytest.fixture
def client():
    """TestClient com Kafka e Redis mockados."""
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

### Teste de Endpoint
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
    mock_send.assert_called_once()
```

### Teste Async
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
```

---

## `pytest.raises()` — Testando Exceções

```python
# Assert que exceção é lançada
with pytest.raises(ValidationError):
    TaskRequest(messages=[])

# Assert que mensagem da exceção corresponde
with pytest.raises(Exception, match="LLM API key"):
    Settings()

# Capturar exceção para inspeção
with pytest.raises(ValidationError) as exc_info:
    TaskRequest(messages=[], temperature=3.0)
assert "min_length" in str(exc_info.value)
```

---

## `@pytest.mark.parametrize` — Testes Dirigidos por Dados

```python
@pytest.mark.parametrize("temperature,valid", [
    (0.0, True),
    (0.7, True),
    (2.0, True),
    (-0.1, False),
    (2.1, False),
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

**Comparação PHP:** `@dataProvider` do PHPUnit:
```php
/** @dataProvider temperatureProvider */
public function testTemperatureValidation(float $temp, bool $valid): void { ... }
```

---

## Anterior: [← FastAPI](11-fastapi.md) | Próximo: [Design Patterns →](13-design-patterns.md)
