# SPEC-02: API Contract

> **Status**: ✅ Approved
> **Version**: 1.0.0
> **Created**: 2025-07-16
> **Last updated**: 2025-07-16

---

## 1. Base URL

```
{protocol}://{host}:{port}/api/v1
```

- **Development**: `http://localhost:8000/api/v1`
- **Docker**: `http://c2f-api:8000/api/v1`

## 2. Authentication

| Environment | Method | Header |
|-------------|--------|--------|
| development | Optional | `X-C2F-API-Key` |
| production | Required | `X-C2F-API-Key` |

```http
X-C2F-API-Key: {value_configured_in_C2F_API_KEY}
```

When invalid or missing in production: **401 Unauthorized**.

## 3. Endpoints

### 3.1. Health Check

```
GET /api/v1/health
```

**Authentication**: None

**Response 200**:

```json
{
  "status": "healthy | degraded",
  "service": "conn2flow-nexus-ai",
  "version": "0.1.0",
  "environment": "development",
  "dependencies": {
    "redis": "up | down",
    "kafka": "up"
  }
}
```

**Rules**:
- `status` = `"healthy"` when Redis responds to PING
- `status` = `"degraded"` when Redis is down
- Kafka is considered "up" if the producer was initialized

---

### 3.2. Submit Task

```
POST /api/v1/tasks/submit
```

**Authentication**: `X-C2F-API-Key` (required in production)

**Request Body**:

```json
{
  "model": "gpt-4o-mini",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello, how can you help me?"}
  ],
  "temperature": 0.7,
  "max_tokens": null,
  "webhook_url": null,
  "metadata": {},
  "stream": false
}
```

| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| `model` | `string` | No | `"gpt-4o-mini"` | Any string |
| `messages` | `array[{role, content}]` | **Yes** | — | `min_length=1` |
| `temperature` | `float` | No | `0.7` | `0.0 ≤ x ≤ 2.0` |
| `max_tokens` | `int \| null` | No | `null` | `0 < x ≤ 128000` |
| `webhook_url` | `string \| null` | No | `null` | Valid URL |
| `metadata` | `object` | No | `{}` | Free-form dictionary |
| `stream` | `boolean` | No | `false` | — |

**Response 202 Accepted**:

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Task accepted for async processing"
}
```

**Response 401 Unauthorized** (production, no API key):

```json
{
  "detail": "Invalid or missing API key"
}
```

**Response 422 Unprocessable Entity** (validation failure):

```json
{
  "detail": [
    {
      "loc": ["body", "messages"],
      "msg": "Field required",
      "type": "missing"
    }
  ]
}
```

**Behavior**:

1. Generates `task_id` (UUID v4)
2. Creates `TaskEvent` (Pydantic model)
3. Saves status `"queued"` to Redis with 24h TTL
4. Publishes event to Kafka topic `c2f_incoming_tasks`
5. Returns HTTP 202 with `task_id`

---

### 3.3. Task Status

```
GET /api/v1/tasks/status/{task_id}
```

**Authentication**: `X-C2F-API-Key` (required in production)

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | `string` | Task UUID |

**Response 200**:

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued | processing | completed | failed",
  "result": {
    "content": "LLM response..."
  },
  "error": null,
  "metadata": {}
}
```

| Field | Type | When present |
|-------|------|--------------|
| `task_id` | `string` | Always |
| `status` | `string` | Always |
| `result` | `object \| null` | When `status = "completed"` |
| `error` | `string \| null` | When `status = "failed"` |
| `metadata` | `object` | Always (may be empty) |

**Response 404 Not Found**:

```json
{
  "detail": "Task {task_id} not found"
}
```

## 4. Status Codes Used

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Health check, task status |
| 202 | Accepted | Task submitted successfully |
| 401 | Unauthorized | Invalid/missing API key (production) |
| 404 | Not Found | Task not found in Redis |
| 422 | Unprocessable Entity | Pydantic validation failed |

## 5. CORS

| Environment | `allow_origins` | `allow_methods` | `allow_headers` |
|-------------|-----------------|-----------------|-----------------|
| development | `["*"]` | `["*"]` | `["*"]` |
| production | `[]` (blocked) | `["*"]` | `["*"]` |

## 6. Swagger / OpenAPI

| Ambiente | `/docs` | `/redoc` |
|----------|---------|----------|
| development | ✅ Habilitado | ✅ Habilitado |
| production | ❌ Desabilitado | ❌ Desabilitado |

## 7. Ciclo de Vida de uma Task

```
┌─────────┐     ┌────────────┐     ┌───────────┐     ┌──────────┐
│ queued   │────▶│ processing │────▶│ completed │     │ failed   │
└─────────┘     └────────────┘     └───────────┘     └──────────┘
                      │                                     ▲
                      └─────────────────────────────────────┘
                          (erro no LLM ou validação)
```

**Transições válidas**:
- `queued` → `processing` (worker consumiu a mensagem)
- `processing` → `completed` (LLM respondeu com sucesso)
- `processing` → `failed` (erro na validação ou chamada LLM)
