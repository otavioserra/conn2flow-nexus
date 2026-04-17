# 8. Workers — Async Processing

## Concept: Worker Pattern

**Workers** are independent processes that run in separate containers. In our project:

| Worker | Consumes From | Produces To | Function |
|--------|--------------|-------------|----------|
| `TaskProcessorWorker` | `c2f_incoming_tasks` | `c2f_completed_tasks` | Runs LangGraph + LiteLLM |
| `DeliveryWorker` | `c2f_completed_tasks` | — | Sends webhook to Conn2Flow |

### Why Separate Processes?

1. **Fault isolation** — if the LLM worker crashes, the API continues receiving tasks
2. **Independent scaling** — we can have 1 API and 10 LLM workers
3. **Dedicated resources** — LLM workers use more memory than the API
4. **Granular restart** — restarting one worker doesn't affect the others

---

## Task Processor Worker: `src/workers/task_processor.py`

### BaseKafkaConsumer Inheritance

```python
class TaskProcessorWorker(BaseKafkaConsumer):
    async def process_message(self, payload: dict[str, Any]) -> None:
        task_id = payload.get("task_id", "unknown")
        model = payload.get("model", self.settings.default_model)
        messages = payload.get("messages", [])
```

**Concept: Template Method Pattern**
- `BaseKafkaConsumer.run()` defines the **algorithm**: connect → loop → process → handle error
- `process_message()` is the **customizable step** — each worker implements its logic
- The loop, retry, and shutdown are inherited — zero duplication

### Processing Flow

```python
# 1. Update status to "processing"
await set_task_status(task_id, "processing", {"model": model})

# 2. Execute the LangGraph pipeline
result_state = await run_task_graph(
    task_id=task_id,
    model=model,
    messages=messages,
    temperature=temperature,
    max_tokens=max_tokens,
)

# 3. Build the result event
if result_state.get("error"):
    result_event = TaskResultEvent(
        task_id=task_id,
        status="failed",
        error=result_state["error"],
        ...
    )
    await set_task_status(task_id, "failed", {"error": ...})
    await incr_metric("tasks_failed")
else:
    result_event = TaskResultEvent(
        task_id=task_id,
        status="completed",
        result={"content": llm_response.get("content", "")},
        usage=llm_response.get("usage"),
        ...
    )
    await set_task_status(task_id, "completed", {...})
    await incr_metric("tasks_completed")

# 4. Publish result to Kafka
await send_event(
    topic=self.settings.kafka_topic_completed,
    value=result_event,
    key=task_id,
)
```

### Worker Entry Point

```python
async def main() -> None:
    settings = get_settings()
    logging.basicConfig(...)

    await start_redis()
    await start_producer()

    worker = TaskProcessorWorker(
        topic=settings.kafka_topic_incoming,
        settings=settings,
    )

    try:
        await worker.run()  # ← Infinite loop
    finally:
        await stop_producer()
        await stop_redis()

if __name__ == "__main__":
    asyncio.run(main())
```

**Concept: `asyncio.run()`**
- Creates an event loop, runs the `main()` coroutine, and closes the loop when done
- It's the entry point for async Python code
- Equivalent to `new Promise().then()` in JavaScript

**Concept: `if __name__ == "__main__"`**
- Runs **only** when the file is executed directly
- Does not run when imported by another module
- In Docker: `command: ["python", "-m", "src.workers.task_processor"]`

---

## Delivery Worker: `src/workers/delivery_worker.py`

### HMAC-SHA256 — Webhook Signing

```python
import hmac
import hashlib

def _sign_payload(payload_bytes: bytes, secret: str) -> str:
    return hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()
```

**Concept: HMAC (Hash-based Message Authentication Code)**
- HMAC ensures the message **was not altered** and **came from who it claims**
- The sender (Nexus AI) and recipient (Conn2Flow) share a **secret**
- The sender calculates: `HMAC(payload, secret)` → signature
- The recipient recalculates and compares — if different, the message was tampered with

**How it works:**
```
Payload: {"task_id": "abc", "result": "Hello"}
Secret: "my-secret-key"
HMAC-SHA256 → "a1b2c3d4e5f6..." (64 hex characters)
```

**Webhook headers:**
```python
headers = {
    "Content-Type": "application/json",
    "X-C2F-Signature": f"sha256={signature}",   # HMAC signature
    "X-C2F-Task-ID": task_id,                   # Task ID
    "User-Agent": "Conn2Flow-Nexus-AI/0.1",     # Identifies the sender
}
```

### Retry with Exponential Backoff

```python
MAX_RETRIES = 5
RETRY_BASE_DELAY = 2  # seconds

for attempt in range(1, MAX_RETRIES + 1):
    try:
        response = await client.post(webhook_url, content=body_bytes, headers=headers)
        if response.status_code < 300:
            delivered = True
            break
    except httpx.TimeoutException:
        ...
    except httpx.RequestError as exc:
        ...

    # Exponential backoff: 2s, 4s, 8s, 16s, 32s
    if attempt < MAX_RETRIES:
        delay = RETRY_BASE_DELAY ** attempt
        await asyncio.sleep(delay)
```

**Concept: Exponential Backoff**
- Instead of retrying immediately, waits longer between each attempt
- Attempt 1: wait 2¹ = 2s
- Attempt 2: wait 2² = 4s
- Attempt 3: wait 2³ = 8s
- Attempt 4: wait 2⁴ = 16s
- Attempt 5: definitive failure

**Why exponential backoff?**
- If the destination server is overloaded, immediate retry **worsens** the problem
- Waiting longer each time gives the server time to recover
- It's the industry standard for network call retries

### httpx — Async HTTP Client

```python
async with httpx.AsyncClient(timeout=30) as client:
    response = await client.post(
        webhook_url,
        content=body_bytes,
        headers=headers,
    )
```

**Concept: `async with` (Async Context Manager)**
- `async with httpx.AsyncClient()` ensures the client is **closed** at the end
- Even in case of exceptions, network resources are released
- `content=body_bytes` sends raw bytes (already serialized with orjson)

---

## How Workers Run in Docker

```yaml
# docker-compose.yml:
worker-task:
  command: ["python", "-m", "src.workers.task_processor"]
  depends_on:
    kafka: { condition: service_healthy }
    redis: { condition: service_healthy }

worker-delivery:
  command: ["python", "-m", "src.workers.delivery_worker"]
  depends_on:
    kafka: { condition: service_healthy }
    redis: { condition: service_healthy }
```

- Each worker is a **separate container** using the same Docker image
- `command` overrides the Dockerfile's `CMD` (which runs uvicorn by default)
- `depends_on + condition: service_healthy` ensures Kafka and Redis are ready

---

## Previous: [← LangGraph](07-langgraph.md) | Next: [Docker →](09-docker.md)
