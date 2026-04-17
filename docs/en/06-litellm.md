# 6. LiteLLM — Multi-Provider LLM Router

## What Is LiteLLM?

**LiteLLM** is a library that provides a **unified API** for calling over 100 AI models from different providers:

```python
# Same interface for ANY provider:
response = await litellm.acompletion(
    model="gpt-4o",              # OpenAI
    messages=[{"role": "user", "content": "Hello"}],
)
response = await litellm.acompletion(
    model="claude-3-5-sonnet",   # Anthropic (same interface!)
    messages=[{"role": "user", "content": "Hello"}],
)
```

### Why LiteLLM Instead of Calling APIs Directly?

| Without LiteLLM | With LiteLLM |
|-----------------|--------------|
| Different SDK for each provider | A single `acompletion()` function |
| Different response formats | Unified format (OpenAI-style) |
| Manual retry for each integration | Built-in automatic retry |
| Manual fallback | Declarative fallback |
| Manual cost tracking | Automatic cost tracking |

---

## Implementation: `src/core/llm_router.py`

### Global Configuration

```python
litellm.drop_params = True    # Ignores unsupported params for the model
litellm.set_verbose = False   # Silences internal LiteLLM logs
```

**Concept: `drop_params`**
- Each model supports different parameters (e.g., `temperature` exists in all, but `top_k` doesn't)
- `drop_params=True` makes LiteLLM ignore unsupported parameters instead of throwing errors
- Allows using the same call for any model

### Fallback Map

```python
FALLBACK_MAP: dict[str, list[str]] = {
    "gpt-4o":                       ["gpt-4o-mini", "claude-3-5-sonnet-20241022"],
    "gpt-4o-mini":                  ["gpt-4o", "claude-3-5-haiku-20241022"],
    "claude-3-5-sonnet-20241022":   ["gpt-4o", "gemini/gemini-2.0-flash"],
    "claude-3-5-haiku-20241022":    ["gpt-4o-mini", "gemini/gemini-2.0-flash"],
    "gemini/gemini-2.0-flash":      ["gpt-4o-mini", "claude-3-5-haiku-20241022"],
}
```

**Concept: Fallback Chain**
- If `gpt-4o` fails (timeout, rate limit, error), LiteLLM automatically tries:
  1. `gpt-4o-mini` (same provider, smaller model)
  2. `claude-3-5-sonnet` (different provider!)
- This ensures **high availability** — even if OpenAI goes down, Anthropic responds

### API Key Injection

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

**Why inject into `os.environ`?**
- LiteLLM reads API keys from environment variables automatically
- `OPENAI_API_KEY` → used for `gpt-4o`, `gpt-4o-mini`
- `ANTHROPIC_API_KEY` → used for `claude-*`
- By centralizing in `settings.py`, we avoid having keys scattered throughout the code

### Async LLM Call

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
        num_retries=2,                              # Tries 2x before failing
        fallbacks=fallbacks if fallbacks else None,  # Alternative models
        timeout=120,                                 # 2-minute timeout
        **kwargs,
    )
```

**Concept: `await litellm.acompletion()`**
- `acompletion` = **async** completion (asynchronous)
- `await` pauses execution of this coroutine without blocking the event loop
- While waiting for the API response, other tasks can be processed

**Concept: `**kwargs` (Keyword Arguments)**
- Allows passing extra parameters that were not explicitly defined
- Useful for model-specific features (e.g., `tools`, `response_format`)
- Passed directly to `litellm.acompletion()`

### Response Format

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

**Concept: OpenAI Chat Completion Format**
- LiteLLM normalizes **all** responses to the OpenAI format:
  - `choices[0].message.content` → generated text
  - `usage.total_tokens` → total tokens consumed
  - `finish_reason` → `"stop"` (completed), `"length"` (hit max_tokens)

**Concept: `getattr(obj, attr, default)`**
- Accesses an object attribute with a default value if it doesn't exist
- `getattr(usage, "prompt_tokens", 0)` → returns `usage.prompt_tokens` or `0` if it doesn't exist
- Safer than `usage.prompt_tokens` which would raise `AttributeError`

### Specific Error Handling

```python
except litellm.AuthenticationError:
    logger.error("LLM authentication failed for model=%s", model)
    raise
except litellm.RateLimitError:
    logger.warning("LLM rate limited for model=%s", model)
    raise
```

**Concept: Typed Exceptions**
- `AuthenticationError` → invalid or expired API key
- `RateLimitError` → too many requests per minute
- Each error type has a different log for easier debugging
- `raise` without argument re-raises the original exception (preserves stack trace)

---

## LLM Call Flow

```
call_llm("gpt-4o", messages)
    │
    ├─ _configure_api_keys()         # Injects keys into os.environ
    │
    ├─ litellm.acompletion()
    │     │
    │     ├─ Try gpt-4o ─── ✓ Success → return result
    │     │
    │     ├─ Try gpt-4o ─── ✗ Fail → retry 1
    │     ├─ Try gpt-4o ─── ✗ Fail → retry 2
    │     │
    │     ├─ Fallback: gpt-4o-mini ── ✓ Success → return result
    │     │
    │     └─ Fallback: claude-3-5-sonnet ── ✓ Success → return result
    │
    └─ Format response → {content, model_used, usage, finish_reason}
```

---

## Previous: [← Redis](05-redis.md) | Next: [LangGraph →](07-langgraph.md)
