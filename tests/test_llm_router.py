"""
Tests for the LLM Router (litellm wrapper).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestLLMRouter:

    @pytest.mark.asyncio
    @patch("src.core.llm_router.litellm")
    async def test_call_llm_success(self, mock_litellm):
        from src.core.llm_router import call_llm

        # Mock LiteLLM response
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20
        mock_usage.total_tokens = 30

        mock_choice = MagicMock()
        mock_choice.message.content = "Simulated response"
        mock_choice.finish_reason = "stop"

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.model = "gpt-4o-mini"
        mock_response.usage = mock_usage

        mock_litellm.acompletion = AsyncMock(return_value=mock_response)

        result = await call_llm(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.5,
        )

        assert result["content"] == "Simulated response"
        assert result["model_used"] == "gpt-4o-mini"
        assert result["usage"]["total_tokens"] == 30
        assert result["finish_reason"] == "stop"

    @pytest.mark.asyncio
    @patch("src.core.llm_router.litellm")
    async def test_call_llm_with_fallback_map(self, mock_litellm):
        from src.core.llm_router import FALLBACK_MAP

        # Verify that primary models have defined fallbacks
        assert "gpt-4o" in FALLBACK_MAP
        assert "claude-3-5-sonnet-20241022" in FALLBACK_MAP
        assert len(FALLBACK_MAP["gpt-4o"]) >= 2


class TestWebhookSignature:

    def test_hmac_signature(self):
        from src.workers.delivery_worker import _sign_payload

        payload = b'{"task_id": "test"}'
        secret = "my-secret"
        sig = _sign_payload(payload, secret)

        assert isinstance(sig, str)
        assert len(sig) == 64  # SHA256 hex digest

    def test_signature_consistency(self):
        from src.workers.delivery_worker import _sign_payload

        payload = b'{"data": "same"}'
        s1 = _sign_payload(payload, "secret")
        s2 = _sign_payload(payload, "secret")
        assert s1 == s2

    def test_different_secrets(self):
        from src.workers.delivery_worker import _sign_payload

        payload = b'{"data": "test"}'
        s1 = _sign_payload(payload, "secret1")
        s2 = _sign_payload(payload, "secret2")
        assert s1 != s2
