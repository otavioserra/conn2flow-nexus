# 11. FastAPI em Profundidade

## O Que É FastAPI?

FastAPI é um **framework web Python moderno e async-first** construído sobre:
- **Starlette** — Framework ASGI (handling HTTP async)
- **Pydantic** — Validação e serialização de dados
- **Uvicorn** — Servidor ASGI (executa a app)

**Comparação PHP:**
| PHP | Python |
|-----|--------|
| Laravel/Symfony | FastAPI |
| Apache/nginx + PHP-FPM | Uvicorn |
| Eloquent ORM | SQLAlchemy/Tortoise |
| FormRequest validation | Modelos Pydantic |
| Middleware | Middleware (mesmo conceito) |
| Routes (web.php) | Router + decorators |
| Service container | `Depends()` |

---

## Application Factory

### Do nosso código (`src/main.py`):
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Conn2Flow Nexus AI",
        description="AI Gateway — Man-in-the-Middle entre Conn2Flow e múltiplos provedores de IA",
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

    # Rotas
    app.include_router(api_router, prefix="/api/v1")

    return app

app = create_app()
```

### Comparação PHP (Laravel):
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

## Roteamento & Endpoints

### Organização do Router
```python
# src/api/router.py
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])

# src/main.py
app.include_router(api_router, prefix="/api/v1")
```

Estrutura final de URLs:
```
GET  /api/v1/health         → health_check()
POST /api/v1/tasks/submit   → submit_task()
GET  /api/v1/tasks/status/{task_id} → get_task_status_endpoint()
```

### Decorators de Rota
```python
@router.post(
    "/submit",
    response_model=TaskAcceptedResponse,  # OpenAPI + validação
    status_code=status.HTTP_202_ACCEPTED,  # Código de resposta padrão
    summary="Submete uma tarefa de IA",    # Resumo OpenAPI
)
async def submit_task(
    payload: TaskRequest,                   # Body do request (auto-parsed)
    settings: Settings = Depends(verify_api_key),  # DI
):
    ...
```

### Métodos HTTP:
| Decorator | Método HTTP | Uso Típico |
|-----------|-----------|-------------|
| `@router.get()` | GET | Buscar dados |
| `@router.post()` | POST | Criar/submeter |
| `@router.put()` | PUT | Atualização completa |
| `@router.patch()` | PATCH | Atualização parcial |
| `@router.delete()` | DELETE | Remover |

---

## Handling de Request

### Parâmetros de Path
```python
@router.get("/tasks/status/{task_id}")
async def get_status(task_id: str):
    # task_id é extraído da URL
    ...
```

### Parâmetros de Query
```python
@router.get("/tasks")
async def list_tasks(
    page: int = 1,         # ?page=2
    limit: int = 10,       # ?limit=50
    status: str | None = None,  # ?status=completed (opcional)
):
    ...
```

### Body do Request (Pydantic)
```python
@router.post("/tasks/submit")
async def submit_task(payload: TaskRequest):
    # FastAPI automaticamente:
    # 1. Lê o body JSON
    # 2. Valida contra o schema TaskRequest
    # 3. Retorna 422 se validação falhar
    # 4. Passa o modelo validado como `payload`
    print(payload.model)       # "gpt-4o-mini"
    print(payload.messages)    # [{"role": "user", "content": "Hello"}]
```

### Headers
```python
from fastapi import Header

@router.post("/submit")
async def submit(
    x_c2f_api_key: str | None = Header(None),  # Header X-C2F-API-Key
):
    # Nomes de header são auto-convertidos: X-C2F-API-Key → x_c2f_api_key
    ...
```

---

## Injeção de Dependência — `Depends()`

Este é o recurso mais poderoso do FastAPI — equivalente ao Service Container do Laravel.

### DI Básica
```python
from fastapi import Depends

def get_settings() -> Settings:
    return Settings()

@router.get("/health")
async def health(settings: Settings = Depends(get_settings)):
    # settings é injetado pelo FastAPI
    return {"version": settings.app_version}
```

### Encadeamento de Dependências
```python
# 1. Obter settings
def get_settings() -> Settings:
    return Settings()

# 2. Verificar API key (depende de settings)
async def verify_api_key(
    x_c2f_api_key: str | None = Header(None),
    settings: Settings = Depends(get_settings),  # Encadeamento DI!
) -> Settings:
    if settings.is_production and settings.c2f_api_key:
        if not x_c2f_api_key or x_c2f_api_key != settings.c2f_api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")
    return settings

# 3. Endpoint usa settings verificados
@router.post("/submit")
async def submit_task(
    payload: TaskRequest,
    settings: Settings = Depends(verify_api_key),  # Verificado!
):
    ...
```

**Fluxo:**
```
Request → FastAPI resolve Depends():
  1. Chama get_settings() → Settings
  2. Chama verify_api_key(header, settings) → Settings (ou 401)
  3. Chama submit_task(payload, settings) → Response
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

### Middleware Customizado
```python
from starlette.middleware.base import BaseHTTPMiddleware
import time

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{elapsed:.3f}s"
        return response

app.add_middleware(TimingMiddleware)
```

---

## Lifespan — Startup & Shutdown

### Do nosso código:
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    await start_redis()
    await start_producer()
    logger.info("All services initialized")

    yield  # App está rodando

    # Shutdown
    await stop_producer()
    await stop_redis()
    logger.info("Shutdown complete")

app = FastAPI(lifespan=lifespan)
```

**Por que lifespan?** — Inicializa recursos caros (conexões DB, produtores Kafka, Redis) **uma vez** no startup, não por request.

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

**`response_model`** faz três coisas:
1. **Valida** os dados da resposta
2. **Filtra** — apenas campos do modelo são retornados (segurança)
3. **Documenta** — gera schema OpenAPI

### Respostas de Erro
```python
from fastapi import HTTPException, status

raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail=f"Task {task_id} not found",
)
# Retorna: {"detail": "Task abc-123 not found"}
```

---

## OpenAPI & Swagger UI

FastAPI **gera automaticamente** documentação OpenAPI do seu código:

- Type hints → tipos do schema
- `Field(description=...)` → descrições
- `response_model` → schema de resposta
- `summary` → resumo do endpoint
- `tags` → agrupamento

Acesse em:
- `/docs` — Swagger UI (interativo)
- `/redoc` — ReDoc (documentação limpa)
- `/openapi.json` — Spec OpenAPI raw

Nossa config desabilita em produção:
```python
docs_url="/docs" if settings.app_debug else None,
redoc_url="/redoc" if settings.app_debug else None,
```

---

## TestClient — Testando Sem Servidor

```python
from fastapi.testclient import TestClient
from src.main import app

# Teste síncrono (mesmo com endpoints async!)
with TestClient(app) as client:
    # Request GET
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    # Request POST com body JSON
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
```

**Não precisa de servidor real!** TestClient simula requests HTTP em memória usando HTTPX.

---

## Executando a Aplicação

```bash
# Desenvolvimento (com hot-reload)
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Produção (Docker)
uvicorn src.main:app --host 0.0.0.0 --port 8000

# Com múltiplos workers
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**`src.main:app`** significa: importar `app` de `src/main.py`.

---

## Anterior: [← Pydantic](10-pydantic.md) | Próximo: [Testes com Pytest →](12-pytest.md)
