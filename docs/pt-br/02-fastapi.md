# 2. FastAPI — Web Framework Assíncrono

## O Que É FastAPI?

**FastAPI** é um framework web Python moderno e de alta performance, construído sobre:
- **Starlette** (framework ASGI para async)
- **Pydantic** (validação de dados)
- **Uvicorn** (servidor ASGI)

### ASGI vs WSGI

| | WSGI (Flask, Django) | ASGI (FastAPI) |
|---|---|---|
| Modelo | Síncrono | Assíncrono (async/await) |
| Concorrência | Thread-based | Event loop (asyncio) |
| I/O | Bloqueia thread | Non-blocking |
| WebSocket | Não nativo | Nativo |
| Performance | ~1x | ~3-5x mais rápido |

FastAPI é **ASGI**, ou seja, cada request é tratada de forma assíncrona. Enquanto uma request espera o Redis responder, outra request pode ser processada no mesmo thread.

---

## Entry Point: `src/main.py`

### Lifespan — Ciclo de Vida da Aplicação

O conceito de **lifespan** no FastAPI gerencia o que acontece quando a aplicação inicia e quando ela para:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup: executa ANTES de aceitar requests ---
    await start_redis()       # Conecta ao Redis
    await start_producer()    # Conecta ao Kafka

    yield  # ← A aplicação roda aqui

    # --- Shutdown: executa quando a app está parando ---
    await stop_producer()     # Desconecta do Kafka
    await stop_redis()        # Desconecta do Redis
```

**Conceito: `@asynccontextmanager`**
- É um decorador do Python que transforma uma função geradora async em um context manager
- Tudo antes do `yield` é o setup (startup)
- Tudo depois do `yield` é o teardown (shutdown)
- Garante que recursos são liberados mesmo em caso de erro

**Por que usar lifespan em vez de `@app.on_event("startup")`?**
- `on_event` foi **deprecated** no FastAPI
- Lifespan é o padrão recomendado desde FastAPI 0.93+
- Permite compartilhar estado entre startup e shutdown

### Criação da Aplicação

```python
def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Conn2Flow Nexus AI",
        description="AI Gateway — Man-in-the-Middle entre Conn2Flow e múltiplos provedores de IA",
        version=settings.app_version,
        docs_url="/docs" if settings.app_debug else None,    # Swagger UI só em debug
        redoc_url="/redoc" if settings.app_debug else None,  # ReDoc só em debug
        lifespan=lifespan,
    )
```

**Conceito: Factory Pattern**
- `create_app()` é uma **factory function** — cria e configura a instância do FastAPI
- Permite criar múltiplas instâncias (útil em testes)
- `docs_url=None` desabilita o Swagger UI em produção (segurança)

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

**Conceito: CORS (Cross-Origin Resource Sharing)**
- Browsers bloqueiam requests de um domínio para outro por segurança
- CORS define quais origens podem acessar a API
- Em **desenvolvimento**: `*` permite qualquer origem
- Em **produção**: lista vazia (ou lista específica) para segurança

**Conceito: Middleware**
- Middleware é código que roda **antes e depois** de cada request
- Funciona como um "interceptor" — modifica request/response
- No FastAPI, middlewares são empilhados (stack)

---

## Router — Organização de Endpoints

### `src/api/router.py`

```python
api_router = APIRouter()
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
```

**Conceito: APIRouter**
- Permite organizar endpoints em módulos separados
- `prefix="/tasks"` adiciona `/tasks` antes de todas as rotas do módulo
- `tags=["Tasks"]` agrupa no Swagger UI
- No `main.py`, tudo é incluído com `prefix="/api/v1"`:
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

**Conceito: Dependency Injection (DI)**
- `Depends(get_settings)` faz o FastAPI chamar `get_settings()` automaticamente e injetar o resultado
- `Header(None)` extrai o valor do header HTTP `X-C2F-API-Key`
- O FastAPI resolve toda a árvore de dependências **antes** de executar o endpoint
- Se a dependência lançar uma exceção, o endpoint **não** é executado

```python
@router.post("/submit", ...)
async def submit_task(
    payload: TaskRequest,                        # Body JSON → validado pelo Pydantic
    settings: Settings = Depends(verify_api_key), # DI: verifica API key
):
```

---

## Status Codes HTTP

| Código | Significado | Uso no Projeto |
|--------|------------|----------------|
| **200** | OK | Health check, consulta de status |
| **202** | Accepted | Task aceita para processamento async |
| **401** | Unauthorized | API key inválida/ausente |
| **404** | Not Found | Task ID não encontrado |
| **422** | Unprocessable Entity | Payload inválido (Pydantic) |

O `HTTP 202 Accepted` é fundamental: significa "recebi seu pedido, vou processar depois". Diferente do 200 que significa "aqui está o resultado".

---

## Uvicorn — Servidor ASGI

```dockerfile
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- **Uvicorn** é o servidor que roda a aplicação FastAPI
- `src.main:app` → importa o objeto `app` do módulo `src.main`
- `--host 0.0.0.0` → aceita conexões de qualquer IP (necessário no Docker)
- `--port 8000` → porta da aplicação

---

## Anterior: [← Arquitetura](01-arquitetura-geral.md) | Próximo: [Pydantic →](03-pydantic.md)
