# 2. FastAPI — Async Web Framework

## What Is FastAPI?

**FastAPI** is a modern, high-performance Python web framework built on top of:
- **Starlette** (ASGI framework for async)
- **Pydantic** (data validation)
- **Uvicorn** (ASGI server)

### ASGI vs WSGI

| | WSGI (Flask, Django) | ASGI (FastAPI) |
|---|---|---|
| Model | Synchronous | Asynchronous (async/await) |
| Concurrency | Thread-based | Event loop (asyncio) |
| I/O | Blocks thread | Non-blocking |
| WebSocket | Not native | Native |
| Performance | ~1x | ~3-5x faster |

FastAPI is **ASGI**, meaning each request is handled asynchronously. While one request waits for Redis to respond, another request can be processed on the same thread.

---

## Entry Point: `src/main.py`

### Lifespan — Application Lifecycle

The **lifespan** concept in FastAPI manages what happens when the application starts and stops:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup: runs BEFORE accepting requests ---
    await start_redis()       # Connect to Redis
    await start_producer()    # Connect to Kafka

    yield  # ← The application runs here

    # --- Shutdown: runs when the app is stopping ---
    await stop_producer()     # Disconnect from Kafka
    await stop_redis()        # Disconnect from Redis
```

**Concept: `@asynccontextmanager`**
- A Python decorator that turns an async generator function into a context manager
- Everything before `yield` is the setup (startup)
- Everything after `yield` is the teardown (shutdown)
- Guarantees resources are released even in case of error

**Why use lifespan instead of `@app.on_event("startup")`?**
- `on_event` was **deprecated** in FastAPI
- Lifespan is the recommended pattern since FastAPI 0.93+
- Allows sharing state between startup and shutdown

### Application Creation

```python
def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Conn2Flow Nexus AI",
        description="AI Gateway — Man-in-the-Middle between Conn2Flow and multiple AI providers",
        version=settings.app_version,
        docs_url="/docs" if settings.app_debug else None,    # Swagger UI only in debug
        redoc_url="/redoc" if settings.app_debug else None,  # ReDoc only in debug
        lifespan=lifespan,
    )
```

**Concept: Factory Pattern**
- `create_app()` is a **factory function** — creates and configures the FastAPI instance
- Allows creating multiple instances (useful in tests)
- `docs_url=None` disables Swagger UI in production (security)

---

## Middleware: CORS

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Concept: CORS (Cross-Origin Resource Sharing)**
- Browsers block requests from one domain to another for security
- CORS defines which origins can access the API
- In **development**: `*` allows any origin
- In **production**: empty list (or specific list) for security

**Concept: Middleware**
- Middleware is code that runs **before and after** each request
- Works like an "interceptor" — modifies request/response
- In FastAPI, middlewares are stacked

---

## Router — Endpoint Organization

### `src/api/router.py`

```python
api_router = APIRouter()
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
```

**Concept: APIRouter**
- Allows organizing endpoints in separate modules
- `prefix="/tasks"` adds `/tasks` before all routes in the module
- `tags=["Tasks"]` groups them in Swagger UI
- In `main.py`, everything is included with `prefix="/api/v1"`:
  - `GET /api/v1/health`
  - `POST /api/v1/tasks/submit`
  - `GET /api/v1/tasks/status/{task_id}`

---

## Dependency Injection

### `src/api/endpoints/tasks.py`

```python
async def verify_api_key(
    x_c2f_api_key: str | None = Header(None),
    settings: Settings = Depends(get_settings),
) -> Settings:
    if settings.is_production and settings.c2f_api_key:
        if not x_c2f_api_key or x_c2f_api_key != settings.c2f_api_key:
            raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return settings
```

**Concept: Dependency Injection (DI)**
- `Depends(get_settings)` makes FastAPI automatically call `get_settings()` and inject the result
- `Header(None)` extracts the value from the `X-C2F-API-Key` HTTP header
- FastAPI resolves the entire dependency tree **before** executing the endpoint
- If a dependency raises an exception, the endpoint is **not** executed

```python
@router.post("/submit", ...)
async def submit_task(
    payload: TaskRequest,                        # JSON body → validated by Pydantic
    settings: Settings = Depends(verify_api_key), # DI: verifies API key
):
```

---

## HTTP Status Codes

| Code | Meaning | Usage in Project |
|------|---------|------------------|
| **200** | OK | Health check, status query |
| **202** | Accepted | Task accepted for async processing |
| **401** | Unauthorized | Invalid/missing API key |
| **404** | Not Found | Task ID not found |
| **422** | Unprocessable Entity | Invalid payload (Pydantic) |

`HTTP 202 Accepted` is fundamental: it means "I received your request, I'll process it later". Different from 200 which means "here is the result".

---

## Uvicorn — ASGI Server

```dockerfile
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- **Uvicorn** is the server that runs the FastAPI application
- `src.main:app` → imports the `app` object from the `src.main` module
- `--host 0.0.0.0` → accepts connections from any IP (required in Docker)
- `--port 8000` → application port

---

## Previous: [← Architecture](01-architecture-overview.md) | Next: [Pydantic →](03-pydantic.md)
