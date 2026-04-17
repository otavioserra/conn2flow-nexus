"""
Conn2Flow Nexus AI - Multi-Model LLM Router
Uses LiteLLM to dynamically route between AI providers.
Supports fallback, automatic retry and cost tracking.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import litellm

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

# LiteLLM: silence verbose messages, use drop_params mode
litellm.drop_params = True
litellm.set_verbose = False

# Fallback map: if the primary model fails, try the next one
FALLBACK_MAP: dict[str, list[str]] = {
    "gpt-4o": ["gpt-4o-mini", "claude-3-5-sonnet-20241022"],
    "gpt-4o-mini": ["gpt-4o", "claude-3-5-haiku-20241022"],
    "claude-3-5-sonnet-20241022": ["gpt-4o", "gemini/gemini-2.0-flash"],
    "claude-3-5-haiku-20241022": ["gpt-4o-mini", "gemini/gemini-2.0-flash"],
    "gemini/gemini-2.0-flash": ["gpt-4o-mini", "claude-3-5-haiku-20241022"],
}


def _configure_api_keys() -> None:
    """Injects API keys from settings into environment variables (required by LiteLLM)."""
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


async def call_llm(
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Executes an async LLM call with automatic fallback.

    Returns:
        Dict with fields: content, model_used, usage, finish_reason
    """
    _configure_api_keys()

    # Build LiteLLM fallbacks
    fallbacks = FALLBACK_MAP.get(model, [])

    try:
        response = await litellm.acompletion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            num_retries=2,
            fallbacks=fallbacks if fallbacks else None,
            timeout=120,
            **kwargs,
        )

        choice = response.choices[0]
        usage = response.usage if response.usage else {}

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

        logger.info(
            "LLM call successful — model=%s tokens=%d",
            result["model_used"],
            result["usage"]["total_tokens"],
        )
        return result

    except litellm.AuthenticationError:
        logger.error("LLM authentication failed for model=%s", model)
        raise
    except litellm.RateLimitError:
        logger.warning("LLM rate limited for model=%s", model)
        raise
    except Exception:
        logger.exception("LLM call failed — model=%s", model)
        raise
