# SPEC-08: Security

> **Status**: ✅ Approved
> **Version**: 1.0.0
> **Created**: 2025-07-16
> **Last updated**: 2025-07-16

---

## 1. Security Layers

```
                    ┌─────────────────────┐
                    │  1. API Key Auth     │  ← Entry
                    ├─────────────────────┤
                    │  2. CORS             │  ← Browser protection
                    ├─────────────────────┤
                    │  3. Input Validation │  ← Pydantic
                    ├─────────────────────┤
                    │  4. HMAC Signing     │  ← Output (webhooks)
                    ├─────────────────────┤
                    │  5. Non-root Docker  │  ← Runtime
                    ├─────────────────────┤
                    │  6. Swagger Disabled │  ← Production
                    └─────────────────────┘
```

## 2. API Key Authentication

### Specification

| Aspect | Value |
|--------|-------|
| **Header** | `X-C2F-API-Key` |
| **Variable** | `C2F_API_KEY` |
| **Required in** | Production (`APP_ENV=production`) |
| **Optional in** | Development |
| **Applied to** | Endpoints `POST /tasks/submit` and `GET /tasks/status/{id}` |
| **Not applied to** | `GET /health` |

### Validation Rules

```
IF app_env == "production" AND c2f_api_key != "":
  IF header X-C2F-API-Key is missing OR != c2f_api_key:
    → HTTP 401 {"detail": "Invalid or missing API key"}
  IF header X-C2F-API-Key == c2f_api_key:
    → Proceed normally

IF app_env != "production":
  → Skip authentication (always proceed)
```

### Implementation

```python
async def verify_api_key(
    x_c2f_api_key: str | None = Header(None),
    settings: Settings = Depends(get_settings),
) -> Settings:
```

Uses **FastAPI Dependency Injection** — applied via `Depends(verify_api_key)`.

## 3. HMAC-SHA256 (Webhook Signing)

### Specification

| Aspect | Value |
|--------|-------|
| **Algorithm** | HMAC-SHA256 |
| **Secret** | `C2F_WEBHOOK_SECRET` |
| **Input** | Complete body (bytes) |
| **Output header** | `X-C2F-Signature: sha256={hex_digest}` |

### Signing Process

```
1. Serialize the payload → body_bytes = orjson.dumps(payload)
2. Compute HMAC:
   signature = hmac.new(
     key = secret.encode("utf-8"),
     msg = body_bytes,
     digestmod = sha256
   ).hexdigest()
3. Send in header: X-C2F-Signature: sha256={signature}
```

### Verification (Conn2Flow side)

The receiver (Conn2Flow PHP) must:

1. Read the raw body from the request
2. Read the `X-C2F-Signature` header
3. Extract the hash after `sha256=`
4. Compute `hash_hmac('sha256', $body, $secret)`
5. Compare with `hash_equals()` (timing-safe)

**Rule**: If `C2F_WEBHOOK_SECRET` is empty, the signature is an empty string.

## 4. CORS (Cross-Origin Resource Sharing)

| Environment | `allow_origins` | `allow_methods` | `allow_headers` | `allow_credentials` |
|-------------|-----------------|-----------------|-----------------|---------------------|
| development | `["*"]` | `["*"]` | `["*"]` | `True` |
| production | `[]` | `["*"]` | `["*"]` | `True` |

**Rule**: In production, CORS is blocked (`allow_origins=[]`). This is because Nexus AI is a backend-to-backend service, not accessed by browsers.

## 5. Input Validation (Pydantic)

All input is automatically validated by Pydantic v2:

| Field | Validation |
|-------|-----------|
| `messages` | `min_length=1` — must have at least 1 message |
| `temperature` | `ge=0.0, le=2.0` — between 0 and 2 |
| `max_tokens` | `gt=0, le=128000` — between 1 and 128000 if present |
| `model` | Free string (actual validation by LiteLLM) |

**Rule**: Pydantic validation rejects with HTTP 422 and error details.

## 6. Swagger/OpenAPI

| Environment | `/docs` (Swagger) | `/redoc` (ReDoc) |
|-------------|-------------------|-------------------|
| development | ✅ Enabled | ✅ Enabled |
| production | ❌ `None` | ❌ `None` |

**Rule**: Based on `APP_DEBUG`:
```python
docs_url="/docs" if settings.app_debug else None
redoc_url="/redoc" if settings.app_debug else None
```

## 7. Docker Security

| Measure | Implementation |
|---------|---------------|
| **Non-root user** | `addgroup --system c2f && adduser --system --ingroup c2f c2f` |
| **USER directive** | `USER c2f` in Dockerfile |
| **No .pyc files** | `PYTHONDONTWRITEBYTECODE=1` |
| **Minimal base** | `python:3.11-slim` (no unnecessary extras) |
| **Multi-stage** | Build dependencies don't go into the final image |

## 8. Secrets Management

| Secret | Where configured | Format |
|--------|-----------------|--------|
| `C2F_API_KEY` | `.env` / environment variable | String |
| `C2F_WEBHOOK_SECRET` | `.env` / environment variable | String |
| `OPENAI_API_KEY` | `.env` / environment variable | String |
| `ANTHROPIC_API_KEY` | `.env` / environment variable | String |
| `GEMINI_API_KEY` | `.env` / environment variable | String |
| `GROQ_API_KEY` | `.env` / environment variable | String |

**Rules**:
- Never commit `.env` with real values (use `.env.example`)
- `.env` is in `.gitignore`
- In production, use Docker secrets or orchestrator variables

## 9. LLM Keys Validation in Production

```python
@model_validator(mode="after")
def _warn_missing_keys(self) -> "Settings":
    has_any = any([openai_api_key, anthropic_api_key, gemini_api_key, groq_api_key])
    if not has_any and self.is_production:
        raise ValueError("At least one LLM API key must be set in production")
```

**Rule**: In production, the application refuses to start if no LLM API key is configured.

## 10. Threat Model (Summary)

| Threat | Mitigation |
|--------|-----------|
| Unauthorized API access | API Key header |
| Webhook spoofing | HMAC-SHA256 signing |
| CSRF via browser | CORS blocked in production |
| Malicious data injection | Strict Pydantic validation |
| Privilege escalation in container | Non-root user |
| Internal endpoint exposure | Swagger disabled in production |
| API keys in logs | LiteLLM verbose disabled |
| Startup without configuration | Key validation on initialization |
# SPEC-08: Security

> **Status**: ✅ Aprovada
> **Versão**: 1.0.0
> **Criada em**: 2025-07-16
> **Última atualização**: 2025-07-16

---

## 1. Camadas de Segurança

```
                    ┌─────────────────────┐
                    │  1. API Key Auth     │  ← Entrada
                    ├─────────────────────┤
                    │  2. CORS             │  ← Browser protection
                    ├─────────────────────┤
                    │  3. Input Validation │  ← Pydantic
                    ├─────────────────────┤
                    │  4. HMAC Signing     │  ← Saída (webhooks)
                    ├─────────────────────┤
                    │  5. Non-root Docker  │  ← Runtime
                    ├─────────────────────┤
                    │  6. Swagger Disabled │  ← Produção
                    └─────────────────────┘
```

## 2. API Key Authentication

### Especificação

| Aspecto | Valor |
|---------|-------|
| **Header** | `X-C2F-API-Key` |
| **Variável** | `C2F_API_KEY` |
| **Obrigatório em** | Produção (`APP_ENV=production`) |
| **Opcional em** | Desenvolvimento |
| **Onde aplicado** | Endpoints `POST /tasks/submit` e `GET /tasks/status/{id}` |
| **Não aplicado em** | `GET /health` |

### Regras de Validação

```
SE app_env == "production" E c2f_api_key != "":
  SE header X-C2F-API-Key ausente OU != c2f_api_key:
    → HTTP 401 {"detail": "Invalid or missing API key"}
  SE header X-C2F-API-Key == c2f_api_key:
    → Prossegue normalmente

SE app_env != "production":
  → Ignora autenticação (sempre prossegue)
```

### Implementação

```python
async def verify_api_key(
    x_c2f_api_key: str | None = Header(None),
    settings: Settings = Depends(get_settings),
) -> Settings:
```

Usa **FastAPI Dependency Injection** — aplicado via `Depends(verify_api_key)`.

## 3. HMAC-SHA256 (Webhook Signing)

### Especificação

| Aspecto | Valor |
|---------|-------|
| **Algoritmo** | HMAC-SHA256 |
| **Secret** | `C2F_WEBHOOK_SECRET` |
| **Input** | Body completo (bytes) |
| **Header de saída** | `X-C2F-Signature: sha256={hex_digest}` |

### Processo de Assinatura

```
1. Serializa o payload → body_bytes = orjson.dumps(payload)
2. Calcula HMAC:
   signature = hmac.new(
     key = secret.encode("utf-8"),
     msg = body_bytes,
     digestmod = sha256
   ).hexdigest()
3. Envia no header: X-C2F-Signature: sha256={signature}
```

### Verificação (lado Conn2Flow)

O receptor (Conn2Flow PHP) deve:

1. Ler o body raw do request
2. Ler o header `X-C2F-Signature`
3. Extrair o hash após `sha256=`
4. Calcular `hash_hmac('sha256', $body, $secret)`
5. Comparar com `hash_equals()` (timing-safe)

**Regra**: Se `C2F_WEBHOOK_SECRET` estiver vazio, a assinatura é uma string vazia.

## 4. CORS (Cross-Origin Resource Sharing)

| Ambiente | `allow_origins` | `allow_methods` | `allow_headers` | `allow_credentials` |
|----------|-----------------|-----------------|-----------------|---------------------|
| development | `["*"]` | `["*"]` | `["*"]` | `True` |
| production | `[]` | `["*"]` | `["*"]` | `True` |

**Regra**: Em produção, CORS é bloqueado (`allow_origins=[]`). Isso porque o Nexus AI é um serviço backend-to-backend, não acessado por browsers.

## 5. Input Validation (Pydantic)

Toda entrada é validada automaticamente pelo Pydantic v2:

| Campo | Validação |
|-------|-----------|
| `messages` | `min_length=1` — deve ter pelo menos 1 mensagem |
| `temperature` | `ge=0.0, le=2.0` — entre 0 e 2 |
| `max_tokens` | `gt=0, le=128000` — entre 1 e 128000 se presente |
| `model` | String livre (validação real pelo LiteLLM) |

**Regra**: Validação Pydantic rejeita com HTTP 422 e detalhes do erro.

## 6. Swagger/OpenAPI

| Ambiente | `/docs` (Swagger) | `/redoc` (ReDoc) |
|----------|-------------------|-------------------|
| development | ✅ Habilitado | ✅ Habilitado |
| production | ❌ `None` | ❌ `None` |

**Regra**: Baseado em `APP_DEBUG`:
```python
docs_url="/docs" if settings.app_debug else None
redoc_url="/redoc" if settings.app_debug else None
```

## 7. Docker Security

| Medida | Implementação |
|--------|---------------|
| **Non-root user** | `addgroup --system c2f && adduser --system --ingroup c2f c2f` |
| **USER directive** | `USER c2f` no Dockerfile |
| **No .pyc files** | `PYTHONDONTWRITEBYTECODE=1` |
| **Minimal base** | `python:3.11-slim` (sem extras desnecessários) |
| **Multi-stage** | Dependências de build não vão para a imagem final |

## 8. Secrets Management

| Secret | Onde configurada | Formato |
|--------|-----------------|---------|
| `C2F_API_KEY` | `.env` / variável de ambiente | String |
| `C2F_WEBHOOK_SECRET` | `.env` / variável de ambiente | String |
| `OPENAI_API_KEY` | `.env` / variável de ambiente | String |
| `ANTHROPIC_API_KEY` | `.env` / variável de ambiente | String |
| `GEMINI_API_KEY` | `.env` / variável de ambiente | String |
| `GROQ_API_KEY` | `.env` / variável de ambiente | String |

**Regras**:
- Nunca commitar `.env` com valores reais (usar `.env.example`)
- `.env` está no `.gitignore`
- Em produção, usar Docker secrets ou variáveis do orquestrador

## 9. Validação de LLM Keys em Produção

```python
@model_validator(mode="after")
def _warn_missing_keys(self) -> "Settings":
    has_any = any([openai_api_key, anthropic_api_key, gemini_api_key, groq_api_key])
    if not has_any and self.is_production:
        raise ValueError("At least one LLM API key must be set in production")
```

**Regra**: Em produção, a aplicação se recusa a iniciar se nenhuma API key de LLM estiver configurada.

## 10. Threat Model (Resumo)

| Ameaça | Mitigação |
|--------|-----------|
| Acesso não autorizado à API | API Key header |
| Webhook spoofing | HMAC-SHA256 signing |
| CSRF via browser | CORS bloqueado em produção |
| Injeção de dados maliciosos | Validação Pydantic rigorosa |
| Privilege escalation no container | Non-root user |
| Exposição de endpoints internos | Swagger desabilitado em produção |
| API keys em logs | LiteLLM verbose desabilitado |
| Startup sem configuração | Validação de keys na inicialização |
