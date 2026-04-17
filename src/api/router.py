"""
Conn2Flow Nexus AI - API Router
Aggregates all API endpoints.
"""

from fastapi import APIRouter

from src.api.endpoints.health import router as health_router
from src.api.endpoints.tasks import router as tasks_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["Health"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
