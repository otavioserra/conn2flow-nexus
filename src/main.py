"""
Conn2Flow Nexus AI - FastAPI Application Entry Point
"""

import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.router import api_router
from src.config.settings import get_settings
from src.core.kafka_producer import start_producer, stop_producer
from src.core.redis_client import start_redis, stop_redis

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application startup and shutdown lifecycle."""
    settings = get_settings()
    app.state.settings = settings

    # --- Startup ---
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    logger.info("Starting Conn2Flow Nexus AI v%s (%s)", settings.app_version, settings.app_env)

    await start_redis()
    await start_producer()

    logger.info("All services initialized")

    yield

    # --- Shutdown ---
    logger.info("Shutting down Conn2Flow Nexus AI...")
    await stop_producer()
    await stop_redis()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Conn2Flow Nexus AI",
        description="AI Gateway — Man-in-the-Middle between Conn2Flow and multiple AI providers",
        version=settings.app_version,
        docs_url="/docs" if settings.app_debug else None,
        redoc_url="/redoc" if settings.app_debug else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if not settings.is_production else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
