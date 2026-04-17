# 09. Tratamento de Erros & Exceções

## PHP vs Python — Visão Geral

| PHP | Python |
|-----|--------|
| `try/catch/finally` | `try/except/else/finally` |
| `throw new Exception()` | `raise Exception()` |
| `Exception` | `Exception` |
| `\Throwable` | `BaseException` |
| `catch (TypeError $e)` | `except TypeError as e:` |
| Múltiplos `catch` | Múltiplos `except` |

---

## Sintaxe Básica

### PHP
```php
try {
    $result = riskyOperation();
} catch (InvalidArgumentException $e) {
    echo "Argumento inválido: " . $e->getMessage();
} catch (RuntimeException | LogicException $e) {
    echo "Erro: " . $e->getMessage();
} finally {
    cleanup();
}
```

### Python
```python
try:
    result = risky_operation()
except ValueError as e:
    print(f"Valor inválido: {e}")
except (RuntimeError, TypeError) as e:
    print(f"Erro: {e}")
except Exception as e:
    print(f"Erro inesperado: {e}")
else:
    # Executa SOMENTE se nenhuma exceção foi lançada
    print(f"Sucesso: {result}")
finally:
    cleanup()
```

### O bloco `else` (exclusivo do Python):
```python
try:
    data = json.loads(raw_string)
except json.JSONDecodeError:
    data = {}
else:
    # Só executa se o parse teve sucesso
    # Exceções aqui NÃO são capturadas pelo except acima
    process(data)
```

---

## Hierarquia de Exceções

```
BaseException
├── SystemExit           # sys.exit()
├── KeyboardInterrupt    # Ctrl+C
├── GeneratorExit
└── Exception            # ← Base para TODAS as exceções de aplicação
    ├── ValueError       # Valor inválido
    ├── TypeError        # Tipo errado
    ├── KeyError         # Chave não encontrada em dict
    ├── IndexError       # Índice fora do range
    ├── AttributeError   # Atributo não existe
    ├── FileNotFoundError
    ├── ConnectionError
    ├── TimeoutError
    ├── RuntimeError
    ├── ImportError
    ├── OSError
    └── ...
```

### Regra: sempre capture `Exception`, nunca `BaseException`:
```python
# ✅ Captura erros da aplicação
except Exception as e:
    ...

# ❌ Captura TUDO, incluindo Ctrl+C e sys.exit()!
except BaseException:
    ...

# ❌ Captura tudo silenciosamente — NUNCA faça isso!
except:
    pass
```

---

## `raise` — Lançando Exceções

### PHP
```php
throw new InvalidArgumentException("ID inválido: $id");
throw new RuntimeException("Falha na API", 0, $previousException);
```

### Python
```python
# Lançar exceção
raise ValueError(f"ID inválido: {task_id}")

# Re-lançar exceção capturada
except Exception as e:
    logger.error(f"Erro: {e}")
    raise  # Re-lança a MESMA exceção (preserva traceback)

# Encadeamento de exceções (exception chaining)
except ConnectionError as e:
    raise RuntimeError("Falha ao conectar ao banco") from e
# Output mostra ambas as exceções: a original e a nova
```

### No nosso código:
```python
# src/core/llm_router.py
async def call_llm(model: str, messages: list, **kwargs) -> dict:
    candidates = [model] + FALLBACK_MAP.get(model, [])
    last_error: Exception | None = None
    for candidate in candidates:
        try:
            response = await acompletion(...)
            return format_response(response, candidate)
        except Exception as e:
            last_error = e
            logger.warning(f"Model {candidate} failed: {e}")
            continue
    raise RuntimeError(
        f"All models failed for: {model}. Last error: {last_error}"
    )
```

---

## Exceções Customizadas

### PHP
```php
class TaskNotFoundException extends RuntimeException {
    public function __construct(string $taskId) {
        parent::__construct("Task não encontrada: $taskId");
    }
}
```

### Python
```python
class TaskNotFoundError(Exception):
    """Raised when a task cannot be found in Redis."""

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        super().__init__(f"Task not found: {task_id}")

# Uso:
raise TaskNotFoundError("abc-123")

# Captura:
try:
    task = await get_task(task_id)
except TaskNotFoundError as e:
    print(f"Task {e.task_id} não existe")
```

### Hierarquia de exceções do projeto:
```python
class NexusError(Exception):
    """Base exception for the Nexus application."""

class TaskNotFoundError(NexusError):
    """Task not found."""

class LLMError(NexusError):
    """LLM call failed."""

class KafkaPublishError(NexusError):
    """Failed to publish to Kafka."""
```

---

## FastAPI — `HTTPException`

### PHP (Laravel)
```php
abort(404, "Task not found");
abort(401, "Unauthorized");
```

### Python (FastAPI)
```python
from fastapi import HTTPException, status

# 404
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail=f"Task {task_id} not found",
)
# Retorna: {"detail": "Task abc-123 not found"}

# 401
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid API key",
    headers={"WWW-Authenticate": "Bearer"},
)
```

### No nosso código:
```python
# src/api/endpoints/tasks.py
async def verify_api_key(
    x_c2f_api_key: str | None = Header(None),
    settings: Settings = Depends(get_settings),
) -> Settings:
    if settings.is_production and settings.c2f_api_key:
        if not x_c2f_api_key or x_c2f_api_key != settings.c2f_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key",
            )
    return settings
```

---

## Pydantic — `ValidationError`

```python
from pydantic import ValidationError

try:
    request = TaskRequest(messages=[], temperature=5.0)
except ValidationError as e:
    print(e.error_count())  # 2
    print(e.errors())       # Lista de erros detalhados
    # [
    #   {"type": "too_short", "loc": ["messages"], ...},
    #   {"type": "less_than_equal", "loc": ["temperature"], ...},
    # ]
```

**FastAPI captura `ValidationError` automaticamente** e retorna 422 Unprocessable Entity.

---

## Boas Práticas

### 1. Seja específico no `except`:
```python
# ❌ Genérico demais
try:
    data = fetch_data()
except Exception:
    pass

# ✅ Específico
try:
    data = fetch_data()
except ConnectionError:
    data = cached_data
except TimeoutError:
    data = default_data
```

### 2. Não silencie exceções:
```python
# ❌ Bug silencioso
except Exception:
    pass

# ✅ Pelo menos logar
except Exception as e:
    logger.error(f"Falha: {e}", exc_info=True)
```

### 3. Use `else` para código de sucesso:
```python
# ✅ Separa o try do código de sucesso
try:
    data = json.loads(raw)
except json.JSONDecodeError:
    return default
else:
    # Exceções aqui são propagadas normalmente
    return process(data)
```

### 4. `finally` para cleanup:
```python
try:
    conn = connect()
    result = conn.query("SELECT 1")
finally:
    conn.close()  # Sempre executa!
```

### 5. Prefira context managers ao `finally`:
```python
# ❌ Manual
try:
    f = open("data.txt")
    data = f.read()
finally:
    f.close()

# ✅ Automático
with open("data.txt") as f:
    data = f.read()
```

---

## Anterior: [← Context Managers](08-context-managers.md) | Próximo: [Pydantic →](10-pydantic.md)
