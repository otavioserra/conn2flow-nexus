# SPEC-09: Configuration

> **Status**: ✅ Approved
> **Version**: 1.0.0
> **Created**: 2025-07-16
> **Last updated**: 2025-07-16

---

## 1. Configuration Mechanism

The system uses **`pydantic-settings`** for centralized and type-safe configuration.

```
                    ┌─────────────────────┐
                    │     .env file        │  ← default values
                    ├─────────────────────┤
                    │  Environment vars    │  ← override .env
                    ├─────────────────────┤
                    │   pydantic-settings  │  ← validation + types
                    ├─────────────────────┤
                    │    Settings class    │  ← single source of truth
                    └─────────────────────┘
```

**Rules**:
- All configuration comes from environment variables
- `pydantic-settings` reads `.env` and real environment variables
- Real environment variables override `.env`
- All values are validated at startup (before the server starts)
- Invalid configuration → exception → the app does NOT start

## 2. Complete Variable Table

### Application

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APP_NAME` | `str` | `"Conn2Flow Nexus AI"` | Application name |
| `APP_VERSION` | `str` | `"0.1.0"` | Version |
| `APP_ENV` | `str` | `"development"` | Environment (`development`/`production`) |
| `APP_DEBUG` | `bool` | `True` | Enables Swagger and verbose logs |
| `APP_LOG_LEVEL` | `str` | `"INFO"` | Log level |

### Security

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `C2F_API_KEY` | `str` | `""` | API Key for authentication |
| `C2F_WEBHOOK_SECRET` | `str` | `""` | HMAC secret for signing webhooks |

### LLM API Keys

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OPENAI_API_KEY` | `str` | `""` | OpenAI API Key |
| `ANTHROPIC_API_KEY` | `str` | `""` | Anthropic (Claude) API Key |
| `GEMINI_API_KEY` | `str` | `""` | Google Gemini API Key |
| `GROQ_API_KEY` | `str` | `""` | Groq API Key |

### Kafka

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `str` | `"localhost:9092"` | Kafka server address |
| `KAFKA_TOPIC_TASKS` | `str` | `"c2f.tasks"` | Task topic |
| `KAFKA_TOPIC_RESULTS` | `str` | `"c2f.results"` | Results topic |
| `KAFKA_CONSUMER_GROUP_TASK` | `str` | `"c2f-task-group"` | Task consumer group |
| `KAFKA_CONSUMER_GROUP_DELIVERY` | `str` | `"c2f-delivery-group"` | Delivery consumer group |

### Redis

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `REDIS_URL` | `str` | `"redis://localhost:6379/0"` | Redis connection URL |
| `REDIS_TTL_SECONDS` | `int` | `86400` | Default TTL (24h) |

### Webhook

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `WEBHOOK_URL` | `str` | `""` | Delivery URL for results |
| `WEBHOOK_TIMEOUT` | `int` | `30` | HTTP timeout in seconds |
| `WEBHOOK_MAX_RETRIES` | `int` | `3` | Max delivery retries |

## 3. Derived Properties

The `Settings` class exposes **computed properties** that derive values from the base variables:

| Property | Type | Logic |
|----------|------|-------|
| `is_production` | `bool` | `app_env == "production"` |
| `is_development` | `bool` | `app_env == "development"` |
| `cors_origins` | `list[str]` | `["*"]` in dev, `[]` in prod |

## 4. Validators

### LLM Keys Validation

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
    if not has_any:
        import logging
        logging.warning("No LLM API key configured")
    return self
```

**Rules**:
- In production: at least 1 key required → otherwise, raises exception
- In development: only emits a warning

## 5. Singleton Pattern

```python
_settings: Settings | None = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

**Rule**: Settings is instantiated only once. `get_settings()` is used as FastAPI `Depends()` in routes and as direct call in workers.

## 6. `.env.example` File

```env
# Application
APP_NAME=Conn2Flow Nexus AI
APP_VERSION=0.1.0
APP_ENV=development
APP_DEBUG=true
APP_LOG_LEVEL=INFO

# Security
C2F_API_KEY=your-api-key-here
C2F_WEBHOOK_SECRET=your-webhook-secret-here

# LLM Keys
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
GROQ_API_KEY=

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_TASKS=c2f.tasks
KAFKA_TOPIC_RESULTS=c2f.results

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_TTL_SECONDS=86400

# Webhook
WEBHOOK_URL=http://localhost/api/nexus/callback
WEBHOOK_TIMEOUT=30
WEBHOOK_MAX_RETRIES=3
```
# SPEC-09: Configuration

> **Status**: ✅ Aprovada
> **Versão**: 1.0.0
> **Criada em**: 2025-07-16
> **Última atualização**: 2025-07-16

---

## 1. Mecanismo de Configuração

O sistema usa **pydantic-settings** (`BaseSettings`) para gerenciar configuração:

| Prioridade | Fonte | Descrição |
|-----------|-------|-----------|
| 1 (maior) | Variáveis de ambiente | `export OPENAI_API_KEY=sk-xxx` |
| 2 | Arquivo `.env` | Carregado automaticamente |
| 3 (menor) | Defaults no código | Valores padrão definidos na classe |

**Regras**:
- Variáveis de ambiente têm precedência sobre `.env`
- `.env` é carregado com encoding UTF-8
- Case insensitive (`app_name` == `APP_NAME`)
- `extra="ignore"` — variáveis desconhecidas são silenciosamente ignoradas
- Singleton via `@lru_cache` — uma única instância por processo

## 2. Variáveis de Ambiente

### Application

| Variável | Tipo | Default | Descrição |
|----------|------|---------|-----------|
| `APP_NAME` | `str` | `conn2flow-nexus-ai` | Nome interno da aplicação |
| `APP_ENV` | `str` | `development` | Ambiente: `development`, `staging`, `production` |
| `APP_DEBUG` | `bool` | `false` | Ativa Swagger e logs detalhados |
| `APP_VERSION` | `str` | `0.1.0` | Versão semântica do app |
| `API_HOST` | `str` | `0.0.0.0` | Host de bind do uvicorn |
| `API_PORT` | `int` | `8000` | Porta do uvicorn |
| `LOG_LEVEL` | `str` | `INFO` | Nível de log: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

### API Security

| Variável | Tipo | Default | Descrição |
|----------|------|---------|-----------|
| `C2F_API_KEY` | `str` | `""` | API key para autenticação de requests |

### LLM Provider Keys

| Variável | Tipo | Default | Descrição |
|----------|------|---------|-----------|
| `OPENAI_API_KEY` | `str` | `""` | API key da OpenAI |
| `ANTHROPIC_API_KEY` | `str` | `""` | API key da Anthropic |
| `GEMINI_API_KEY` | `str` | `""` | API key do Google Gemini |
| `GROQ_API_KEY` | `str` | `""` | API key do Groq |

### Default LLM

| Variável | Tipo | Default | Descrição |
|----------|------|---------|-----------|
| `DEFAULT_MODEL` | `str` | `gpt-4o-mini` | Modelo LLM padrão quando não especificado |

### Kafka

| Variável | Tipo | Default | Descrição |
|----------|------|---------|-----------|
| `KAFKA_BOOTSTRAP_SERVERS` | `str` | `kafka:9092` | Endereço do broker Kafka |
| `KAFKA_TOPIC_INCOMING` | `str` | `c2f_incoming_tasks` | Tópico de tarefas de entrada |
| `KAFKA_TOPIC_COMPLETED` | `str` | `c2f_completed_tasks` | Tópico de tarefas completadas |
| `KAFKA_CONSUMER_GROUP` | `str` | `c2f-workers` | Consumer group dos workers |

### Redis

| Variável | Tipo | Default | Descrição |
|----------|------|---------|-----------|
| `REDIS_URL` | `str` | `redis://redis:6379/0` | URL de conexão Redis |

### Webhook

| Variável | Tipo | Default | Descrição |
|----------|------|---------|-----------|
| `C2F_WEBHOOK_URL` | `str` | `""` | URL padrão de callback para o Conn2Flow |
| `C2F_WEBHOOK_SECRET` | `str` | `""` | Secret para assinatura HMAC dos webhooks |

## 3. Properties Derivadas

```python
@property
def is_production(self) -> bool:
    return self.app_env == "production"
```

| Property | Tipo | Derivada de | Valor |
|----------|------|-------------|-------|
| `is_production` | `bool` | `app_env` | `True` se `app_env == "production"` |

## 4. Validações

### Model Validator: LLM Keys em Produção

```python
@model_validator(mode="after")
def _warn_missing_keys(self) -> "Settings":
```

**Regra**: Se `is_production == True` e nenhuma LLM API key está configurada, a aplicação **lança `ValueError`** e não inicia.

### Impacto do `APP_ENV`

| `APP_ENV` | `is_production` | API Key obrigatória | CORS | Swagger | LLM Keys validadas |
|-----------|----------------|--------------------|----- |---------|---------------------|
| `development` | `False` | Não | `*` | ✅ | Não |
| `staging` | `False` | Não | `*` | ✅ | Não |
| `production` | `True` | Sim | `[]` | ❌ | Sim |

### Impacto do `APP_DEBUG`

| `APP_DEBUG` | `/docs` | `/redoc` |
|-------------|---------|----------|
| `true` | Habilitado | Habilitado |
| `false` | Desabilitado | Desabilitado |

## 5. Singleton Pattern

```python
@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Regras**:
- `get_settings()` retorna sempre a **mesma instância**
- O `.env` é lido apenas uma vez, na primeira chamada
- Para testes, usar `monkeypatch` nas variáveis de ambiente ANTES da primeira chamada
- Para limpar o cache: `get_settings.cache_clear()` (usado em testes)

## 6. Arquivo `.env.example`

Template para desenvolvedores. Deve conter todas as variáveis com valores de exemplo:

```env
APP_NAME=conn2flow-nexus-ai
APP_ENV=development
APP_DEBUG=true
APP_VERSION=0.1.0
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=DEBUG
C2F_API_KEY=dev-api-key-change-me
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
GROQ_API_KEY=
DEFAULT_MODEL=gpt-4o-mini
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC_INCOMING=c2f_incoming_tasks
KAFKA_TOPIC_COMPLETED=c2f_completed_tasks
KAFKA_CONSUMER_GROUP=c2f-workers
REDIS_URL=redis://redis:6379/0
C2F_WEBHOOK_URL=http://host.docker.internal/api/webhook/ai-response
C2F_WEBHOOK_SECRET=dev-webhook-secret
```

**Regras**:
- `.env.example` é versionado no Git
- `.env` NÃO é versionado (está no `.gitignore`)
- API keys de LLM devem ficar vazias no exemplo
