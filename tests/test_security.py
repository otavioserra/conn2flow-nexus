"""
Focused security contract tests.
"""

import pytest

from fastapi import HTTPException, status

from src.api.endpoints.tasks import verify_api_key
from src.config.settings import Settings


class TestVerifyApiKey:

    @pytest.mark.asyncio
    async def test_accepts_matching_key_in_production(self):
        settings = Settings(
            app_env="production",
            c2f_api_key="expected-key",
            openai_api_key="sk-test-key",
        )

        result = await verify_api_key("expected-key", settings)

        assert result is settings

    @pytest.mark.asyncio
    async def test_rejects_missing_key_in_production(self):
        settings = Settings(
            app_env="production",
            c2f_api_key="expected-key",
            openai_api_key="sk-test-key",
        )

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(None, settings)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid or missing API key"

    @pytest.mark.asyncio
    async def test_rejects_invalid_key_in_production(self):
        settings = Settings(
            app_env="production",
            c2f_api_key="expected-key",
            openai_api_key="sk-test-key",
        )

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key("wrong-key", settings)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid or missing API key"

    @pytest.mark.asyncio
    async def test_bypasses_authentication_outside_production(self):
        settings = Settings(
            app_env="development",
            c2f_api_key="expected-key",
        )

        result = await verify_api_key(None, settings)

        assert result is settings

    @pytest.mark.asyncio
    async def test_bypasses_authentication_when_no_key_is_configured(self):
        settings = Settings(
            app_env="production",
            c2f_api_key="",
            openai_api_key="sk-test-key",
        )

        result = await verify_api_key(None, settings)

        assert result is settings