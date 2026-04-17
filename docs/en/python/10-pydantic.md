# 10. Pydantic & Data Validation

## What Is Pydantic?

Pydantic is a **data validation and serialization library** that uses Python type annotations. It's the foundation of FastAPI's request/response handling.

**PHP comparison:** Imagine combining Laravel's `FormRequest` validation + `JsonResource` serialization + strict typing — that's Pydantic.

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int
    email: str | None = None

# Valid
user = User(name="Alice", age=30)
print(user.name)  # "Alice"

# Automatic type coercion
user = User(name="Alice", age="30")  # age is coerced to int
print(user.age)   # 30 (int, not str!)

# Validation error
user = User(name="Alice", age="not_a_number")
# ❌ ValidationError: 1 validation error for User
#    age: Input should be a valid integer
```

---

## BaseModel — The Foundation

### PHP DTO/Value Object
```php
class TaskRequest {
    public function __construct(
        public readonly string $model,
        public readonly array $messages,
        public readonly float $temperature = 0.7,
        public readonly ?int $maxTokens = null,
    ) {}
}
```

### Python Pydantic
```python
from pydantic import BaseModel, Field
from typing import Any

class TaskRequest(BaseModel):
    """Payload sent by Conn2Flow to process an AI task."""

    model: str = Field(
        default="gpt-4o-mini",
        description="LLM model identifier",
        examples=["gpt-4o", "claude-3-5-sonnet"],
    )
    messages: list[dict[str, str]] = Field(
        ...,  # Required (no default)
        description="List of messages in OpenAI format",
        min_length=1,
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,   # >= 0.0
        le=2.0,   # <= 2.0
    )
    max_tokens: int | None = Field(
        default=None,
        gt=0,      # > 0
        le=128000,  # <= 128000
    )
    webhook_url: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)
    stream: bool = Field(default=False)
```

---

## `Field()` — Detailed Configuration

```python
from pydantic import Field

class Product(BaseModel):
    # Required field (no default)
    name: str = Field(..., min_length=1, max_length=200)

    # Default value
    price: float = Field(default=0.0, ge=0)

    # Default factory (new dict/list per instance)
    tags: list[str] = Field(default_factory=list)

    # Numeric constraints
    quantity: int = Field(default=1, gt=0, le=10000)

    # String pattern
    sku: str = Field(pattern=r'^[A-Z]{3}-\d{4}$')

    # Description (appears in OpenAPI docs)
    description: str | None = Field(
        default=None,
        description="Product description",
        examples=["A great product"],
    )
```

### Field Constraints:

| Constraint | Type | Meaning |
|-----------|------|---------|
| `...` | Any | Required (no default) |
| `default=X` | Any | Default value |
| `default_factory=list` | Callable | Factory for mutable defaults |
| `ge=0` | Numeric | Greater than or equal |
| `gt=0` | Numeric | Greater than (strict) |
| `le=100` | Numeric | Less than or equal |
| `lt=100` | Numeric | Less than (strict) |
| `min_length=1` | String/List | Minimum length |
| `max_length=200` | String/List | Maximum length |
| `pattern=r'...'` | String | Regex pattern |
| `description="..."` | Any | Documentation |
| `examples=[...]` | Any | Example values |

### From our codebase — `Field(...)` means **required**:
```python
# src/api/schemas/requests.py
messages: list[dict[str, str]] = Field(
    ...,  # This is required — no default
    description="List of messages in OpenAI format [{role, content}]",
    min_length=1,
)
```

### `default_factory` — Why It Matters:
```python
# ❌ BUG: All instances share the same dict!
metadata: dict[str, Any] = {}

# ✅ Each instance gets a new dict
metadata: dict[str, Any] = Field(default_factory=dict)
```

This is the Pydantic equivalent of the Python gotcha with mutable default arguments.

---

## Validation — Automatic & Custom

### Automatic (from type hints + Field)
```python
# All of these raise ValidationError:
TaskRequest(messages=[])                    # min_length=1
TaskRequest(messages=[{"role": "user", "content": "Hi"}], temperature=3.0)  # le=2.0
TaskRequest(messages=[{"role": "user", "content": "Hi"}], max_tokens=-1)    # gt=0
```

### Custom Validators
```python
from pydantic import BaseModel, field_validator, model_validator

class UserCreate(BaseModel):
    username: str
    password: str
    password_confirm: str

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError("Username must be alphanumeric")
        return v.lower()  # Transform: normalize to lowercase

    @model_validator(mode="after")
    def passwords_match(self) -> "UserCreate":
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self
```

### From our codebase (`src/config/settings.py`):
```python
@model_validator(mode="after")
def _warn_missing_keys(self) -> "Settings":
    """Validates that at least one LLM API key is configured in production."""
    has_any = any([
        self.openai_api_key,
        self.anthropic_api_key,
        self.gemini_api_key,
        self.groq_api_key,
    ])
    if not has_any and self.is_production:
        raise ValueError(
            "At least one LLM API key must be set in production "
            "(OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY, GROQ_API_KEY)"
        )
    return self
```

**`mode="after"`** → Runs **after** all field validations. The model is fully constructed, so you can access `self.field_name`.

**`mode="before"`** → Runs **before** field validations. Receives raw input data.

---

## Serialization — `model_dump()` and `model_dump_json()`

```python
class TaskEvent(BaseModel):
    task_id: str
    model: str
    messages: list[dict[str, str]]
    temperature: float = 0.7
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

event = TaskEvent(
    task_id="abc-123",
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}],
)

# To dict
data = event.model_dump()
# {"task_id": "abc-123", "model": "gpt-4o-mini", "messages": [...], "temperature": 0.7, "created_at": datetime(...)}

# To dict (JSON-compatible — datetime becomes string)
data = event.model_dump(mode="json")
# {"task_id": "abc-123", ..., "created_at": "2025-01-15T10:30:00+00:00"}

# To JSON string
json_str = event.model_dump_json()
# '{"task_id":"abc-123",...}'

# Exclude fields
data = event.model_dump(exclude={"created_at"})

# Include only specific fields
data = event.model_dump(include={"task_id", "status"})

# Exclude None values
data = event.model_dump(exclude_none=True)
```

### From our codebase — Kafka serialization:
```python
# src/core/kafka_producer.py
def _serialize(value: Any) -> bytes:
    if isinstance(value, BaseModel):
        return orjson.dumps(value.model_dump(mode="json"))
    if isinstance(value, (dict, list)):
        return orjson.dumps(value)
    return orjson.dumps(value)
```

`model_dump(mode="json")` ensures all values are JSON-serializable (datetime → string, etc.).

---

## Pydantic Settings — Environment Configuration

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",           # Load from .env file
        env_file_encoding="utf-8",
        case_sensitive=False,       # APP_ENV and app_env are the same
        extra="ignore",            # Ignore extra env vars
    )

    # Field name → env var (automatic)
    app_name: str = "conn2flow-nexus-ai"     # APP_NAME env var
    app_env: str = "development"              # APP_ENV env var
    kafka_bootstrap_servers: str = "kafka:9092"  # KAFKA_BOOTSTRAP_SERVERS

    # Nested names use underscore separator
    openai_api_key: str = ""                  # OPENAI_API_KEY
    c2f_api_key: str = ""                     # C2F_API_KEY
```

### Loading Priority (highest to lowest):
1. `__init__` arguments
2. Environment variables
3. `.env` file
4. Default values in the model

### Singleton Pattern with `@lru_cache`:
```python
from functools import lru_cache

@lru_cache
def get_settings() -> Settings:
    """Returns the singleton settings instance."""
    return Settings()
```

First call: creates and caches. Subsequent calls: returns cached instance. This ensures:
- Settings are loaded **once** (performance)
- All code uses the **same** settings instance (consistency)

---

## Events — Kafka Models

```python
# src/models/events.py
from datetime import datetime, timezone

class TaskEvent(BaseModel):
    """Event published to the c2f_incoming_tasks topic."""
    task_id: str
    model: str
    messages: list[dict[str, str]]
    temperature: float = 0.7
    max_tokens: int | None = None
    webhook_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    stream: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TaskResultEvent(BaseModel):
    """Event published to the c2f_completed_tasks topic."""
    task_id: str
    status: str = Field(description="completed | failed")
    model: str
    result: dict[str, Any] | None = None
    error: str | None = None
    webhook_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    usage: dict[str, int] | None = Field(default=None)
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

**`default_factory=lambda: datetime.now(timezone.utc)`** → Each event gets the **current** timestamp when created, not when the class is defined.

---

## Response Models

```python
# src/api/schemas/responses.py
class TaskAcceptedResponse(BaseModel):
    task_id: str = Field(description="Unique task identifier")
    status: str = Field(default="queued")
    message: str = Field(default="Task accepted for async processing")

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str = Field(description="queued | processing | completed | failed")
    result: dict[str, Any] | None = Field(default=None)
    error: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)
```

In FastAPI:
```python
@router.post("/submit", response_model=TaskAcceptedResponse, status_code=202)
async def submit_task(payload: TaskRequest, ...):
    return TaskAcceptedResponse(task_id=task_id, status="queued")
```

`response_model=TaskAcceptedResponse` tells FastAPI:
1. Validate the response against this schema
2. Serialize using this model (exclude extra fields)
3. Generate OpenAPI documentation

---

## Testing Pydantic Models

```python
# tests/test_schemas.py
class TestTaskRequest:
    def test_valid_minimal(self):
        req = TaskRequest(messages=[{"role": "user", "content": "Hello"}])
        assert req.model == "gpt-4o-mini"  # Default
        assert req.temperature == 0.7
        assert req.stream is False

    def test_empty_messages_fails(self):
        with pytest.raises(ValidationError):
            TaskRequest(messages=[])  # min_length=1

    def test_temperature_out_of_range(self):
        with pytest.raises(ValidationError):
            TaskRequest(messages=[...], temperature=3.0)  # le=2.0

class TestTaskEvent:
    def test_serialization(self):
        event = TaskEvent(task_id="t1", model="gpt-4o", messages=[...])
        data = event.model_dump(mode="json")
        assert data["task_id"] == "t1"
        assert "created_at" in data  # Datetime serialized as string
```

---

## Pydantic v1 vs v2

Our project uses **Pydantic v2** (2.x). If you see old tutorials:

| Pydantic v1 | Pydantic v2 |
|-------------|-------------|
| `.dict()` | `.model_dump()` |
| `.json()` | `.model_dump_json()` |
| `.parse_obj()` | `.model_validate()` |
| `@validator` | `@field_validator` |
| `@root_validator` | `@model_validator` |
| `class Config:` | `model_config = SettingsConfigDict(...)` |
| `schema()` | `model_json_schema()` |

---

## Previous: [← Error Handling](09-error-handling.md) | Next: [FastAPI →](11-fastapi.md)
