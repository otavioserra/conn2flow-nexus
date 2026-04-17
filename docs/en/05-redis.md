# 5. Redis — Cache and State Management

## What Is Redis?

**Redis** (Remote Dictionary Server) is an **in-memory** database that works as:
- **Key-Value Store** — stores data as key/value pairs
- **Cache** — temporary, fast-access data
- **Message Broker** — pub/sub (not used here, we use Kafka)
- **Counter** — atomic increment operations

### Why Redis in This Project?

| Use | Reason |
|-----|--------|
| **Task status** | Query `GET /status/{task_id}` without going to Kafka |
| **Metrics** | Atomic counters (tasks processed, webhooks delivered) |
| **Health check** | Verify Redis is active |

Redis is **extremely fast** (~100k operations/second) because it keeps everything in RAM.

---

## Fundamental Concepts

### Key-Value Store

```
Key                                Value (JSON in bytes)
─────────────────────────────────  ──────────────────────────────
c2f:task:abc-123                   {"status": "completed", "result": {...}}
c2f:task:def-456                   {"status": "processing", "model": "gpt-4o"}
c2f:metrics:tasks_completed        42
c2f:metrics:webhooks_failed        3
```

### TTL (Time To Live)

```python
DEFAULT_TTL = 60 * 60 * 24  # 24 hours in seconds
await r.set(key, value, ex=ttl)  # "ex" = expire in seconds
```

- Each key can have an **expiration time**
- After the TTL, Redis **automatically removes** the key
- Prevents Redis from growing infinitely
- In the project: task statuses expire in 24h

### Serialization with orjson

```python
# Saving:
value = orjson.dumps({"status": status, **(data or {})})
await r.set(f"{PREFIX_TASK}{task_id}", value, ex=ttl)

# Reading:
raw = await r.get(f"{PREFIX_TASK}{task_id}")
return orjson.loads(raw)  # bytes → dict
```

- Redis stores **raw bytes** — it has no "JSON" type
- We use `orjson.dumps()` to convert dict → bytes
- We use `orjson.loads()` to convert bytes → dict

---

## Implementation: `src/core/redis_client.py`

### Async Singleton

```python
import redis.asyncio as aioredis

_redis: aioredis.Redis | None = None

async def start_redis() -> aioredis.Redis:
    global _redis
    _redis = aioredis.from_url(
        settings.redis_url,
        decode_responses=False,    # Works with raw bytes
        max_connections=20,        # Pool of 20 connections
    )
    await _redis.ping()  # Tests connection immediately
```

**Concept: Connection Pool**
- `max_connections=20` creates a **connection pool**
- Instead of opening/closing a connection per operation, reuses existing connections
- Multiple coroutines can use Redis simultaneously without conflict

**Concept: `decode_responses=False`**
- By default, `redis-py` can decode bytes → string automatically
- We disable it because we use `orjson` for serialization/deserialization (faster)

### Status Operations

```python
# Prefixes organize keys by category
PREFIX_TASK = "c2f:task:"
PREFIX_METRICS = "c2f:metrics:"

async def set_task_status(task_id: str, status: str, data: dict | None = None):
    r = get_redis()
    value = orjson.dumps({"status": status, **(data or {})})
    await r.set(f"{PREFIX_TASK}{task_id}", value, ex=DEFAULT_TTL)
```

**Concept: Key Naming Convention**
- `c2f:task:abc-123` → namespace:type:identifier
- `:` is a Redis convention for organizing keys hierarchically
- Tools like RedisInsight group keys by namespace

**Concept: `**(data or {})`**
- Spread operator (`**`) "spreads" the dict into another dict
- `data or {}` prevents errors if `data` is `None`

### Atomic Counters

```python
async def incr_metric(name: str, amount: int = 1) -> int:
    r = get_redis()
    return await r.incrby(f"{PREFIX_METRICS}{name}", amount)
```

**Concept: Atomic Operation**
- `INCRBY` is an **atomic** operation in Redis
- Even if 10 workers increment simultaneously, the final value will be correct
- There is no race condition — Redis is single-threaded for commands

### Health Check

```python
# In health.py:
r = get_redis()
await r.ping()  # Returns True if Redis is active
```

---

## Docker Configuration

```yaml
redis:
  image: redis:7-alpine          # Lightweight image (Alpine Linux)
  command: >
    redis-server
    --appendonly yes               # Persists data to disk (AOF)
    --maxmemory 256mb             # Memory limit
    --maxmemory-policy allkeys-lru # Removes least used keys when full
  volumes:
    - redis_data:/data             # Persists across restarts
```

**Concept: `appendonly yes` (AOF - Append Only File)**
- Redis is in-memory, but `appendonly yes` saves each operation to disk
- If the container restarts, data is recovered
- Trade-off: slightly slower, but doesn't lose data

**Concept: `maxmemory-policy allkeys-lru`**
- LRU = Least Recently Used
- When Redis reaches 256MB, it automatically removes the **least accessed** keys
- Perfect for cache and temporary statuses

---

## Flow in the Project

```
1. POST /submit
   └── set_task_status(task_id, "queued")          ← Redis SET

2. TaskProcessorWorker starts
   └── set_task_status(task_id, "processing")      ← Redis SET

3. LLM responds
   ├── set_task_status(task_id, "completed", {...}) ← Redis SET
   └── incr_metric("tasks_completed")               ← Redis INCRBY

4. GET /status/{task_id}
   └── get_task_status(task_id)                     ← Redis GET

5. Webhook fails
   ├── set_task_status(task_id, "delivery_failed")  ← Redis SET
   └── incr_metric("webhooks_failed")               ← Redis INCRBY
```

---

## Previous: [← Kafka](04-kafka.md) | Next: [LiteLLM →](06-litellm.md)
