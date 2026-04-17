# 13. Design Patterns no Código

Este módulo mapeia **design patterns conhecidos** para implementações concretas no nosso código do Conn2Flow Nexus AI. Se você programa PHP há 20 anos, já conhece esses patterns — aqui está como eles se apresentam em Python.

---

## 1. Singleton — Uma Instância, Global

### PHP
```php
class Settings {
    private static ?self $instance = null;

    public static function getInstance(): self {
        return self::$instance ??= new self();
    }

    private function __construct() {
        $this->loadEnv();
    }
}
```

### Python — `@lru_cache`
```python
# src/config/settings.py
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "conn2flow-nexus-ai"
    app_env: str = "development"
    ...

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

`@lru_cache` cacheia o valor de retorno. Primeira chamada cria a instância, chamadas subsequentes retornam a cacheada. Esse é o Singleton idiomático do Python.

### Singletons a Nível de Módulo
```python
# src/core/kafka_producer.py
_producer: AIOKafkaProducer | None = None   # Estado a nível de módulo

async def start_producer():
    global _producer
    _producer = AIOKafkaProducer(...)
    await _producer.start()

async def get_producer() -> AIOKafkaProducer:
    if _producer is None:
        raise RuntimeError("Producer not initialized")
    return _producer
```

**Padrão:** `_variável` a nível de módulo + função getter = singleton controlado.

---

## 2. Factory — Criação de Objetos

### Python — `create_app()`
```python
# src/main.py
def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Conn2Flow Nexus AI",
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.add_middleware(CORSMiddleware, ...)
    app.include_router(api_router, prefix="/api/v1")
    return app

app = create_app()
```

**Por que Factory?** Separa configuração de uso. Testes podem chamar `create_app()` com settings diferentes. O padrão `TestClient(app)` depende disso.

---

## 3. Strategy — Algoritmos Intercambiáveis

### Python — `FALLBACK_MAP`
```python
# src/core/llm_router.py
FALLBACK_MAP: dict[str, list[str]] = {
    "gpt-4o":            ["gpt-4o-mini", "claude-3-5-sonnet-20241022"],
    "gpt-4o-mini":       ["gpt-4o", "claude-3-5-haiku-20241022"],
    "claude-3-5-sonnet": ["gpt-4o", "gemini-1.5-pro"],
    ...
}

async def call_llm(model: str, messages: list, **kwargs) -> dict:
    """Tenta o modelo primário, depois fallback pelas alternativas."""
    candidates = [model] + FALLBACK_MAP.get(model, [])
    for candidate in candidates:
        try:
            response = await acompletion(model=candidate, messages=messages, **kwargs)
            return format_response(response, candidate)
        except Exception:
            continue
    raise RuntimeError(f"All models failed for: {model}")
```

A **Strategy** é selecionada pela chave `model`. A cadeia de fallback é o algoritmo de seleção. Adicionar um novo modelo é apenas uma nova entrada no dict.

---

## 4. Abstract Base Class (ABC) — Template Method

### Python
```python
# src/core/kafka_consumer.py
from abc import ABC, abstractmethod

class BaseKafkaConsumer(ABC):
    def __init__(self, topic: str, group_id: str):
        self._topic = topic
        self._group_id = group_id

    @abstractmethod
    async def handle_message(self, data: dict) -> None:
        """Subclasses DEVEM implementar este método."""
        ...

    async def run(self) -> None:
        """Template Method: start → consume → handle → repeat."""
        await self._start()
        try:
            async for msg in self._consumer:
                data = orjson.loads(msg.value)
                await self.handle_message(data)
        finally:
            await self._stop()
```

**Template Method Pattern:** O método `run()` define o esqueleto do algoritmo. Subclasses fornecem `handle_message()` — o passo variável.

### Implementação Concreta:
```python
# src/workers/task_processor.py
class TaskProcessor(BaseKafkaConsumer):
    async def handle_message(self, data: dict) -> None:
        event = TaskEvent(**data)
        result = await run_task_graph(
            task_id=event.task_id,
            model=event.model,
            messages=event.messages,
        )
        await send_event("c2f_completed_tasks", result_event)
```

---

## 5. State Machine — Ciclo de Vida da Task

### Python — State Machine com Redis
```python
# src/core/redis_client.py
async def set_task_status(task_id: str, status: str, data: dict | None = None):
    r = get_redis()
    payload = {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}
    if data:
        payload["result"] = data
    await r.set(f"task:{task_id}", orjson.dumps(payload), ex=3600)
```

Transições de estado:
```
queued → processing → completed
                   → failed
```

### LangGraph — State Machine Baseada em Grafo
```python
# src/graphs/base_graph.py
graph = StateGraph(dict)
graph.add_node("call_llm_node", call_llm_node)
graph.add_node("format_result_node", format_result_node)
graph.set_entry_point("call_llm_node")
graph.add_edge("call_llm_node", "format_result_node")
graph.add_edge("format_result_node", END)
compiled = graph.compile()
```

Cada nó é um estado. Arestas definem transições. LangGraph executa o grafo transitando entre estados.

---

## 6. Observer / Event-Driven — Kafka Pub/Sub

### Python — Tópicos Kafka
```python
# Producer (Publicador)
await send_event("c2f_incoming_tasks", task_event)

# Consumer (Assinante/Observer)
class TaskProcessor(BaseKafkaConsumer):
    def __init__(self):
        super().__init__(topic="c2f_incoming_tasks", group_id="task-processors")

    async def handle_message(self, data: dict) -> None:
        # Reage ao evento
        ...
        # Publica evento resultado
        await send_event("c2f_completed_tasks", result_event)
```

**Fluxo:**
```
API → Kafka (c2f_incoming_tasks) → TaskProcessor → Kafka (c2f_completed_tasks) → DeliveryWorker → Webhook
```

Múltiplos consumers podem assinar o mesmo tópico. Adicionar um novo observer é criar um novo consumer — sem mudanças no publisher.

---

## 7. Dependency Injection — FastAPI `Depends()`

### Python (FastAPI)
```python
async def verify_api_key(
    x_c2f_api_key: str | None = Header(None),
    settings: Settings = Depends(get_settings),
) -> Settings:
    if settings.is_production and settings.c2f_api_key:
        if not x_c2f_api_key or x_c2f_api_key != settings.c2f_api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")
    return settings

@router.post("/submit")
async def submit_task(
    payload: TaskRequest,
    settings: Settings = Depends(verify_api_key),
):
    ...
```

`Depends()` é como o service container do Laravel, mas declarado no nível do parâmetro da função. FastAPI resolve o grafo de dependências automaticamente.

---

## 8. Decorator Pattern — Envolvendo Comportamento

```python
import functools
import time

def log_execution_time(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info(f"{func.__name__} levou {elapsed:.3f}s")
        return result
    return wrapper

@log_execution_time
async def call_llm(model: str, messages: list, **kwargs):
    ...
```

A sintaxe `@decorator` do Python torna este pattern uma feature nativa. Veja [Módulo 04 — Funções & Decorators](04-funcoes-decorators.md).

---

## Tabela Resumo

| Pattern | PHP | Python (Nosso Código) | Arquivo |
|---------|-----|----------------------|---------|
| Singleton | `static $instance` | `@lru_cache`, `_var` do módulo | `settings.py`, `kafka_producer.py`, `redis_client.py` |
| Factory | Static factory method | `create_app()` | `main.py` |
| Strategy | Interface + implementações | `FALLBACK_MAP` dict | `llm_router.py` |
| Abstract Base Class | `abstract class` | `ABC` + `@abstractmethod` | `kafka_consumer.py` |
| State Machine | Enum + transições | Redis status + LangGraph | `redis_client.py`, `base_graph.py` |
| Observer/Event-Driven | Events + Listeners | Tópicos Kafka | `kafka_producer.py`, `task_processor.py` |
| Dependency Injection | Container/construtor | `Depends()` | `tasks.py`, `health.py` |
| Decorator | Classe Middleware | Funções `@decorator` | por todo o código |

---

## Anterior: [← Testes com Pytest](12-pytest.md) | Próximo: [Ecossistema & Ferramentas →](14-ecossistema-ferramentas.md)
