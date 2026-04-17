"""
Conn2Flow Nexus AI - Kafka Event Models
Pydantic models representing events flowing through Kafka.
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class TaskEvent(BaseModel):
    """Event published to the c2f_incoming_tasks topic."""

    task_id: str
    model: str
    messages: list[dict[str, str]]
    temperature: float = 0.7
    max_tokens: int | None = None
    webhook_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    stream: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TaskResultEvent(BaseModel):
    """Event published to the c2f_completed_tasks topic."""

    task_id: str
    status: str = Field(description="completed | failed")
    model: str
    result: dict[str, Any] | None = None
    error: str | None = None
    webhook_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    usage: dict[str, int] | None = Field(
        default=None,
        description="Token usage: {prompt_tokens, completion_tokens, total_tokens}",
    )
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
