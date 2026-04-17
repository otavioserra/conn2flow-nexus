"""
Conn2Flow Nexus AI - Response Schemas
Data contracts for API responses.
"""

from typing import Any

from pydantic import BaseModel, Field


class TaskAcceptedResponse(BaseModel):
    """HTTP 202 response returned immediately after accepting the task."""

    task_id: str = Field(description="Unique task identifier")
    status: str = Field(default="queued", description="Current task status")
    message: str = Field(default="Task accepted for async processing")


class TaskStatusResponse(BaseModel):
    """Response with the current status of a task."""

    task_id: str
    status: str = Field(description="queued | processing | completed | failed")
    result: dict[str, Any] | None = Field(default=None, description="LLM result, if completed")
    error: str | None = Field(default=None, description="Error message, if failed")
    metadata: dict[str, Any] = Field(default_factory=dict)
