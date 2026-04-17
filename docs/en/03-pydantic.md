# 3. Pydantic — Data Validation and Configuration

## What Is Pydantic?

**Pydantic** is the most popular data validation library in Python. It:
- Validates types automatically
- Converts data (type coercion)
- Generates JSON Schema
- Serializes/deserializes models

In Conn2Flow Nexus AI, Pydantic is used in **two forms**:
1. **Pydantic v2 (BaseModel)** — for request/response schemas and Kafka events
2. **pydantic-settings (BaseSettings)** — for loading configuration from `.env`

---

## Pydantic BaseModel — Schemas

### Request Schema: `src/api/schemas/requests.py`

```python
class TaskRequest(BaseModel):
    model: str = Field(
        default="gpt-4o-mini",
        description="LLM model identifier",
        examples=["gpt-4o", "claude-3-5-sonnet"],
    )
    messages: list[dict[str, str]] = Field(
        ...,            # ← "..." means REQUIRED (no default)
        min_length=1,   # ← At least 1 message
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,         # ← greater than or equal (≥ 0.0)
        le=2.0,         # ← less than or equal (≤ 2.0)
    )
    max_tokens: int | None = Field(
        default=None,
        gt=0,           # ← greater than (> 0)
        le=128000,      # ← max 128k tokens
    )
```

### Key Concepts:

**`Field(...)`** — Python's `...` (Ellipsis) indicates the field is required, with no default value.

**Numeric validators:**
- `ge` = greater or equal (≥)
- `le` = less or equal (≤)
- `gt` = greater than (>)
- `lt` = less than (<)

**Python 3.10+ Type Hints:**
- `int | None` → accepts `int` or `None` (Union type with modern syntax)
- `list[dict[str, str]]` → list of dictionaries with string keys and values
- `dict[str, Any]` → dictionary with string keys and any type values

**`default_factory`:**
```python
metadata: dict[str, Any] = Field(default_factory=dict)
```
- `default_factory=dict` creates a **new dictionary** for each instance
- Without this, all instances would share the same dict (classic Python bug with mutable defaults)

---

## Response Schemas: `src/api/schemas/responses.py`

```python
class TaskAcceptedResponse(BaseModel):
    task_id: str = Field(description="Unique task identifier")
    status: str = Field(default="queued")
    message: str = Field(default="Task accepted for async processing")

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: dict[str, Any] | None = Field(default=None)
    error: str | None = Field(default=None)
```

**Concept: API Contracts**
- Defining `response_model=TaskAcceptedResponse` on the endpoint ensures that:
  1. FastAPI validates the endpoint's **output**
  2. Extra fields are removed automatically
  3. Swagger UI shows the correct schema
  4. Documentation is auto-generated

---

## Event Models: `src/models/events.py`

```python
class TaskEvent(BaseModel):
    task_id: str
    model: str
    messages: list[dict[str, str]]
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
```

**Concept: Serialization for Kafka**

These models are serialized to bytes before entering Kafka:
```python
# In kafka_producer.py:
def _serialize(value: Any) -> bytes:
    if isinstance(value, BaseModel):
        return orjson.dumps(value.model_dump(mode="json"))
```

- `model_dump(mode="json")` converts the model to a dict with JSON-safe types
  - `datetime` → ISO 8601 string
  - `Enum` → primitive value
- `orjson.dumps()` converts the dict to JSON bytes (3-10x faster than `json.dumps()`)

---

## pydantic-settings — Configuration: `src/config/settings.py`

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,     # APP_ENV = app_env = App_Env
        extra="ignore",           # Ignores extra variables in .env
    )

    app_name: str = "conn2flow-nexus-ai"
    kafka_bootstrap_servers: str = "kafka:9092"
    openai_api_key: str = ""
```

### How It Works:

1. pydantic-settings reads the `.env` file
2. Maps each environment variable to the corresponding field:
   - `APP_NAME=conn2flow-nexus-ai` → `settings.app_name = "conn2flow-nexus-ai"`
   - `KAFKA_BOOTSTRAP_SERVERS=kafka:9092` → `settings.kafka_bootstrap_servers = "kafka:9092"`
3. **System** environment variables take priority over `.env`

### `@model_validator` — Custom Validation

```python
@model_validator(mode="after")
def _warn_missing_keys(self) -> "Settings":
    has_any = any([
        self.openai_api_key,
        self.anthropic_api_key,
        self.gemini_api_key,
        self.groq_api_key,
    ])
    if not has_any and self.is_production:
        raise ValueError("At least one LLM API key must be set in production")
    return self
```

**Concept: `model_validator(mode="after")`**
- Runs **after** all fields are individually validated
- Allows validation involving multiple fields simultaneously
- `mode="before"` would run before field validation

### `@property` — Computed Property

```python
@property
def is_production(self) -> bool:
    return self.app_env == "production"
```

- Not stored — it's **computed** on each access
- Used as `settings.is_production` (without parentheses)

### Singleton with `@lru_cache`

```python
@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Concept: `@lru_cache` (Least Recently Used Cache)**
- The first call creates the `Settings()` object and stores it in cache
- Subsequent calls return the **same object** — doesn't re-read `.env`
- Implements the **Singleton** pattern in a Pythonic way
- In FastAPI, this ensures the entire app uses the same settings

---

## Complete Validation Flow

```
Request JSON ──► Pydantic TaskRequest ──► Automatic validation ──► Endpoint
                     │                          │
                     │                    ✗ Invalid → HTTP 422
                     │
                     ▼
              Validated fields:
              - messages has ≥ 1 item? ✓
              - temperature between 0.0 and 2.0? ✓
              - max_tokens > 0 and ≤ 128000? ✓
```

---

## Previous: [← FastAPI](02-fastapi.md) | Next: [Apache Kafka →](04-kafka.md)
