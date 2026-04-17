"""
Conn2Flow Nexus AI - Kafka Producer
Async wrapper for publishing events to Kafka topics.
"""

from __future__ import annotations

import logging
from typing import Any

import orjson
from aiokafka import AIOKafkaProducer
from pydantic import BaseModel

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

_producer: AIOKafkaProducer | None = None


def _serialize(value: Any) -> bytes:
    """Serializes payload to bytes using orjson."""
    if isinstance(value, BaseModel):
        return orjson.dumps(value.model_dump(mode="json"))
    if isinstance(value, (dict, list)):
        return orjson.dumps(value)
    if isinstance(value, bytes):
        return value
    return orjson.dumps(value)


async def start_producer() -> AIOKafkaProducer:
    """Initializes and returns the singleton Kafka producer."""
    global _producer
    if _producer is not None:
        return _producer

    settings = get_settings()
    _producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_serializer=_serialize,
        key_serializer=lambda k: k.encode("utf-8") if isinstance(k, str) else k,
        acks="all",
        enable_idempotence=True,
        retry_backoff_ms=100,
        request_timeout_ms=30_000,
    )
    await _producer.start()
    logger.info("Kafka producer started — %s", settings.kafka_bootstrap_servers)
    return _producer


async def stop_producer() -> None:
    """Stops the Kafka producer."""
    global _producer
    if _producer is not None:
        await _producer.stop()
        _producer = None
        logger.info("Kafka producer stopped")


async def send_event(topic: str, value: Any, key: str | None = None) -> None:
    """Publishes an event to the specified Kafka topic.

    Args:
        topic: Kafka topic name.
        value: Payload (Pydantic model, dict or bytes).
        key: Optional key for partitioning.
    """
    if _producer is None:
        raise RuntimeError("Kafka producer not initialized. Call start_producer() first.")

    metadata = await _producer.send_and_wait(topic, value=value, key=key)
    logger.debug(
        "Event sent — topic=%s partition=%d offset=%d key=%s",
        metadata.topic,
        metadata.partition,
        metadata.offset,
        key,
    )
