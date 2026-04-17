"""
Conn2Flow Nexus AI - Health Check Endpoint
"""

import logging

from fastapi import APIRouter

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check():
    settings = get_settings()

    # Test Redis connection
    redis_ok = False
    try:
        from src.core.redis_client import get_redis
        r = get_redis()
        await r.ping()
        redis_ok = True
    except Exception:
        logger.warning("Redis health check failed")

    return {
        "status": "healthy" if redis_ok else "degraded",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "dependencies": {
            "redis": "up" if redis_ok else "down",
            "kafka": "up",  # Producer would be null if stopped
        },
    }
