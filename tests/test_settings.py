"""
Tests for settings.py (pydantic-settings).
"""

import pytest

from src.config.settings import Settings


class TestSettings:

    def test_defaults(self):
        s = Settings()
        assert s.app_name == "conn2flow-nexus-ai"
        assert s.api_port == 8000
        assert s.kafka_topic_incoming == "c2f_incoming_tasks"
        assert s.kafka_topic_completed == "c2f_completed_tasks"

    def test_is_production(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-prod-key")
        s = Settings()
        assert s.is_production is True

    def test_production_requires_api_key(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        with pytest.raises(Exception, match="LLM API key"):
            Settings()

    def test_debug_mode(self, monkeypatch):
        monkeypatch.setenv("APP_DEBUG", "true")
        s = Settings()
        assert s.app_debug is True

    def test_custom_kafka_bootstrap(self, monkeypatch):
        monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "custom-kafka:19092")
        s = Settings()
        assert s.kafka_bootstrap_servers == "custom-kafka:19092"
