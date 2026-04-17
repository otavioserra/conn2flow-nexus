"""
Tests for the API (endpoints via TestClient).
"""

import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """TestClient with mocks for Kafka and Redis."""
    with (
        patch("src.main.start_redis", new_callable=AsyncMock),
        patch("src.main.stop_redis", new_callable=AsyncMock),
        patch("src.main.start_producer", new_callable=AsyncMock),
        patch("src.main.stop_producer", new_callable=AsyncMock),
    ):
        from src.main import app
        with TestClient(app) as c:
            yield c


class TestHealthEndpoint:

    def test_health_returns_200(self, client):
        with patch("src.core.redis_client.get_redis") as mock_redis:
            mock_r = AsyncMock()
            mock_r.ping = AsyncMock(return_value=True)
            mock_redis.return_value = mock_r
            resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "conn2flow-nexus-ai"
        assert "version" in data

    def test_health_degraded_when_redis_down(self, client):
        with patch("src.core.redis_client.get_redis", side_effect=RuntimeError("No redis")):
            resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "degraded"


class TestTaskSubmitEndpoint:

    @patch("src.api.endpoints.tasks.set_task_status", new_callable=AsyncMock)
    @patch("src.api.endpoints.tasks.send_event", new_callable=AsyncMock)
    def test_submit_returns_202(self, mock_send, mock_status, client):
        resp = client.post(
            "/api/v1/tasks/submit",
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )
        assert resp.status_code == 202
        data = resp.json()
        assert "task_id" in data
        assert data["status"] == "queued"
        mock_send.assert_called_once()
        mock_status.assert_called_once()

    @patch("src.api.endpoints.tasks.set_task_status", new_callable=AsyncMock)
    @patch("src.api.endpoints.tasks.send_event", new_callable=AsyncMock)
    def test_submit_invalid_payload(self, mock_send, mock_status, client):
        resp = client.post(
            "/api/v1/tasks/submit",
            json={"model": "gpt-4o", "messages": []},
        )
        assert resp.status_code == 422  # Validation error

    @patch("src.api.endpoints.tasks.set_task_status", new_callable=AsyncMock)
    @patch("src.api.endpoints.tasks.send_event", new_callable=AsyncMock)
    def test_submit_with_metadata(self, mock_send, mock_status, client):
        resp = client.post(
            "/api/v1/tasks/submit",
            json={
                "messages": [{"role": "user", "content": "Summarize this"}],
                "metadata": {"project": "conn2flow", "module": "reports"},
            },
        )
        assert resp.status_code == 202
        # Verify that the sent event contains metadata
        call_kwargs = mock_send.call_args
        assert call_kwargs is not None


class TestTaskStatusEndpoint:

    @patch("src.api.endpoints.tasks.get_task_status", new_callable=AsyncMock)
    def test_status_found(self, mock_get, client):
        mock_get.return_value = {
            "status": "completed",
            "result": {"content": "Response text"},
        }
        resp = client.get("/api/v1/tasks/status/fake-task-id")
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    @patch("src.api.endpoints.tasks.get_task_status", new_callable=AsyncMock)
    def test_status_not_found(self, mock_get, client):
        mock_get.return_value = None
        resp = client.get("/api/v1/tasks/status/nonexistent")
        assert resp.status_code == 404
