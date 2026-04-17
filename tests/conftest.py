"""
Shared fixtures for tests.
"""

import os

import pytest


@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch):
    """Sets environment variables for testing."""
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_DEBUG", "true")
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("C2F_API_KEY", "test-api-key")
    monkeypatch.setenv("C2F_WEBHOOK_URL", "http://localhost:8080/webhook")
    monkeypatch.setenv("C2F_WEBHOOK_SECRET", "test-secret")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("DEFAULT_MODEL", "gpt-4o-mini")
