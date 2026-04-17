# 13. Design Patterns in the Codebase

This module maps **well-known design patterns** to concrete implementations in our Conn2Flow Nexus AI codebase. If you've been writing PHP for 20 years, you already know these patterns — here's how they look in Python.

---

## 1. Singleton — One Instance, Globally

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
// Usage: Settings::getInstance()->get('app_env')
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

`@lru_cache` caches the return value. First call creates the instance, subsequent calls return the cached one. This is Python's idiomatic Singleton.

### Global Module-Level Singletons
```python
# src/core/kafka_producer.py
_producer: AIOKafkaProducer | None = None   # Module-level state

async def start_producer():
    global _producer
    _producer = AIOKafkaProducer(...)
    await _producer.start()

async def get_producer() -> AIOKafkaProducer:
    if _producer is None:
        raise RuntimeError("Producer not initialized")
    return _producer
```

**Pattern:** Module-level `_variable` + getter function = controlled singleton.

---

## 2. Factory — Object Creation

### PHP
```php
class AppFactory {
    public static function create(): Application {
        $app = new Application();
        $app->registerMiddleware([...]);
        $app->registerRoutes([...]);
        return $app;
    }
}
```

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

**Why Factory?** Separates configuration from usage. Tests can call `create_app()` with different settings. The `TestClient(app)` pattern depends on this.

---

## 3. Strategy — Swappable Algorithms

### PHP
```php
interface PaymentStrategy {
    public function pay(float $amount): bool;
}

class PayPalPayment implements PaymentStrategy {
    public function pay(float $amount): bool { ... }
}

class StripePayment implements PaymentStrategy {
    public function pay(float $amount): bool { ... }
}
```

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
    """Tries the primary model, then falls back through alternatives."""
    candidates = [model] + FALLBACK_MAP.get(model, [])
    for candidate in candidates:
        try:
            response = await acompletion(model=candidate, messages=messages, **kwargs)
            return format_response(response, candidate)
        except Exception:
            continue
    raise RuntimeError(f"All models failed for: {model}")
```

The **Strategy** is selected by `model` key. The fallback chain is the strategy's selection algorithm. Adding a new model is just a new dict entry.

---

## 4. Abstract Base Class (ABC) — Template Method

### PHP
```php
abstract class BaseConsumer {
    abstract protected function handleMessage(array $data): void;

    public function run(): void {
        while ($msg = $this->consume()) {
            $this->handleMessage($msg);
        }
    }
}
```

### Python
```python
# src/core/kafka_consumer.py
from abc import ABC, abstractmethod

class BaseKafkaConsumer(ABC):
    def __init__(self, topic: str, group_id: str):
        self._topic = topic
        self._group_id = group_id
        self._consumer: AIOKafkaConsumer | None = None

    @abstractmethod
    async def handle_message(self, data: dict) -> None:
        """Subclasses MUST implement this."""
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

**Template Method Pattern:** The `run()` method defines the algorithm skeleton. Subclasses provide `handle_message()` — the variable step.

### Concrete Implementation:
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

## 5. State Machine — Task Lifecycle

### PHP
```php
enum TaskStatus: string {
    case QUEUED = 'queued';
    case PROCESSING = 'processing';
    case COMPLETED = 'completed';
    case FAILED = 'failed';
}
```

### Python — Redis-Backed State Machine
```python
# src/core/redis_client.py
async def set_task_status(task_id: str, status: str, data: dict | None = None):
    r = get_redis()
    payload = {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}
    if data:
        payload["result"] = data
    await r.set(f"task:{task_id}", orjson.dumps(payload), ex=3600)
```

State transitions:
```
queued → processing → completed
                   → failed
```

Each transition is an explicit `set_task_status()` call. State is persisted in Redis with TTL.

### LangGraph — Graph-Based State Machine
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

Each node is a state. Edges define transitions. LangGraph executes the graph, transitioning between states based on edge definitions.

---

## 6. Observer / Event-Driven — Kafka Pub/Sub

### PHP
```php
// Laravel Events
event(new TaskCompleted($task));

// Listener
class SendWebhook {
    public function handle(TaskCompleted $event): void {
        Http::post($event->webhookUrl, $event->toArray());
    }
}
```

### Python — Kafka Topics
```python
# Producer (Publisher)
# src/api/endpoints/tasks.py
await send_event("c2f_incoming_tasks", task_event)

# Consumer (Subscriber/Observer)
# src/workers/task_processor.py
class TaskProcessor(BaseKafkaConsumer):
    def __init__(self):
        super().__init__(topic="c2f_incoming_tasks", group_id="task-processors")

    async def handle_message(self, data: dict) -> None:
        # React to the event
        ...
        # Publish result event
        await send_event("c2f_completed_tasks", result_event)
```

**Pattern flow:**
```
API → Kafka (c2f_incoming_tasks) → TaskProcessor → Kafka (c2f_completed_tasks) → DeliveryWorker → Webhook
```

Multiple consumers can subscribe to the same topic. Adding a new observer is creating a new consumer — no changes to the publisher.

---

## 7. Dependency Injection — FastAPI `Depends()`

### PHP (Laravel)
```php
// Constructor injection
class TaskController {
    public function __construct(
        private KafkaService $kafka,
        private SettingsService $settings,
    ) {}

    public function submit(TaskRequest $request): JsonResponse {
        $this->kafka->send('tasks', $request->validated());
    }
}
```

### Python (FastAPI)
```python
# src/api/endpoints/tasks.py
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

`Depends()` is like Laravel's service container, but declared at the function parameter level. FastAPI resolves the dependency graph automatically.

---

## 8. Decorator Pattern — Wrapping Behavior

### PHP
```php
// Middleware wraps request handling
class LoggingMiddleware {
    public function handle(Request $request, Closure $next): Response {
        Log::info("Request: " . $request->url());
        $response = $next($request);
        Log::info("Response: " . $response->status());
        return $response;
    }
}
```

### Python
```python
import functools
import time

def log_execution_time(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info(f"{func.__name__} took {elapsed:.3f}s")
        return result
    return wrapper

@log_execution_time
async def call_llm(model: str, messages: list, **kwargs):
    ...
```

Python's `@decorator` syntax makes this pattern first-class. See [Module 04 — Functions & Decorators](04-functions-decorators.md).

---

## Pattern Summary Table

| Pattern | PHP | Python (Our Codebase) | File |
|---------|-----|----------------------|------|
| Singleton | `static $instance` | `@lru_cache`, module `_var` | `settings.py`, `kafka_producer.py`, `redis_client.py` |
| Factory | Static factory method | `create_app()` | `main.py` |
| Strategy | Interface + implementations | `FALLBACK_MAP` dict | `llm_router.py` |
| Abstract Base Class | `abstract class` | `ABC` + `@abstractmethod` | `kafka_consumer.py` |
| State Machine | Enum + transitions | Redis status + LangGraph | `redis_client.py`, `base_graph.py` |
| Observer/Event-Driven | Events + Listeners | Kafka topics | `kafka_producer.py`, `task_processor.py` |
| Dependency Injection | Container/constructor | `Depends()` | `tasks.py`, `health.py` |
| Decorator | Middleware class | `@decorator` functions | throughout codebase |

---

## Previous: [← Testing with Pytest](12-pytest.md) | Next: [Ecosystem & Tooling →](14-ecosystem-tooling.md)
