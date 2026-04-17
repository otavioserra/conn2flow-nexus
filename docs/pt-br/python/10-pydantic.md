# 10. Pydantic & Validação de Dados

## O Que É Pydantic?

Pydantic é uma **biblioteca de validação e serialização de dados** que usa anotações de tipo Python. É a base do handling de request/response do FastAPI.

**Comparação PHP:** Imagine combinar a validação do `FormRequest` do Laravel + serialização do `JsonResource` + tipagem estrita — isso é o Pydantic.

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int
    email: str | None = None

# Válido
user = User(name="Alice", age=30)
print(user.name)  # "Alice"

# Coerção automática de tipo
user = User(name="Alice", age="30")  # age é convertido para int
print(user.age)   # 30 (int, não str!)

# Erro de validação
user = User(name="Alice", age="não_é_número")
# ❌ ValidationError: 1 validation error for User
#    age: Input should be a valid integer
```

---

## BaseModel — A Fundação

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
    """Payload enviado pelo Conn2Flow para processar uma tarefa de IA."""

    model: str = Field(
        default="gpt-4o-mini",
        description="Identificador do modelo LLM",
        examples=["gpt-4o", "claude-3-5-sonnet"],
    )
    messages: list[dict[str, str]] = Field(
        ...,  # Obrigatório (sem default)
        description="Lista de mensagens no formato OpenAI",
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

## `Field()` — Configuração Detalhada

```python
from pydantic import Field

class Product(BaseModel):
    # Campo obrigatório (sem default)
    name: str = Field(..., min_length=1, max_length=200)

    # Valor padrão
    price: float = Field(default=0.0, ge=0)

    # Factory padrão (novo dict/list por instância)
    tags: list[str] = Field(default_factory=list)

    # Restrições numéricas
    quantity: int = Field(default=1, gt=0, le=10000)

    # Padrão de string (regex)
    sku: str = Field(pattern=r'^[A-Z]{3}-\d{4}$')

    # Descrição (aparece na documentação OpenAPI)
    description: str | None = Field(
        default=None,
        description="Descrição do produto",
        examples=["Um ótimo produto"],
    )
```

### Restrições do Field:

| Restrição | Tipo | Significado |
|-----------|------|-------------|
| `...` | Qualquer | Obrigatório (sem default) |
| `default=X` | Qualquer | Valor padrão |
| `default_factory=list` | Callable | Factory para defaults mutáveis |
| `ge=0` | Numérico | Maior ou igual |
| `gt=0` | Numérico | Maior que (estrito) |
| `le=100` | Numérico | Menor ou igual |
| `lt=100` | Numérico | Menor que (estrito) |
| `min_length=1` | String/Lista | Comprimento mínimo |
| `max_length=200` | String/Lista | Comprimento máximo |
| `pattern=r'...'` | String | Padrão regex |
| `description="..."` | Qualquer | Documentação |
| `examples=[...]` | Qualquer | Valores de exemplo |

### Do nosso código — `Field(...)` significa **obrigatório**:
```python
# src/api/schemas/requests.py
messages: list[dict[str, str]] = Field(
    ...,  # Isto é obrigatório — sem default
    description="List of messages in OpenAI format [{role, content}]",
    min_length=1,
)
```

### `default_factory` — Por Que Importa:
```python
# ❌ BUG: Todas as instâncias compartilham o mesmo dict!
metadata: dict[str, Any] = {}

# ✅ Cada instância recebe um novo dict
metadata: dict[str, Any] = Field(default_factory=dict)
```

---

## Validação — Automática & Customizada

### Automática (de type hints + Field)
```python
# Todos estes lançam ValidationError:
TaskRequest(messages=[])                    # min_length=1
TaskRequest(messages=[{"role": "user", "content": "Hi"}], temperature=3.0)  # le=2.0
TaskRequest(messages=[{"role": "user", "content": "Hi"}], max_tokens=-1)    # gt=0
```

### Validadores Customizados
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
            raise ValueError("Username deve ser alfanumérico")
        return v.lower()  # Transforma: normaliza para minúsculas

    @model_validator(mode="after")
    def passwords_match(self) -> "UserCreate":
        if self.password != self.password_confirm:
            raise ValueError("Senhas não coincidem")
        return self
```

### Do nosso código (`src/config/settings.py`):
```python
@model_validator(mode="after")
def _warn_missing_keys(self) -> "Settings":
    """Valida que pelo menos uma chave API LLM está configurada em produção."""
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

**`mode="after"`** → Executa **depois** de todas as validações de campo. O modelo está totalmente construído, então você pode acessar `self.nome_campo`.

**`mode="before"`** → Executa **antes** das validações de campo. Recebe os dados brutos.

---

## Serialização — `model_dump()` e `model_dump_json()`

```python
event = TaskEvent(
    task_id="abc-123",
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}],
)

# Para dict
data = event.model_dump()

# Para dict (compatível com JSON — datetime vira string)
data = event.model_dump(mode="json")

# Para string JSON
json_str = event.model_dump_json()

# Excluir campos
data = event.model_dump(exclude={"created_at"})

# Incluir apenas campos específicos
data = event.model_dump(include={"task_id", "status"})

# Excluir valores None
data = event.model_dump(exclude_none=True)
```

### Do nosso código — Serialização Kafka:
```python
# src/core/kafka_producer.py
def _serialize(value: Any) -> bytes:
    if isinstance(value, BaseModel):
        return orjson.dumps(value.model_dump(mode="json"))
    if isinstance(value, (dict, list)):
        return orjson.dumps(value)
    return orjson.dumps(value)
```

`model_dump(mode="json")` garante que todos os valores são serializáveis em JSON (datetime → string, etc.).

---

## Pydantic Settings — Configuração via Ambiente

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",           # Carrega do arquivo .env
        env_file_encoding="utf-8",
        case_sensitive=False,       # APP_ENV e app_env são iguais
        extra="ignore",            # Ignora vars extras
    )

    app_name: str = "conn2flow-nexus-ai"     # APP_NAME env var
    app_env: str = "development"              # APP_ENV env var
    kafka_bootstrap_servers: str = "kafka:9092"
    openai_api_key: str = ""                  # OPENAI_API_KEY
```

### Prioridade de Carregamento (maior para menor):
1. Argumentos do `__init__`
2. Variáveis de ambiente
3. Arquivo `.env`
4. Valores padrão no modelo

### Padrão Singleton com `@lru_cache`:
```python
from functools import lru_cache

@lru_cache
def get_settings() -> Settings:
    """Retorna a instância singleton de settings."""
    return Settings()
```

---

## Pydantic v1 vs v2

Nosso projeto usa **Pydantic v2** (2.x). Se encontrar tutoriais antigos:

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

## Anterior: [← Tratamento de Erros](09-tratamento-erros.md) | Próximo: [FastAPI →](11-fastapi.md)
