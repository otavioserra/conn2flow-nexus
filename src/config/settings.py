"""
Conn2Flow Nexus AI - Configuration
Centralizes all application settings using pydantic-settings.
Variables are loaded from .env automatically.
"""

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global settings for Conn2Flow Nexus AI."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "conn2flow-nexus-ai"
    app_env: str = "development"
    app_debug: bool = False
    app_version: str = "0.1.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    # --- API Security ---
    c2f_api_key: str = Field(
        default="",
        description="API key for authenticating requests from Conn2Flow",
    )

    # --- LLM Provider Keys ---
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    groq_api_key: str = ""

    # --- Default LLM ---
    default_model: str = "gpt-4o-mini"

    # --- Kafka ---
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_topic_incoming: str = "c2f_incoming_tasks"
    kafka_topic_completed: str = "c2f_completed_tasks"
    kafka_consumer_group: str = "c2f-workers"

    # --- Redis ---
    redis_url: str = "redis://redis:6379/0"

    # --- Webhook ---
    c2f_webhook_url: str = ""
    c2f_webhook_secret: str = ""

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @model_validator(mode="after")
    def _warn_missing_keys(self) -> "Settings":
        """Warns if no LLM API key is configured in production."""
        has_any = any([
            self.openai_api_key,
            self.anthropic_api_key,
            self.gemini_api_key,
            self.groq_api_key,
        ])
        if not has_any and self.is_production:
            raise ValueError(
                "At least one LLM API key must be set in production "
                "(OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY, GROQ_API_KEY)"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Returns the singleton settings instance."""
    return Settings()
