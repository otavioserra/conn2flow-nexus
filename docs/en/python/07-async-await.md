# 07. Async/Await & Concurrency

## The Big Picture — Why Async?

In PHP (traditional), every request is handled by a separate process/thread. If you need to wait for a database query, the whole thread blocks. With Apache + mod_php, you spin up more processes to handle concurrent requests.

Python's `asyncio` is fundamentally different: **one thread handles thousands of concurrent operations** by cooperatively switching between them whenever one is waiting (I/O bound).

```
PHP (Apache + mod_php):
Request 1 → Thread 1 → [DB query... waiting...] → Response 1
Request 2 → Thread 2 → [DB query... waiting...] → Response 2
Request 3 → Thread 3 → [DB query... waiting...] → Response 3
(3 threads, each blocked)

Python (asyncio / uvicorn):
Request 1 → [DB query → yield control]
Request 2 → [DB query → yield control]
Request 3 → [DB query → yield control]
[DB 1 ready] → Response 1
[DB 3 ready] → Response 3
[DB 2 ready] → Response 2
(1 thread, no blocking!)
```

---

## Coroutines — The Building Block

### PHP (no native equivalent until Fibers in 8.1)
```php
// PHP 8.1 Fibers (low-level, rarely used directly)
$fiber = new Fiber(function (): void {
    $value = Fiber::suspend('pause');
    echo "Resumed with: $value";
});
```

### Python
```python
import asyncio

# A coroutine function (async def)
async def fetch_data() -> str:
    print("Starting fetch...")
    await asyncio.sleep(1)  # Simulates I/O wait (non-blocking)
    print("Fetch complete!")
    return "data"

# Running a coroutine
async def main():
    result = await fetch_data()
    print(result)

# Entry point
asyncio.run(main())
```

### Key Concepts:

| Concept | What It Does |
|---------|-------------|
| `async def` | Declares a coroutine function (returns a coroutine object) |
| `await` | Pauses the coroutine until the awaited operation completes |
| `asyncio.run()` | Creates an event loop and runs the top-level coroutine |
| Event loop | The scheduler that manages all coroutines |

**Critical rule:** You can only use `await` inside an `async def` function.

---

## Event Loop — How It Works

```
┌──────────────────────────────────────────┐
│              Event Loop                   │
│                                           │
│  1. Pick ready coroutine                  │
│  2. Run it until it hits `await`          │
│  3. Suspend it, save state                │
│  4. Pick next ready coroutine             │
│  5. Repeat                                │
│                                           │
│  When I/O completes → mark coroutine      │
│  as ready → it gets picked up again       │
└──────────────────────────────────────────┘
```

The event loop is like a **single-threaded Apache** that never blocks — when one request waits for the database, it handles another request instead of sitting idle.

---

## Real Code from Our Project

### `src/main.py` — Lifespan
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application startup and shutdown lifecycle."""
    settings = get_settings()

    # --- Startup ---
    await start_redis()    # Async: connect to Redis
    await start_producer() # Async: connect to Kafka

    yield  # App is running, handling requests

    # --- Shutdown ---
    await stop_producer()
    await stop_redis()
```

### `src/core/redis_client.py` — Async Redis
```python
async def start_redis() -> aioredis.Redis:
    global _redis
    if _redis is not None:
        return _redis

    settings = get_settings()
    _redis = aioredis.from_url(
        settings.redis_url,
        decode_responses=False,
        max_connections=20,
    )
    await _redis.ping()  # Async ping — doesn't block!
    return _redis

async def set_task_status(task_id: str, status: str, data: dict | None = None) -> None:
    r = get_redis()
    value = orjson.dumps({"status": status, **(data or {})})
    await r.set(f"{PREFIX_TASK}{task_id}", value, ex=ttl)  # Async SET
```

### `src/core/kafka_producer.py` — Async Kafka
```python
async def start_producer() -> AIOKafkaProducer:
    global _producer
    _producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        acks="all",
        enable_idempotence=True,
    )
    await _producer.start()  # Async connect
    return _producer

async def send_event(topic: str, value: Any, key: str | None = None) -> None:
    metadata = await _producer.send_and_wait(topic, value=value, key=key)
    # send_and_wait is async — yields control while Kafka processes
```

### `src/api/endpoints/tasks.py` — Async Endpoint
```python
@router.post("/submit", status_code=status.HTTP_202_ACCEPTED)
async def submit_task(
    payload: TaskRequest,
    settings: Settings = Depends(verify_api_key),
):
    task_id = str(uuid.uuid4())
    event = TaskEvent(task_id=task_id, ...)

    await set_task_status(task_id, "queued", {"model": payload.model})  # Redis
    await send_event(topic=settings.kafka_topic_incoming, value=event)  # Kafka

    return TaskAcceptedResponse(task_id=task_id, status="queued")
```

### `src/core/kafka_consumer.py` — Async Consumer Loop
```python
async def run(self) -> None:
    """Main loop: consumes messages and delegates."""
    await self.start()
    try:
        async for msg in self._consumer:  # async for — iterates asynchronously!
            try:
                await self.process_message(msg.value)
            except Exception:
                await self.handle_error(msg.value)
    except asyncio.CancelledError:
        logger.info("Consumer cancelled")
    finally:
        await self.stop()
```

### `src/workers/delivery_worker.py` — Async HTTP with Retry
```python
async with httpx.AsyncClient(timeout=30) as client:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = await client.post(webhook_url, content=body_bytes, headers=headers)
            if response.status_code < 300:
                delivered = True
                break
        except httpx.TimeoutException:
            last_error = "Timeout"

        if attempt < MAX_RETRIES:
            delay = RETRY_BASE_DELAY ** attempt
            await asyncio.sleep(delay)  # Non-blocking sleep!
```

---

## Concurrent Execution — `asyncio.gather()`

Run multiple coroutines **concurrently** (not in parallel — still one thread):

```python
import asyncio

async def fetch_user(user_id: int) -> dict:
    await asyncio.sleep(1)  # Simulates API call
    return {"id": user_id, "name": f"User {user_id}"}

async def fetch_orders(user_id: int) -> list:
    await asyncio.sleep(1.5)  # Simulates API call
    return [{"order_id": 1, "user_id": user_id}]

async def main():
    # Sequential: 2.5 seconds total
    user = await fetch_user(1)
    orders = await fetch_orders(1)

    # Concurrent: ~1.5 seconds total (max of the two)
    user, orders = await asyncio.gather(
        fetch_user(1),
        fetch_orders(1),
    )

asyncio.run(main())
```

### `asyncio.gather()` with error handling:
```python
results = await asyncio.gather(
    fetch_user(1),
    fetch_orders(1),
    return_exceptions=True,  # Don't raise — return exceptions in results
)

for result in results:
    if isinstance(result, Exception):
        print(f"Failed: {result}")
    else:
        print(f"Success: {result}")
```

---

## `async for` — Async Iteration

```python
# Regular iteration
for item in items:
    process(item)

# Async iteration (the iterator can await between items)
async for msg in self._consumer:
    await self.process_message(msg.value)
```

From our Kafka consumer: `async for msg in self._consumer` — the consumer **waits** for the next message from Kafka. While waiting, the event loop can do other things.

### How to create an async iterator:
```python
class AsyncRange:
    def __init__(self, n: int):
        self.n = n
        self.current = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.current >= self.n:
            raise StopAsyncIteration
        await asyncio.sleep(0.1)  # Simulate async work
        value = self.current
        self.current += 1
        return value

async def main():
    async for i in AsyncRange(5):
        print(i)
```

---

## `async with` — Async Context Managers

```python
# Synchronous context manager
with open("file.txt") as f:
    data = f.read()

# Async context manager
async with httpx.AsyncClient(timeout=30) as client:
    response = await client.get("https://api.example.com")
```

From our codebase:
```python
# src/workers/delivery_worker.py
async with httpx.AsyncClient(timeout=30) as client:
    # client is created (async setup)
    response = await client.post(webhook_url, ...)
    # When exiting: client connections are closed (async cleanup)
```

---

## `asyncio.sleep()` vs `time.sleep()`

```python
import asyncio
import time

# ❌ BLOCKS the entire event loop!
time.sleep(5)

# ✅ Non-blocking — other coroutines can run during this wait
await asyncio.sleep(5)
```

**Critical rule:** Never use `time.sleep()` in async code! It blocks the entire thread, freezing all coroutines.

From our codebase — exponential backoff:
```python
# src/workers/delivery_worker.py
if attempt < MAX_RETRIES:
    delay = RETRY_BASE_DELAY ** attempt  # 2, 4, 8, 16, 32 seconds
    await asyncio.sleep(delay)  # ✅ Non-blocking wait
```

---

## `asyncio.run()` — Entry Point

```python
# src/workers/task_processor.py
async def main() -> None:
    """Worker entry point."""
    await start_redis()
    await start_producer()
    worker = TaskProcessorWorker(topic=settings.kafka_topic_incoming)
    try:
        await worker.run()
    finally:
        await stop_producer()
        await stop_redis()

if __name__ == "__main__":
    asyncio.run(main())  # Creates event loop + runs main()
```

`asyncio.run()` is the **bridge** between sync and async worlds:
1. Creates a new event loop
2. Runs the coroutine to completion
3. Closes the loop

You only call it **once** at the top level. Inside async code, just `await`.

---

## Tasks — Fire and Forget

```python
async def background_task(name: str):
    await asyncio.sleep(5)
    print(f"{name} completed")

async def main():
    # Create a task that runs in the background
    task = asyncio.create_task(background_task("cleanup"))

    # Do other work while task runs
    await asyncio.sleep(1)
    print("Doing other work...")

    # Wait for the task if needed
    await task
```

---

## Common Pitfalls for PHP Developers

### 1. Forgetting `await`
```python
# ❌ BUG: This doesn't wait for completion!
async def save_data():
    set_task_status(task_id, "completed")  # Missing await!
    # Returns a coroutine object, doesn't execute

# ✅ Correct
async def save_data():
    await set_task_status(task_id, "completed")
```

### 2. Using blocking I/O in async code
```python
# ❌ Blocks the event loop!
import requests  # Synchronous library!
response = requests.get("https://api.example.com")

# ✅ Use async library
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get("https://api.example.com")
```

### 3. Not understanding concurrency vs parallelism
```
Concurrency (asyncio):    One chef, multiple dishes cooking simultaneously
                          Chef stirs soup → checks oven → flips pancake
                          (context switching, single thread)

Parallelism (multiprocessing): Multiple chefs, each cooking a dish
                               (true simultaneous execution, multiple CPUs)
```

`asyncio` is perfect for **I/O-bound** work (network, disk, database). For **CPU-bound** work (image processing, heavy computation), use `multiprocessing` or `concurrent.futures`.

---

## PHP Async Comparison

| Feature | PHP | Python |
|---------|-----|--------|
| Async model | ReactPHP/Swoole/Fibers | asyncio (built-in) |
| Web server | Apache/nginx + PHP-FPM | uvicorn (ASGI) |
| Async HTTP | Guzzle promises | httpx / aiohttp |
| Async DB | (limited) | asyncpg, aiomysql |
| Async Redis | Predis async | redis.asyncio |
| Async Kafka | (none native) | aiokafka |
| Framework | Laravel Octane | FastAPI |

Python's async ecosystem is **much more mature** than PHP's. Almost every library has an async version.

---

## Previous: [← Modules & Packages](06-modules-packages.md) | Next: [Context Managers →](08-context-managers.md)
