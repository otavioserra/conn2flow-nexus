# SPEC-05: LLM Routing

> **Status**: ✅ Approved
> **Version**: 1.0.0
> **Created**: 2025-07-16
> **Last updated**: 2025-07-16

---

## 1. Overview

The LLM Router is the layer that abstracts communication with multiple AI providers. It uses **LiteLLM** as the abstraction library, providing:

- Unified interface for all providers
- Automatic fallback between models
- Built-in retry
- Unsupported parameter dropping

## 2. Supported Providers

| Provider | Environment Variable | Example Models |
|----------|---------------------|----------------|
| OpenAI | `OPENAI_API_KEY` | `gpt-4o`, `gpt-4o-mini` |
| Anthropic | `ANTHROPIC_API_KEY` | `claude-3-5-sonnet-20241022`, `claude-3-5-haiku-20241022` |
| Google Gemini | `GEMINI_API_KEY` | `gemini/gemini-2.0-flash` |
| Groq | `GROQ_API_KEY` | `groq/llama-3.1-70b-versatile` |

**Rule**: The provider is automatically determined by LiteLLM based on the model prefix. Gemini models use the `gemini/` prefix, Groq uses `groq/`.

## 3. Fallback Map

When the primary model fails, the system automatically tries alternative models in the defined order:

| Primary Model | Fallback 1 | Fallback 2 |
|--------------|------------|------------|
| `gpt-4o` | `gpt-4o-mini` | `claude-3-5-sonnet-20241022` |
| `gpt-4o-mini` | `gpt-4o` | `claude-3-5-haiku-20241022` |
| `claude-3-5-sonnet-20241022` | `gpt-4o` | `gemini/gemini-2.0-flash` |
| `claude-3-5-haiku-20241022` | `gpt-4o-mini` | `gemini/gemini-2.0-flash` |
| `gemini/gemini-2.0-flash` | `gpt-4o-mini` | `claude-3-5-haiku-20241022` |

**Rule**: If the model is not in the fallback map, no fallback is attempted. The call fails immediately after the primary model's retries.

## 4. LiteLLM Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `drop_params` | `True` | Ignores unsupported model parameters |
| `set_verbose` | `False` | Disables verbose LiteLLM logs |
| `num_retries` | `2` | Tries 2 times before failing/fallback |
| `timeout` | `120` (seconds) | Timeout per LLM call |

## 5. `call_llm()` Function Interface

### Signature

```python
async def call_llm(
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int | None = None,
    **kwargs: Any,
) -> dict[str, Any]
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | `str` | Yes | LLM model identifier |
| `messages` | `list[dict]` | Yes | Messages in OpenAI format |
| `temperature` | `float` | No | Sampling temperature |
| `max_tokens` | `int \| None` | No | Response token limit |
| `**kwargs` | `Any` | No | Additional parameters passed to LiteLLM |

### Return (Success)

```python
{
    "content": "Hello! How can I help you?",
    "model_used": "gpt-4o-mini",
    "usage": {
        "prompt_tokens": 25,
        "completion_tokens": 10,
        "total_tokens": 35
    },
    "finish_reason": "stop"
}
```

### Exceptions

| Exception | When | Re-raise |
|-----------|------|----------|
| `litellm.AuthenticationError` | Invalid API key | Yes |
| `litellm.RateLimitError` | Rate limit exceeded | Yes (after retries) |
| `litellm.Timeout` | Call timeout | Yes (after retries) |
| `Exception` | Any other error | Yes |

## 6. API Key Injection

API keys are injected into environment variables at call time:

```python
settings → os.environ["OPENAI_API_KEY"]
settings → os.environ["ANTHROPIC_API_KEY"]
settings → os.environ["GEMINI_API_KEY"]
settings → os.environ["GROQ_API_KEY"]
```

**Rule**: Only non-empty keys are injected. Empty keys are ignored.

## 7. Execution Flow

```
call_llm(model="gpt-4o", messages=[...])
  │
  ├─ _configure_api_keys()          # Inject keys into os.environ
  │
  ├─ fallbacks = FALLBACK_MAP["gpt-4o"]  # ["gpt-4o-mini", "claude-3-5-sonnet"]
  │
  ├─ litellm.acompletion(
  │      model="gpt-4o",
  │      messages=[...],
  │      fallbacks=["gpt-4o-mini", "claude-3-5-sonnet"],
  │      num_retries=2,
  │      timeout=120
  │  )
  │
  ├─ [SUCCESS] → extract content, usage, finish_reason → return dict
  │
  └─ [FAILURE] → litellm tries fallbacks → [SUCCESS] return dict
                                          → [TOTAL FAILURE] raise Exception
```

## 8. Default Model

| Property | Value |
|----------|-------|
| **Variable** | `DEFAULT_MODEL` |
| **Default** | `gpt-4o-mini` |
| **Used when** | Client does not specify `model` in `TaskRequest` |
