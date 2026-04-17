"""
Conn2Flow Nexus AI - Task Processor Worker
Kafka consumer that listens to c2f_incoming_tasks,
executes the LangGraph pipeline and publishes results to c2f_completed_tasks.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from src.config.settings import get_settings
from src.core.kafka_consumer import BaseKafkaConsumer
from src.core.kafka_producer import send_event, start_producer, stop_producer
from src.core.redis_client import incr_metric, set_task_status, start_redis, stop_redis
from src.graphs.base_graph import run_task_graph
from src.models.events import TaskResultEvent

logger = logging.getLogger(__name__)


class TaskProcessorWorker(BaseKafkaConsumer):
    """Consumes tasks from Kafka, processes via LangGraph and publishes results."""

    async def process_message(self, payload: dict[str, Any]) -> None:
        task_id = payload.get("task_id", "unknown")
        model = payload.get("model", self.settings.default_model)
        messages = payload.get("messages", [])
        temperature = payload.get("temperature", 0.7)
        max_tokens = payload.get("max_tokens")
        webhook_url = payload.get("webhook_url")
        metadata = payload.get("metadata", {})

        logger.info("[task-processor] Processing task=%s model=%s", task_id, model)

        # Update status to "processing"
        await set_task_status(task_id, "processing", {"model": model})

        # Execute the LangGraph pipeline
        result_state = await run_task_graph(
            task_id=task_id,
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Build the result event
        if result_state.get("error"):
            result_event = TaskResultEvent(
                task_id=task_id,
                status="failed",
                model=model,
                error=result_state["error"],
                webhook_url=webhook_url or self.settings.c2f_webhook_url,
                metadata=metadata,
            )
            await set_task_status(task_id, "failed", {"error": result_state["error"]})
            await incr_metric("tasks_failed")
        else:
            llm_response = result_state.get("llm_response", {})
            result_event = TaskResultEvent(
                task_id=task_id,
                status="completed",
                model=llm_response.get("model_used", model),
                result={"content": llm_response.get("content", "")},
                usage=llm_response.get("usage"),
                webhook_url=webhook_url or self.settings.c2f_webhook_url,
                metadata=metadata,
            )
            await set_task_status(
                task_id,
                "completed",
                {
                    "result": {"content": llm_response.get("content", "")},
                    "model": llm_response.get("model_used", model),
                    "usage": llm_response.get("usage"),
                },
            )
            await incr_metric("tasks_completed")

        # Publish result to the output topic
        await send_event(
            topic=self.settings.kafka_topic_completed,
            value=result_event,
            key=task_id,
        )

        logger.info(
            "[task-processor] Task %s → %s",
            task_id,
            result_event.status,
        )


async def main() -> None:
    """Worker entry point."""
    settings = get_settings()

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    logger.info("[task-processor] Starting worker...")

    # Initialize dependencies
    await start_redis()
    await start_producer()

    worker = TaskProcessorWorker(
        topic=settings.kafka_topic_incoming,
        settings=settings,
    )

    try:
        await worker.run()
    except KeyboardInterrupt:
        logger.info("[task-processor] Interrupted by user")
    finally:
        await stop_producer()
        await stop_redis()


if __name__ == "__main__":
    asyncio.run(main())
