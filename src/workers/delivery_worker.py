"""
Conn2Flow Nexus AI - Delivery Worker
Kafka consumer that listens to c2f_completed_tasks
and dispatches Webhook POST back to Conn2Flow.
Payload is signed with HMAC-SHA256 via X-C2F-Signature header.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
from typing import Any

import httpx
import orjson

from src.config.settings import get_settings
from src.core.kafka_consumer import BaseKafkaConsumer
from src.core.redis_client import incr_metric, set_task_status, start_redis, stop_redis

logger = logging.getLogger(__name__)

MAX_RETRIES = 5
RETRY_BASE_DELAY = 2  # seconds


def _sign_payload(payload_bytes: bytes, secret: str) -> str:
    """Generates HMAC-SHA256 signature for the payload."""
    return hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()


class DeliveryWorker(BaseKafkaConsumer):
    """Consumes results from Kafka and sends via webhook to Conn2Flow."""

    async def process_message(self, payload: dict[str, Any]) -> None:
        task_id = payload.get("task_id", "unknown")
        webhook_url = payload.get("webhook_url")
        status = payload.get("status", "unknown")

        if not webhook_url:
            logger.warning(
                "[delivery] No webhook_url for task=%s — skipping delivery",
                task_id,
            )
            return

        logger.info("[delivery] Delivering task=%s status=%s → %s", task_id, status, webhook_url)

        # Serialize and sign the payload
        body_bytes = orjson.dumps(payload)
        secret = self.settings.c2f_webhook_secret
        signature = _sign_payload(body_bytes, secret) if secret else ""

        headers = {
            "Content-Type": "application/json",
            "X-C2F-Signature": f"sha256={signature}",
            "X-C2F-Task-ID": task_id,
            "User-Agent": "Conn2Flow-Nexus-AI/0.1",
        }

        # Retry with exponential backoff
        delivered = False
        last_error = ""

        async with httpx.AsyncClient(timeout=30) as client:
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    response = await client.post(
                        webhook_url,
                        content=body_bytes,
                        headers=headers,
                    )

                    if response.status_code < 300:
                        logger.info(
                            "[delivery] Task %s delivered — status_code=%d attempt=%d",
                            task_id,
                            response.status_code,
                            attempt,
                        )
                        delivered = True
                        await incr_metric("webhooks_delivered")
                        break

                    last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                    logger.warning(
                        "[delivery] Webhook non-2xx — task=%s status=%d attempt=%d",
                        task_id,
                        response.status_code,
                        attempt,
                    )

                except httpx.TimeoutException:
                    last_error = "Timeout"
                    logger.warning(
                        "[delivery] Webhook timeout — task=%s attempt=%d",
                        task_id,
                        attempt,
                    )
                except httpx.RequestError as exc:
                    last_error = str(exc)
                    logger.warning(
                        "[delivery] Webhook request error — task=%s attempt=%d error=%s",
                        task_id,
                        attempt,
                        exc,
                    )

                # Backoff exponencial: 2s, 4s, 8s, 16s, 32s
                if attempt < MAX_RETRIES:
                    delay = RETRY_BASE_DELAY ** attempt
                    logger.debug("[delivery] Retrying in %ds...", delay)
                    await asyncio.sleep(delay)

        if not delivered:
            logger.error(
                "[delivery] Failed to deliver task=%s after %d attempts — %s",
                task_id,
                MAX_RETRIES,
                last_error,
            )
            await set_task_status(
                task_id,
                "delivery_failed",
                {"error": f"Webhook delivery failed: {last_error}"},
            )
            await incr_metric("webhooks_failed")


async def main() -> None:
    """Delivery worker entry point."""
    settings = get_settings()

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    logger.info("[delivery] Starting delivery worker...")

    await start_redis()

    worker = DeliveryWorker(
        topic=settings.kafka_topic_completed,
        settings=settings,
    )

    try:
        await worker.run()
    except KeyboardInterrupt:
        logger.info("[delivery] Interrupted by user")
    finally:
        await stop_redis()


if __name__ == "__main__":
    asyncio.run(main())
