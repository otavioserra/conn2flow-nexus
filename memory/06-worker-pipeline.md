# SPEC-06: Worker Pipeline

> **Status**: ✅ Approved
> **Version**: 1.0.0
> **Created**: 2025-07-16
> **Last updated**: 2025-07-16

---

## 1. Overview

The processing pipeline is composed of two independent workers that communicate via Kafka:

1. **Task Worker**: Consumes tasks → executes LangGraph → publishes results
2. **Delivery Worker**: Consumes results → delivers via Webhook

Both extend the base class `BaseKafkaConsumer` (Template Method Pattern).

## 2. BaseKafkaConsumer (Base Class)

### Interface

```python
class BaseKafkaConsumer(ABC):
    def __init__(self, topic: str, settings: Settings | None = None)
    async def start() -> None         # Initialize consumer
    async def stop() -> None          # Shut down consumer
    async def run() -> None           # Main loop
    async def process_message(payload: dict) -> None  # ABSTRACT
    async def handle_error(payload: dict) -> None      # Hook (optional override)
```

### Loop Behavior (`run()`)

```
start()
  │
  ▼
async for msg in consumer:
  │
  ├─ try: process_message(msg.value)
  │
  └─ except: handle_error(msg.value)
       │
       └─ (default: log warning with payload keys)
```

### Consumer Configuration

| Property | Value |
|----------|-------|
| `bootstrap_servers` | `settings.kafka_bootstrap_servers` |
| `group_id` | `settings.kafka_consumer_group` |
| `auto_offset_reset` | `"earliest"` |
| `enable_auto_commit` | `True` |
| `auto_commit_interval_ms` | `5000` |
| `value_deserializer` | `orjson.loads` |

## 3. Task Worker (`TaskProcessorWorker`)

### Responsibility

Consumes events from `c2f_incoming_tasks`, processes via LangGraph, and publishes results to `c2f_completed_tasks`.

### Flow

```
consume(c2f_incoming_tasks)
  │
  ▼ payload = TaskEvent (deserialized)
  │
  ├─ set_task_status(task_id, "processing")
  │
  ├─ run_task_graph(task_id, model, messages, ...)
  │     │
  │     ├─ validate_input → verify messages and role="user"
  │     │     │
  │     │     ├─ [VALID] → invoke_llm
  │     │     │     │
  │     │     │     ├─ [SUCCESS] → format_output → status="completed"
  │     │     │     │
  │     │     │     └─ [FAILURE] → format_output → status="failed"
  │     │     │
  │     │     └─ [INVALID] → format_output → status="failed"
  │     │
  │     └─ return TaskGraphState
  │
  ├─ [SUCCESS] set_task_status(task_id, "completed", {result, model, usage})
  │             incr_metric("tasks_completed")
  │
  ├─ [FAILURE]  set_task_status(task_id, "failed", {error})
  │             incr_metric("tasks_failed")
  │
  └─ send_event(c2f_completed_tasks, TaskResultEvent)
```

### Entry Point

```bash
python -m src.workers.task_processor
```

Initializes Redis, Kafka Producer and Consumer, then enters the consumption loop.

## 4. LangGraph (Processing Graph)

### State Schema

```python
class TaskGraphState(TypedDict):
    task_id: str
    model: str
    messages: list[dict[str, str]]
    temperature: float
    max_tokens: int | None
    llm_response: dict[str, Any] | None
    error: str | None
    status: str
```

### Graph Nodes

| Node | Function | Input | Output |
|------|----------|-------|--------|
| `validate_input` | Validate messages and role | State | `{status}` or `{error, status}` |
| `invoke_llm` | Call `call_llm()` | State | `{llm_response, status}` or `{error, status}` |
| `format_output` | Post-processing (noop) | State | `{}` |

### Conditional Routing

```python
def should_call_llm(state) -> str:
    if state.get("error"):
        return "format_output"  # Skip LLM if already failed
    return "invoke_llm"
```

### Visual Graph

```
START
  │
  ▼
[validate_input]
  │
  ├─ (no error) ──▶ [invoke_llm] ──▶ [format_output] ──▶ END
  │
  └─ (has error) ──▶ [format_output] ──▶ END
```

### Validations Performed

| Validation | Error |
|-----------|-------|
| `messages` is empty | `"No messages provided"` |
| No message with `role="user"` | `"At least one user message is required"` |

## 5. Delivery Worker (`DeliveryWorker`)

### Responsibility

Consumes events from `c2f_completed_tasks` and delivers the result via HTTP POST to Conn2Flow.

### Flow

```
consume(c2f_completed_tasks)
  │
  ▼ payload = TaskResultEvent (deserialized)
  │
  ├─ [no webhook_url] → log warning, skip
  │
  ├─ serialize payload → orjson.dumps(payload)
  │
  ├─ sign payload → HMAC-SHA256(body, secret)
  │
  └─ HTTP POST with exponential retry
       │
       ├─ attempt 1: POST webhook_url
       │     ├─ [2xx] → success, incr_metric("webhooks_delivered")
       │     └─ [non-2xx or timeout] → retry
       │
       ├─ attempt 2: delay = 2 * 2^1 = 4s
       ├─ attempt 3: delay = 2 * 2^2 = 8s
       ├─ attempt 4: delay = 2 * 2^3 = 16s
       └─ attempt 5: delay = 2 * 2^4 = 32s
             │
             └─ [TOTAL FAILURE] → set_task_status("delivery_failed")
```

### HMAC Signature

| Aspect | Value |
|--------|-------|
| **Algorithm** | HMAC-SHA256 |
| **Secret** | `C2F_WEBHOOK_SECRET` (environment variable) |
| **Input** | Serialized body (bytes) |
| **Header** | `X-C2F-Signature: sha256={hex_digest}` |

### Webhook Headers

| Header | Value |
|--------|-------|
| `Content-Type` | `application/json` |
| `X-C2F-Signature` | `sha256={hmac_hex}` |
| `X-C2F-Task-ID` | Task UUID |
| `User-Agent` | `Conn2Flow-Nexus-AI/0.1` |

### Retry Configuration

| Parameter | Value |
|-----------|-------|
| `MAX_RETRIES` | 5 |
| `RETRY_BASE_DELAY` | 2 seconds |
| **Formula** | `base_delay * 2^(attempt-1)` |
| **Delays** | 2s, 4s, 8s, 16s, 32s |
| `httpx timeout` | 30 seconds |

### Entry Point

```bash
python -m src.workers.delivery_worker
```

## 6. Worker Lifecycle

```
main()
  │
  ├─ logging.basicConfig(...)
  │
  ├─ start_redis()
  ├─ start_producer()       # Task Worker needs to publish results
  │
  ├─ worker = XxxWorker(topic=..., settings=...)
  │
  ├─ try: worker.run()      # Infinite consumption loop
  │
  └─ finally:
       ├─ stop_producer()
       └─ stop_redis()
```
