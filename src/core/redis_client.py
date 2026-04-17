"""
Conn2Flow Nexus AI - Redis Client
Async singleton for Redis operations (checkpointing, cache, status).
"""

from __future__ import annotations

import logging
from typing import Any

import orjson
import redis.asyncio as aioredis

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

_redis: aioredis.Redis | None = None

# Redis key prefixes
PREFIX_TASK = "c2f:task:"
PREFIX_METRICS = "c2f:metrics:"
DEFAULT_TTL = 60 * 60 * 24  # 24h


async def start_redis() -> aioredis.Redis:
    """Initializes the singleton Redis client."""
    global _redis
    if _redis is not None:
        return _redis

    settings = get_settings()
    _redis = aioredis.from_url(
        settings.redis_url,
        decode_responses=False,
        max_connections=20,
    )
    await _redis.ping()
    logger.info("Redis connected — %s", settings.redis_url)
    return _redis


async def stop_redis() -> None:
    """Closes the Redis connection."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
        logger.info("Redis connection closed")


def get_redis() -> aioredis.Redis:
    """Returns the active Redis instance."""
    if _redis is None:
        raise RuntimeError("Redis not initialized. Call start_redis() first.")
    return _redis


# ---------------------------------------------------------------------------
# Task Status Operations
# ---------------------------------------------------------------------------

async def set_task_status(
    task_id: str,
    status: str,
    data: dict[str, Any] | None = None,
    ttl: int = DEFAULT_TTL,
) -> None:
    """Saves/updates a task status in Redis."""
    r = get_redis()
    value = orjson.dumps({"status": status, **(data or {})})
    await r.set(f"{PREFIX_TASK}{task_id}", value, ex=ttl)


async def get_task_status(task_id: str) -> dict[str, Any] | None:
    """Retrieves a task status from Redis."""
    r = get_redis()
    raw = await r.get(f"{PREFIX_TASK}{task_id}")
    if raw is None:
        return None
    return orjson.loads(raw)


# ---------------------------------------------------------------------------
# Metrics / Counters
# ---------------------------------------------------------------------------

async def incr_metric(name: str, amount: int = 1) -> int:
    """Increments a metrics counter."""
    r = get_redis()
    return await r.incrby(f"{PREFIX_METRICS}{name}", amount)


async def get_metric(name: str) -> int:
    """Retrieves a counter value."""
    r = get_redis()
    val = await r.get(f"{PREFIX_METRICS}{name}")
    return int(val) if val else 0
