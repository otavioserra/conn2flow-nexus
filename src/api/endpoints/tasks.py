"""
Conn2Flow Nexus AI - Task Submission Endpoints
Receives requests from Conn2Flow, validates via Pydantic,
publishes to Kafka and returns HTTP 202 Accepted.
"""

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status

from src.api.schemas.requests import TaskRequest
from src.api.schemas.responses import TaskAcceptedResponse, TaskStatusResponse
from src.config.settings import Settings, get_settings
from src.core.kafka_producer import send_event
from src.core.redis_client import get_task_status, set_task_status
from src.models.events import TaskEvent

router = APIRouter()


async def verify_api_key(
    x_c2f_api_key: str | None = Header(None),
    settings: Settings = Depends(get_settings),
) -> Settings:
    """Verifies the X-C2F-API-Key header against the configured key."""
    if settings.is_production and settings.c2f_api_key:
        if not x_c2f_api_key or x_c2f_api_key != settings.c2f_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key",
            )
    return settings


@router.post(
    "/submit",
    response_model=TaskAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submits an AI task for asynchronous processing",
)
async def submit_task(
    payload: TaskRequest,
    settings: Settings = Depends(verify_api_key),
):
    task_id = str(uuid.uuid4())

    # Create the Kafka event
    event = TaskEvent(
        task_id=task_id,
        model=payload.model,
        messages=payload.messages,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        webhook_url=payload.webhook_url,
        metadata=payload.metadata,
        stream=payload.stream,
    )

    # Save initial status in Redis
    await set_task_status(task_id, "queued", {"model": payload.model})

    # Publish to Kafka
    await send_event(
        topic=settings.kafka_topic_incoming,
        value=event,
        key=task_id,
    )

    return TaskAcceptedResponse(
        task_id=task_id,
        status="queued",
        message="Task accepted for async processing",
    )


@router.get(
    "/status/{task_id}",
    response_model=TaskStatusResponse,
    summary="Queries the status of a submitted task",
)
async def get_task_status_endpoint(
    task_id: str,
    _settings: Settings = Depends(verify_api_key),
):
    data = await get_task_status(task_id)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    return TaskStatusResponse(task_id=task_id, **data)
