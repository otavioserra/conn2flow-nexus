"""
Focused delivery worker contract tests.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import orjson
import pytest

from src.config.settings import Settings
from src.workers.delivery_worker import DeliveryWorker, MAX_RETRIES, _sign_payload


def _make_settings() -> Settings:
    return Settings(
        app_env="development",
        c2f_webhook_secret="test-secret",
        kafka_bootstrap_servers="localhost:9092",
        kafka_topic_completed="c2f_completed_tasks",
    )


def _make_worker() -> DeliveryWorker:
    return DeliveryWorker(topic="c2f_completed_tasks", settings=_make_settings())


def _mock_async_client(post_result) -> MagicMock:
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=post_result)

    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_client)
    mock_context.__aexit__ = AsyncMock(return_value=None)

    return mock_context


class TestDeliveryWorker:

    @pytest.mark.asyncio
    async def test_skips_delivery_when_webhook_url_is_missing(self):
        worker = _make_worker()

        with (
            patch("src.workers.delivery_worker.httpx.AsyncClient") as mock_client_cls,
            patch("src.workers.delivery_worker.incr_metric", new_callable=AsyncMock) as mock_incr_metric,
            patch("src.workers.delivery_worker.set_task_status", new_callable=AsyncMock) as mock_set_task_status,
        ):
            await worker.process_message({"task_id": "task-1", "status": "completed"})

        mock_client_cls.assert_not_called()
        mock_incr_metric.assert_not_awaited()
        mock_set_task_status.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_delivers_payload_with_signature_header(self):
        worker = _make_worker()
        payload = {
            "task_id": "task-2",
            "status": "completed",
            "webhook_url": "https://example.test/webhook",
            "result": {"content": "done"},
        }
        body_bytes = orjson.dumps(payload)
        expected_signature = _sign_payload(body_bytes, "test-secret")
        response = MagicMock(status_code=200, text="ok")
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=response)
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with (
            patch(
                "src.workers.delivery_worker.httpx.AsyncClient",
                return_value=mock_context,
            ),
            patch("src.workers.delivery_worker.incr_metric", new_callable=AsyncMock) as mock_incr_metric,
            patch("src.workers.delivery_worker.set_task_status", new_callable=AsyncMock) as mock_set_task_status,
        ):
            await worker.process_message(payload)

        mock_incr_metric.assert_awaited_once_with("webhooks_delivered")
        mock_set_task_status.assert_not_awaited()
        mock_client.post.assert_awaited_once()

        post_call = mock_client.post.await_args
        assert post_call.args[0] == "https://example.test/webhook"
        assert post_call.kwargs["content"] == body_bytes
        assert post_call.kwargs["headers"]["X-C2F-Task-ID"] == "task-2"
        assert (
            post_call.kwargs["headers"]["X-C2F-Signature"]
            == f"sha256={expected_signature}"
        )

    @pytest.mark.asyncio
    async def test_marks_delivery_failed_after_retries(self):
        worker = _make_worker()
        payload = {
            "task_id": "task-3",
            "status": "completed",
            "webhook_url": "https://example.test/webhook",
        }
        response = MagicMock(status_code=500, text="server error")
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=[response] * MAX_RETRIES)
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_client)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("src.workers.delivery_worker.httpx.AsyncClient", return_value=mock_context),
            patch("src.workers.delivery_worker.asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
            patch("src.workers.delivery_worker.incr_metric", new_callable=AsyncMock) as mock_incr_metric,
            patch("src.workers.delivery_worker.set_task_status", new_callable=AsyncMock) as mock_set_task_status,
        ):
            await worker.process_message(payload)

        assert mock_client.post.await_count == MAX_RETRIES
        assert mock_sleep.await_count == MAX_RETRIES - 1
        mock_set_task_status.assert_awaited_once()
        mock_incr_metric.assert_awaited_once_with("webhooks_failed")

        task_status_call = mock_set_task_status.await_args
        assert task_status_call.args[0] == "task-3"
        assert task_status_call.args[1] == "delivery_failed"
        assert "HTTP 500" in task_status_call.args[2]["error"]