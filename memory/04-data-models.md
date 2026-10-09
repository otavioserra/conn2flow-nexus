# SPEC-04: Data Models

> **Status**: ✅ Approved
> **Version**: 1.0.0
> **Created**: 2025-07-16
> **Last updated**: 2025-07-16

---

## 1. Pydantic Models (Data Validation)

### 1.1. Request Models

#### TaskRequest

**File**: `src/api/schemas/requests.py`

```python
class TaskRequest(BaseModel):
    model: str = "gpt-4o-mini"
    messages: list[dict[str, str]]   # min_length=1
    temperature: float = 0.7         # 0.0 ≤ x ≤ 2.0
    max_tokens: int | None = None    # 0 < x ≤ 128000
    webhook_url: str | None = None
    metadata: dict[str, Any] = {}
    stream: bool = False
```

**Invariants**:
- `messages` must have at least 1 item
- `temperature` must be between 0.0 and 2.0 (inclusive)
- `max_tokens`, if present, must be > 0 and ≤ 128000
- `model` accepts any string (actual validation done by LiteLLM)

### 1.2. Response Models

#### TaskAcceptedResponse

**File**: `src/api/schemas/responses.py`

```python
class TaskAcceptedResponse(BaseModel):
    task_id: str        # UUID v4
    status: str         # Always "queued"
    message: str        # "Task accepted for async processing"
```

#### TaskStatusResponse

**File**: `src/api/schemas/responses.py`

```python
class TaskStatusResponse(BaseModel):
    task_id: str
    status: str                           # queued | processing | completed | failed
    result: dict[str, Any] | None = None  # Present when completed
    error: str | None = None              # Present when failed
    metadata: dict[str, Any] = {}
```

### 1.3. Event Models

#### TaskEvent

**File**: `src/models/events.py`

```python
class TaskEvent(BaseModel):
    task_id: str
    model: str
    messages: list[dict[str, str]]
    temperature: float = 0.7
    max_tokens: int | None = None
    webhook_url: str | None = None
    metadata: dict[str, Any] = {}
    stream: bool = False
    created_at: datetime  # Auto: UTC now
```

#### TaskResultEvent

**File**: `src/models/events.py`

```python
class TaskResultEvent(BaseModel):
    task_id: str
    status: str                          # completed | failed
    model: str
    result: dict[str, Any] | None = None
    error: str | None = None
    webhook_url: str | None = None
    metadata: dict[str, Any] = {}
    usage: dict[str, int] | None = None  # {prompt_tokens, completion_tokens, total_tokens}
    completed_at: datetime               # Auto: UTC now
```

## 2. LangGraph State

### TaskGraphState

**File**: `src/graphs/base_graph.py`

```python
class TaskGraphState(TypedDict):
    task_id: str
    model: str
    messages: list[dict[str, str]]
    temperature: float
    max_tokens: int | None
    llm_response: dict[str, Any] | None  # Populated by invoke_llm node
    error: str | None                     # Populated on failure
    status: str                           # processing | completed | failed
```

**Invariants**:
- `task_id` is immutable after creation
- `error` and `llm_response` are mutually exclusive (only one is populated)
- `status` follows the state machine: `processing → completed | failed`

## 3. Redis Data Structures

### 3.1. Task Status

**Key pattern**: `c2f:task:{task_id}`
**TTL**: 24 hours (86400 seconds)
**Type**: STRING (JSON serialized with orjson)

#### When `queued`:

```json
{
  "status": "queued",
  "model": "gpt-4o-mini"
}
```

#### When `processing`:

```json
{
  "status": "processing",
  "model": "gpt-4o-mini"
}
```

#### When `completed`:

```json
{
  "status": "completed",
  "result": {
    "content": "LLM response..."
  },
  "model": "gpt-4o-mini",
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 10,
    "total_tokens": 35
  }
}
```

#### When `failed`:

```json
{
  "status": "failed",
  "error": "LLM error: AuthenticationError: Invalid API key"
}
```

### 3.2. Metrics (Counters)

**Key pattern**: `c2f:metrics:{name}`
**Type**: STRING (atomically incremented via INCRBY)
**TTL**: No expiration

| Key | Description |
|-----|-------------|
| `c2f:metrics:tasks_completed` | Total successfully completed tasks |
| `c2f:metrics:tasks_failed` | Total failed tasks |
| `c2f:metrics:webhooks_delivered` | Total successfully delivered webhooks |

## 4. LLM Response (internal)

Return from `call_llm()` function in `src/core/llm_router.py`:

```python
{
    "content": str,           # LLM response content
    "model_used": str,        # Model that actually responded
    "usage": {
        "prompt_tokens": int,
        "completion_tokens": int,
        "total_tokens": int,
    },
    "finish_reason": str,     # "stop" | "length" | "content_filter"
}
```

## 5. Relacionamento entre Models

```
TaskRequest (HTTP input)
    │
    ▼ (API cria TaskEvent)
TaskEvent (Kafka message)
    │
    ▼ (Worker cria TaskGraphState)
TaskGraphState (LangGraph state)
    │
    ▼ (Worker cria TaskResultEvent)
TaskResultEvent (Kafka message)
    │
    ▼ (Delivery Worker envia via webhook)
HTTP POST body (JSON = TaskResultEvent serializado)
```

```
Redis (paralelo a todo o fluxo):
  TaskRequest → set("queued")
  TaskEvent consumed → set("processing")
  LLM response → set("completed") ou set("failed")
  
  GET /status/{id} → get() → TaskStatusResponse
```
