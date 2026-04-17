# 6. LiteLLM — Multi-Provider LLM Router

## O Que É LiteLLM?

**LiteLLM** é uma biblioteca que fornece uma **API unificada** para chamar mais de 100 modelos de IA de diferentes provedores:

```python
# Mesma interface para QUALQUER provedor:
response = await litellm.acompletion(
    model="gpt-4o",              # OpenAI
    messages=[{"role": "user", "content": "Olá"}],
)
response = await litellm.acompletion(
    model="claude-3-5-sonnet",   # Anthropic (mesma interface!)
    messages=[{"role": "user", "content": "Olá"}],
)
```

### Por que LiteLLM em vez de chamar APIs diretamente?

| Sem LiteLLM | Com LiteLLM |
|-------------|-------------|
| SDK diferente para cada provedor | Uma única função `acompletion()` |
| Formatos de resposta diferentes | Formato unificado (estilo OpenAI) |
| Retry manual em cada integração | Retry automático built-in |
| Fallback manual | Fallback declarativo |
| Tracking de custos manual | Cost tracking automático |

---

## Implementação: `src/core/llm_router.py`

### Configuração Global

```python
litellm.drop_params = True    # Ignora params não suportados pelo modelo
litellm.set_verbose = False   # Silencia logs internos do LiteLLM
```

**Conceito: `drop_params`**
- Cada modelo suporta parâmetros diferentes (ex: `temperature` existe em todos, mas `top_k` não)
- `drop_params=True` faz o LiteLLM ignorar parâmetros não suportados em vez de dar erro
- Permite usar a mesma chamada para qualquer modelo

### Mapa de Fallback

```python
FALLBACK_MAP: dict[str, list[str]] = {
    "gpt-4o":                       ["gpt-4o-mini", "claude-3-5-sonnet-20241022"],
    "gpt-4o-mini":                  ["gpt-4o", "claude-3-5-haiku-20241022"],
    "claude-3-5-sonnet-20241022":   ["gpt-4o", "gemini/gemini-2.0-flash"],
    "claude-3-5-haiku-20241022":    ["gpt-4o-mini", "gemini/gemini-2.0-flash"],
    "gemini/gemini-2.0-flash":      ["gpt-4o-mini", "claude-3-5-haiku-20241022"],
}
```

**Conceito: Fallback Chain**
- Se `gpt-4o` falhar (timeout, rate limit, erro), LiteLLM tenta automaticamente:
  1. `gpt-4o-mini` (mesmo provedor, modelo menor)
  2. `claude-3-5-sonnet` (provedor diferente!)
- Isso garante **alta disponibilidade** — mesmo se a OpenAI cair, a Anthropic responde

### Injeção de API Keys

```python
def _configure_api_keys() -> None:
    settings = get_settings()
    key_map = {
        "OPENAI_API_KEY": settings.openai_api_key,
        "ANTHROPIC_API_KEY": settings.anthropic_api_key,
        "GEMINI_API_KEY": settings.gemini_api_key,
        "GROQ_API_KEY": settings.groq_api_key,
    }
    for env_var, value in key_map.items():
        if value:
            os.environ[env_var] = value
```

**Por que injetar em `os.environ`?**
- LiteLLM lê API keys das variáveis de ambiente automaticamente
- `OPENAI_API_KEY` → usado para `gpt-4o`, `gpt-4o-mini`
- `ANTHROPIC_API_KEY` → usado para `claude-*`
- Ao centralizar no `settings.py`, evitamos ter keys espalhadas pelo código

### Chamada LLM Assíncrona

```python
async def call_llm(
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    _configure_api_keys()

    fallbacks = FALLBACK_MAP.get(model, [])

    response = await litellm.acompletion(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        num_retries=2,                              # Tenta 2x antes de falhar
        fallbacks=fallbacks if fallbacks else None,  # Modelos alternativos
        timeout=120,                                 # 2 minutos de timeout
        **kwargs,
    )
```

**Conceito: `await litellm.acompletion()`**
- `acompletion` = **async** completion (assíncrono)
- `await` pausa a execução desta coroutine sem bloquear o event loop
- Enquanto espera a resposta da API, outras tasks podem ser processadas

**Conceito: `**kwargs` (Keyword Arguments)**
- Permite passar parâmetros extras que não foram explicitamente definidos
- Útil para funcionalidades específicas de certos modelos (ex: `tools`, `response_format`)
- São repassados diretamente para o `litellm.acompletion()`

### Formato de Resposta

```python
choice = response.choices[0]
usage = response.usage

result = {
    "content": choice.message.content or "",
    "model_used": response.model or model,
    "usage": {
        "prompt_tokens": getattr(usage, "prompt_tokens", 0),
        "completion_tokens": getattr(usage, "completion_tokens", 0),
        "total_tokens": getattr(usage, "total_tokens", 0),
    },
    "finish_reason": choice.finish_reason or "stop",
}
```

**Conceito: Formato OpenAI Chat Completion**
- LiteLLM normaliza **todas** as respostas para o formato OpenAI:
  - `choices[0].message.content` → texto gerado
  - `usage.total_tokens` → total de tokens consumidos
  - `finish_reason` → `"stop"` (concluiu), `"length"` (atingiu max_tokens)

**Conceito: `getattr(obj, attr, default)`**
- Acessa um atributo de um objeto com valor default se não existir
- `getattr(usage, "prompt_tokens", 0)` → retorna `usage.prompt_tokens` ou `0` se não existir
- Mais seguro que `usage.prompt_tokens` que lançaria `AttributeError`

### Tratamento de Erros Específicos

```python
except litellm.AuthenticationError:
    logger.error("LLM authentication failed for model=%s", model)
    raise
except litellm.RateLimitError:
    logger.warning("LLM rate limited for model=%s", model)
    raise
```

**Conceito: Exceções Tipadas**
- `AuthenticationError` → API key inválida ou expirada
- `RateLimitError` → muitas requests por minuto
- Cada tipo de erro tem um log diferente para facilitar debugging
- `raise` sem argumento re-lança a exceção original (preserva stack trace)

---

## Fluxo da Chamada LLM

```
call_llm("gpt-4o", messages)
    │
    ├─ _configure_api_keys()         # Injeta keys no os.environ
    │
    ├─ litellm.acompletion()
    │     │
    │     ├─ Tenta gpt-4o ─── ✓ Sucesso → retorna resultado
    │     │
    │     ├─ Tenta gpt-4o ─── ✗ Falha → retry 1
    │     ├─ Tenta gpt-4o ─── ✗ Falha → retry 2
    │     │
    │     ├─ Fallback: gpt-4o-mini ── ✓ Sucesso → retorna resultado
    │     │
    │     └─ Fallback: claude-3-5-sonnet ── ✓ Sucesso → retorna resultado
    │
    └─ Formata resposta → {content, model_used, usage, finish_reason}
```

---

## Anterior: [← Redis](05-redis.md) | Próximo: [LangGraph →](07-langgraph.md)
