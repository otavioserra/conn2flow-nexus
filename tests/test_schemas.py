"""
Tests for Pydantic schemas (requests and responses).
"""

import pytest
from pydantic import ValidationError

from src.api.schemas.requests import TaskRequest
from src.api.schemas.responses import TaskAcceptedResponse, TaskStatusResponse
from src.models.events import TaskEvent, TaskResultEvent


# ---------------------------------------------------------------------------
# TaskRequest
# ---------------------------------------------------------------------------

class TestTaskRequest:

    def test_valid_minimal(self):
        req = TaskRequest(messages=[{"role": "user", "content": "Hello"}])
        assert req.model == "gpt-4o-mini"
        assert req.temperature == 0.7
        assert req.max_tokens is None
        assert req.stream is False

    def test_valid_full(self):
        req = TaskRequest(
            model="claude-3-5-sonnet-20241022",
            messages=[
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "Hi"},
            ],
            temperature=0.3,
            max_tokens=1000,
            webhook_url="https://example.com/callback",
            metadata={"project_id": "123"},
            stream=True,
        )
        assert req.model == "claude-3-5-sonnet-20241022"
        assert req.temperature == 0.3
        assert req.max_tokens == 1000
        assert req.stream is True
        assert req.metadata["project_id"] == "123"

    def test_empty_messages_fails(self):
        with pytest.raises(ValidationError):
            TaskRequest(messages=[])

    def test_temperature_out_of_range(self):
        with pytest.raises(ValidationError):
            TaskRequest(
                messages=[{"role": "user", "content": "Hi"}],
                temperature=3.0,
            )

    def test_max_tokens_negative_fails(self):
        with pytest.raises(ValidationError):
            TaskRequest(
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=-1,
            )


# ---------------------------------------------------------------------------
# TaskAcceptedResponse
# ---------------------------------------------------------------------------

class TestTaskAcceptedResponse:

    def test_defaults(self):
        resp = TaskAcceptedResponse(task_id="abc-123")
        assert resp.status == "queued"
        assert "processing" in resp.message


# ---------------------------------------------------------------------------
# TaskStatusResponse
# ---------------------------------------------------------------------------

class TestTaskStatusResponse:

    def test_completed(self):
        resp = TaskStatusResponse(
            task_id="t1",
            status="completed",
            result={"content": "Hello!"},
        )
        assert resp.result["content"] == "Hello!"
        assert resp.error is None

    def test_failed(self):
        resp = TaskStatusResponse(
            task_id="t1",
            status="failed",
            error="LLM timeout",
        )
        assert resp.error == "LLM timeout"
        assert resp.result is None


# ---------------------------------------------------------------------------
# TaskEvent (Kafka)
# ---------------------------------------------------------------------------

class TestTaskEvent:

    def test_serialization(self):
        event = TaskEvent(
            task_id="t1",
            model="gpt-4o",
            messages=[{"role": "user", "content": "Test"}],
        )
        data = event.model_dump(mode="json")
        assert data["task_id"] == "t1"
        assert "created_at" in data

    def test_defaults(self):
        event = TaskEvent(
            task_id="t1",
            model="gpt-4o",
            messages=[{"role": "user", "content": "Test"}],
        )
        assert event.temperature == 0.7
        assert event.stream is False


# ---------------------------------------------------------------------------
# TaskResultEvent (Kafka)
# ---------------------------------------------------------------------------

class TestTaskResultEvent:

    def test_completed_event(self):
        event = TaskResultEvent(
            task_id="t1",
            status="completed",
            model="gpt-4o",
            result={"content": "Response text"},
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        )
        assert event.status == "completed"
        assert event.usage["total_tokens"] == 30

    def test_failed_event(self):
        event = TaskResultEvent(
            task_id="t1",
            status="failed",
            model="gpt-4o",
            error="API timeout",
        )
        assert event.error == "API timeout"
        assert event.result is None
