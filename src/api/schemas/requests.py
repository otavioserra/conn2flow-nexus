"""
Conn2Flow Nexus AI - Request Schemas
Strict data contracts (Pydantic v2) for incoming requests.
"""

from typing import Any

from pydantic import BaseModel, Field


class TaskRequest(BaseModel):
    """Payload sent by Conn2Flow to process an AI task."""

    model: str = Field(
        default="gpt-4o-mini",
        description="LLM model identifier (e.g., gpt-4o, claude-3-5-sonnet, gemini-2.0-flash)",
        examples=["gpt-4o", "claude-3-5-sonnet", "gemini-2.0-flash", "llama-3.1-70b"],
    )
    messages: list[dict[str, str]] = Field(
        ...,
        description="List of messages in OpenAI format [{role, content}]",
        min_length=1,
        examples=[[{"role": "user", "content": "Hello, how can I help you?"}]],
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Model sampling temperature",
    )
    max_tokens: int | None = Field(
        default=None,
        gt=0,
        le=128000,
        description="Maximum number of tokens in the response",
    )
    webhook_url: str | None = Field(
        default=None,
        description="Callback URL to deliver the result (overrides default)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Free-form metadata that will be returned with the response",
    )
    stream: bool = Field(
        default=False,
        description="If True, chunks will be sent via streaming to the webhook",
    )
