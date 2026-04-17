"""
Conn2Flow Nexus AI - Kafka Consumer Base
Base class for consumers that listen to Kafka topics.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any

import orjson
from aiokafka import AIOKafkaConsumer

from src.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class BaseKafkaConsumer(ABC):
    """Base class for workers that consume from a Kafka topic."""

    def __init__(self, topic: str, settings: Settings | None = None) -> None:
        self.topic = topic
        self.settings = settings or get_settings()
        self._consumer: AIOKafkaConsumer | None = None
        self._running = False

    async def start(self) -> None:
        """Initializes the consumer and starts consuming."""
        self._consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.settings.kafka_bootstrap_servers,
            group_id=self.settings.kafka_consumer_group,
            value_deserializer=lambda v: orjson.loads(v) if v else None,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            auto_commit_interval_ms=5_000,
        )
        await self._consumer.start()
        self._running = True
        logger.info(
            "[%s] Consumer started — topic=%s group=%s",
            self.__class__.__name__,
            self.topic,
            self.settings.kafka_consumer_group,
        )

    async def stop(self) -> None:
        """Stops the consumer."""
        self._running = False
        if self._consumer is not None:
            await self._consumer.stop()
            self._consumer = None
            logger.info("[%s] Consumer stopped", self.__class__.__name__)

    async def run(self) -> None:
        """Main loop: consumes messages and delegates to process_message()."""
        await self.start()
        try:
            async for msg in self._consumer:
                try:
                    logger.debug(
                        "[%s] Message received — partition=%d offset=%d",
                        self.__class__.__name__,
                        msg.partition,
                        msg.offset,
                    )
                    await self.process_message(msg.value)
                except Exception:
                    logger.exception(
                        "[%s] Error processing message at offset=%d",
                        self.__class__.__name__,
                        msg.offset,
                    )
                    await self.handle_error(msg.value)
        except asyncio.CancelledError:
            logger.info("[%s] Consumer cancelled", self.__class__.__name__)
        finally:
            await self.stop()

    @abstractmethod
    async def process_message(self, payload: dict[str, Any]) -> None:
        """Processes an individual message. Must be implemented by subclasses."""
        ...

    async def handle_error(self, payload: dict[str, Any]) -> None:
        """Error handling hook (DLQ, extra logging, etc.).

        Subclasses can override to implement custom logic.
        """
        logger.warning(
            "[%s] Message sent to error handling — payload keys: %s",
            self.__class__.__name__,
            list(payload.keys()) if isinstance(payload, dict) else "N/A",
        )
