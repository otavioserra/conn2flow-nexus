# 11. FastAPI Deep Dive

## What Is FastAPI?

FastAPI is a **modern, async-first Python web framework** built on top of:
- **Starlette** — ASGI framework (async HTTP handling)
- **Pydantic** — Data validation and serialization
- **Uvicorn** — ASGI server (runs the app)

**PHP comparison:**
| PHP | Python |
|-----|--------|
| Laravel/Symfony | FastAPI |
| Apache/nginx + PHP-FPM | Uvicorn |
| Eloquent ORM | SQLAlchemy/Tortoise |
| FormRequest validation | Pydantic models |
| Middleware | Middleware (same concept) |
| Routes (web.php) | Router + decorators |
| Service container | `Depends()` |

---

## Application Factory

### From our codebase (`src/main.py`):
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Conn2Flow Nexus AI",
        description="AI Gateway — Man-in-the-Middle between Conn2Flow and multiple AI providers",
        version=settings.app_version,
        docs_url="/docs" if settings.app_debug else None,    # Swagger UI
        redoc_url="/redoc" if settings.app_debug else None,  # ReDoc
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if not settings.is_production else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(api_router, prefix="/api/v1")

    return app

app = create_app()
```

### PHP comparison (Laravel):
```php
// routes/api.php
Route::prefix('api/v1')->group(function () {
    Route::get('/health', [HealthController::class, 'check']);
    Route::prefix('/tasks')->group(function () {
        Route::post('/submit', [TaskController::class, 'submit']);
        Route::get('/status/{taskId}', [TaskController::class, 'status']);
    });
});
```

---

## Routing & Endpoints

### Router Organization
```python
# src/api/router.py
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])

# src/main.py
app.include_router(api_router, prefix="/api/v1")
```

Final URL structure:
```
GET  /api/v1/health         → health_check()
POST /api/v1/tasks/submit   → submit_task()
GET  /api/v1/tasks/status/{task_id} → get_task_status_endpoint()
```

### Route Decorators
```python
# src/api/endpoints/health.py
router = APIRouter()

@router.get("/health")
async def health_check():
    ...

# src/api/endpoints/tasks.py
router = APIRouter()

@router.post(
    "/submit",
    response_model=TaskAcceptedResponse,  # OpenAPI + validation
    status_code=status.HTTP_202_ACCEPTED,  # Default response code
    summary="Submits an AI task",          # OpenAPI summary
)
async def submit_task(
    payload: TaskRequest,                   # Request body (auto-parsed)
    settings: Settings = Depends(verify_api_key),  # DI
):
    ...

@router.get(
    "/status/{task_id}",                   # Path parameter
    response_model=TaskStatusResponse,
)
async def get_task_status_endpoint(
    task_id: str,                          # Extracted from URL
    _settings: Settings = Depends(verify_api_key),
):
    ...
```

### HTTP Methods:
| Decorator | HTTP Method | Typical Use |
|-----------|------------|-------------|
| `@router.get()` | GET | Retrieve data |
| `@router.post()` | POST | Create/submit |
| `@router.put()` | PUT | Full update |
| `@router.patch()` | PATCH | Partial update |
| `@router.delete()` | DELETE | Remove |

---

## Request Handling

### Path Parameters
```python
@router.get("/tasks/status/{task_id}")
async def get_status(task_id: str):
    # task_id is extracted from the URL
    ...
```

### Query Parameters
```python
@router.get("/tasks")
async def list_tasks(
    page: int = 1,         # ?page=2
    limit: int = 10,       # ?limit=50
    status: str | None = None,  # ?status=completed (optional)
):
    ...
```

### Request Body (Pydantic)
```python
@router.post("/tasks/submit")
async def submit_task(payload: TaskRequest):
    # FastAPI automatically:
    # 1. Reads the JSON body
    # 2. Validates against TaskRequest schema
    # 3. Returns 422 if validation fails
    # 4. Passes the validated model as `payload`
    print(payload.model)       # "gpt-4o-mini"
    print(payload.messages)    # [{"role": "user", "content": "Hello"}]
```

### Headers
```python
from fastapi import Header

@router.post("/submit")
async def submit(
    x_c2f_api_key: str | None = Header(None),  # X-C2F-API-Key header
):
    # Header names are auto-converted: X-C2F-API-Key → x_c2f_api_key
    ...
```

---

## Dependency Injection — `Depends()`

This is FastAPI's most powerful feature — equivalent to Laravel's Service Container.

### Basic DI
```python
from fastapi import Depends

def get_settings() -> Settings:
    return Settings()

@router.get("/health")
async def health(settings: Settings = Depends(get_settings)):
    # settings is injected by FastAPI
    return {"version": settings.app_version}
```

### Chain Dependencies
```python
# 1. Get settings
def get_settings() -> Settings:
    return Settings()

# 2. Verify API key (depends on settings)
async def verify_api_key(
    x_c2f_api_key: str | None = Header(None),
    settings: Settings = Depends(get_settings),  # DI chain!
) -> Settings:
    if settings.is_production and settings.c2f_api_key:
        if not x_c2f_api_key or x_c2f_api_key != settings.c2f_api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")
    return settings

# 3. Endpoint uses verified settings
@router.post("/submit")
async def submit_task(
    payload: TaskRequest,
    settings: Settings = Depends(verify_api_key),  # Verified!
):
    ...
```

**Flow:**
```
Request → FastAPI resolves Depends():
  1. Calls get_settings() → Settings
  2. Calls verify_api_key(header, settings) → Settings (or 401)
  3. Calls submit_task(payload, settings) → Response
```

### PHP comparison (Laravel):
```php
// Middleware approach
Route::post('/submit', [TaskController::class, 'submit'])
    ->middleware('api.key');

// Or constructor injection
class TaskController {
    public function __construct(
        private Settings $settings,
        private TaskService $taskService,
    ) {}
}
```

---

## Middleware

### CORS Middleware
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Custom Middleware
```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{elapsed:.3f}s"
        return response

app.add_middleware(TimingMiddleware)
```

---

## Lifespan — Startup & Shutdown

### From our codebase:
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    await start_redis()
    await start_producer()
    logger.info("All services initialized")

    yield  # App is running

    # Shutdown
    await stop_producer()
    await stop_redis()
    logger.info("Shutdown complete")

app = FastAPI(lifespan=lifespan)
```

**Why lifespan?** — Initialize expensive resources (DB connections, Kafka producers, Redis) **once** at startup, not per-request.

### PHP comparison:
```php
// Laravel: AppServiceProvider::boot()
public function boot(): void {
    $this->app->singleton(KafkaProducer::class, fn() => new KafkaProducer());
}
```

---

## Response Models & Status Codes

```python
@router.post(
    "/submit",
    response_model=TaskAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def submit_task(payload: TaskRequest, ...):
    return TaskAcceptedResponse(
        task_id=task_id,
        status="queued",
        message="Task accepted for async processing",
    )
```

**`response_model`** does three things:
1. **Validates** the response data
2. **Filters** — only fields in the model are returned (security)
3. **Documents** — generates OpenAPI schema

### Error Responses
```python
from fastapi import HTTPException, status

raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail=f"Task {task_id} not found",
)
# Returns: {"detail": "Task abc-123 not found"}
```

---

## OpenAPI & Swagger UI

FastAPI **automatically generates** OpenAPI documentation from your code:

- Type hints → schema types
- `Field(description=...)` → descriptions
- `response_model` → response schema
- `summary` → endpoint summary
- `tags` → grouping

Access at:
- `/docs` — Swagger UI (interactive)
- `/redoc` — ReDoc (clean documentation)
- `/openapi.json` — Raw OpenAPI spec

Our config disables these in production:
```python
docs_url="/docs" if settings.app_debug else None,
redoc_url="/redoc" if settings.app_debug else None,
```

---

## TestClient — Testing Without a Server

```python
from fastapi.testclient import TestClient
from src.main import app

# Synchronous testing (even though endpoints are async!)
with TestClient(app) as client:
    # GET request
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    # POST request with JSON body
    response = client.post(
        "/api/v1/tasks/submit",
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )
    assert response.status_code == 202
    data = response.json()
    assert "task_id" in data

    # With headers
    response = client.post(
        "/api/v1/tasks/submit",
        json={...},
        headers={"X-C2F-API-Key": "my-secret-key"},
    )
```

**No real server needed!** TestClient simulates HTTP requests in-memory using HTTPX.

---

## Running the Application

```bash
# Development (with hot-reload)
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Production (Docker)
uvicorn src.main:app --host 0.0.0.0 --port 8000

# With multiple workers
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**`src.main:app`** means: import `app` from `src/main.py`.

---

## Previous: [← Pydantic](10-pydantic.md) | Next: [Testing with Pytest →](12-pytest.md)
