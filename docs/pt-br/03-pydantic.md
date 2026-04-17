# 3. Pydantic — Validação de Dados e Configuração

## O Que É Pydantic?

**Pydantic** é a biblioteca de validação de dados mais popular do Python. Ela:
- Valida tipos automaticamente
- Converte dados (coerção de tipos)
- Gera JSON Schema
- Serializa/deserializa modelos

No Conn2Flow Nexus AI, Pydantic é usado em **duas formas**:
1. **Pydantic v2 (BaseModel)** — para schemas de request/response e eventos Kafka
2. **pydantic-settings (BaseSettings)** — para carregar configurações do `.env`

---

## Pydantic BaseModel — Schemas

### Request Schema: `src/api/schemas/requests.py`

```python
class TaskRequest(BaseModel):
    model: str = Field(
        default="gpt-4o-mini",
        description="Identificador do modelo LLM",
        examples=["gpt-4o", "claude-3-5-sonnet"],
    )
    messages: list[dict[str, str]] = Field(
        ...,            # ← "..." significa OBRIGATÓRIO (sem default)
        min_length=1,   # ← Pelo menos 1 mensagem
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,         # ← greater than or equal (≥ 0.0)
        le=2.0,         # ← less than or equal (≤ 2.0)
    )
    max_tokens: int | None = Field(
        default=None,
        gt=0,           # ← greater than (> 0)
        le=128000,      # ← máximo 128k tokens
    )
```

### Conceitos-Chave:

**`Field(...)`** — O `...` (Ellipsis) do Python indica que o campo é obrigatório, sem valor default.

**Validadores numéricos:**
- `ge` = greater or equal (≥)
- `le` = less or equal (≤)
- `gt` = greater than (>)
- `lt` = less than (<)

**Type Hints Python 3.10+:**
- `int | None` → aceita `int` ou `None` (Union type com syntax moderna)
- `list[dict[str, str]]` → lista de dicionários com chaves e valores string
- `dict[str, Any]` → dicionário com chaves string e valores de qualquer tipo

**`default_factory`:**
```python
metadata: dict[str, Any] = Field(default_factory=dict)
```
- `default_factory=dict` cria um **novo dicionário** a cada instância
- Sem isso, todas as instâncias compartilhariam o mesmo dict (bug clássico do Python com mutable defaults)

---

## Response Schemas: `src/api/schemas/responses.py`

```python
class TaskAcceptedResponse(BaseModel):
    task_id: str = Field(description="Identificador único da tarefa")
    status: str = Field(default="queued")
    message: str = Field(default="Task accepted for async processing")

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: dict[str, Any] | None = Field(default=None)
    error: str | None = Field(default=None)
```

**Conceito: Contratos de API**
- Definir `response_model=TaskAcceptedResponse` no endpoint garante que:
  1. O FastAPI valida a **saída** do endpoint
  2. Campos extras são removidos automaticamente
  3. O Swagger UI mostra o schema correto
  4. A documentação é auto-gerada

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

**Conceito: Serialização para Kafka**

Estes modelos são serializados para bytes antes de entrar no Kafka:
```python
# Em kafka_producer.py:
def _serialize(value: Any) -> bytes:
    if isinstance(value, BaseModel):
        return orjson.dumps(value.model_dump(mode="json"))
```

- `model_dump(mode="json")` converte o modelo para dict com tipos JSON-safe
  - `datetime` → string ISO 8601
  - `Enum` → valor primitivo
- `orjson.dumps()` converte o dict para bytes JSON (3-10x mais rápido que `json.dumps()`)

---

## pydantic-settings — Configuração: `src/config/settings.py`

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,     # APP_ENV = app_env = App_Env
        extra="ignore",           # Ignora variáveis extras no .env
    )

    app_name: str = "conn2flow-nexus-ai"
    kafka_bootstrap_servers: str = "kafka:9092"
    openai_api_key: str = ""
```

### Como Funciona:

1. O pydantic-settings lê o arquivo `.env`
2. Mapeia cada variável de ambiente para o campo correspondente:
   - `APP_NAME=conn2flow-nexus-ai` → `settings.app_name = "conn2flow-nexus-ai"`
   - `KAFKA_BOOTSTRAP_SERVERS=kafka:9092` → `settings.kafka_bootstrap_servers = "kafka:9092"`
3. Variáveis de ambiente do **sistema** têm prioridade sobre o `.env`

### `@model_validator` — Validação Customizada

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

**Conceito: `model_validator(mode="after")`**
- Roda **depois** de todos os campos serem validados individualmente
- Permite validação que envolve múltiplos campos ao mesmo tempo
- `mode="before"` rodaria antes da validação dos campos

### `@property` — Propriedade Computada

```python
@property
def is_production(self) -> bool:
    return self.app_env == "production"
```

- Não é armazenado — é **calculado** a cada acesso
- Usado como `settings.is_production` (sem parênteses)

### Singleton com `@lru_cache`

```python
@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Conceito: `@lru_cache` (Least Recently Used Cache)**
- A primeira chamada cria o objeto `Settings()` e o armazena em cache
- Chamadas subsequentes retornam o **mesmo objeto** — não reler o `.env`
- Implementa o padrão **Singleton** de forma Pythonica
- No FastAPI, isso garante que toda a app usa as mesmas configurações

---

## Fluxo Completo de Validação

```
Request JSON ──► Pydantic TaskRequest ──► Validação automática ──► Endpoint
                     │                          │
                     │                    ✗ Inválido → HTTP 422
                     │
                     ▼
              Campos validados:
              - messages tem ≥ 1 item? ✓
              - temperature entre 0.0 e 2.0? ✓
              - max_tokens > 0 e ≤ 128000? ✓
```

---

## Anterior: [← FastAPI](02-fastapi.md) | Próximo: [Apache Kafka →](04-kafka.md)
