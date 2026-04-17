# SPEC-03: Event Schemas (Kafka)

> **Status**: ✅ Approved
> **Version**: 1.0.0
> **Created**: 2025-07-16
> **Last updated**: 2025-07-16

---

## 1. Kafka Topics

| Topic | Partitions | Producer | Consumer |
|-------|-----------|----------|----------|
| `c2f_incoming_tasks` | 3 | API (`c2f-api`) | Task Worker (`c2f-worker-task`) |
| `c2f_completed_tasks` | 3 | Task Worker | Delivery Worker (`c2f-worker-delivery`) |

### Topic Configuration

| Property | Value |
|----------|-------|
| **Replication factor** | 1 (single node) |
| **Retention** | 168 hours (7 days) |
| **Auto-create** | Enabled |
| **Cleanup policy** | delete |
| **Consumer group** | `c2f-workers` |
| **Offset reset** | `earliest` |
| **Auto-commit** | Enabled (interval: 5s) |

## 2. Event Schemas

### 2.1. TaskEvent (`c2f_incoming_tasks`)

Published by the API when a new task is submitted.

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "model": "gpt-4o-mini",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": null,
  "webhook_url": "http://example.com/webhook",
  "metadata": {"source": "chat", "user_id": "123"},
  "stream": false,
  "created_at": "2025-07-16T10:30:00Z"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `task_id` | `string` (UUID) | Yes | Unique task identifier |
| `model` | `string` | Yes | LLM model to use |
| `messages` | `array[{role, content}]` | Yes | Messages in OpenAI format |
| `temperature` | `float` | No | Default: `0.7` |
| `max_tokens` | `int \| null` | No | Default: `null` |
| `webhook_url` | `string \| null` | No | URL for result delivery |
| `metadata` | `object` | No | Default: `{}` |
| `stream` | `boolean` | No | Default: `false` |
| `created_at` | `string` (ISO 8601) | Auto | UTC creation timestamp |

### 2.2. TaskResultEvent (`c2f_completed_tasks`)

Published by the Task Worker when a task is processed.

**Success Case**:

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "model": "gpt-4o-mini",
  "result": {
    "content": "Hello! How can I help you today?"
  },
  "error": null,
  "webhook_url": "http://example.com/webhook",
  "metadata": {"source": "chat", "user_id": "123"},
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 10,
    "total_tokens": 35
  },
  "completed_at": "2025-07-16T10:30:05Z"
}
```

**Failure Case**:

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "model": "gpt-4o-mini",
  "result": null,
  "error": "LLM error: AuthenticationError: Invalid API key",
  "webhook_url": "http://example.com/webhook",
  "metadata": {"source": "chat", "user_id": "123"},
  "usage": null,
  "completed_at": "2025-07-16T10:30:02Z"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `task_id` | `string` (UUID) | Yes | Task identifier |
| `status` | `string` | Yes | `"completed"` or `"failed"` |
| `model` | `string` | Yes | Model actually used |
| `result` | `object \| null` | No | LLM response content |
| `error` | `string \| null` | No | Error message |
| `webhook_url` | `string \| null` | No | Delivery URL |
| `metadata` | `object` | No | Preserved metadata |
| `usage` | `object \| null` | No | Token count |
| `completed_at` | `string` (ISO 8601) | Auto | UTC completion timestamp |

### Usage Schema (sub-object)

```json
{
  "prompt_tokens": 25,
  "completion_tokens": 10,
  "total_tokens": 35
}
```

## 3. Serialization

| Aspect | Specification |
|--------|---------------|
| **Format** | JSON |
| **Library** | `orjson` (high performance) |
| **Key serializer** | UTF-8 string |
| **Value serializer** | `orjson.dumps()` via Pydantic `.model_dump(mode="json")` |
| **Value deserializer** | `orjson.loads()` |
| **Partition key** | `task_id` (ensures ordering per task) |

## 4. Producer Configuration

| Property | Value | Rationale |
|----------|-------|-----------|
| `acks` | `"all"` | Durability guarantee |
| `enable_idempotence` | `True` | Prevents duplicates |
| `retry_backoff_ms` | `100` | Backoff between retries |
| `request_timeout_ms` | `30000` | 30s timeout per request |

## 5. Consumer Configuration

| Property | Value | Rationale |
|----------|-------|-----------|
| `group_id` | `"c2f-workers"` | Shared consumer group |
| `auto_offset_reset` | `"earliest"` | Process messages from the beginning |
| `enable_auto_commit` | `True` | Automatic offset commit |
| `auto_commit_interval_ms` | `5000` | Commit every 5 seconds |

## 6. Event Flow

```
[API]
  │
  │ TaskEvent {task_id, model, messages, ...}
  ▼
[c2f_incoming_tasks] ─── partition based on task_id
  │
  │ consume (BaseKafkaConsumer)
  ▼
[Task Worker]
  │ process (LangGraph → LiteLLM)
  │
  │ TaskResultEvent {task_id, status, result/error, ...}
  ▼
[c2f_completed_tasks] ─── partition based on task_id
  │
  │ consume (BaseKafkaConsumer)
  ▼
[Delivery Worker]
  │ deliver via HTTP POST + HMAC
  ▼
[Conn2Flow PHP]
```
