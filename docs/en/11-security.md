# 11. Security

## Security Layers in the Project

Conn2Flow Nexus AI implements security in multiple layers:

```
Layer 1: API Key Authentication        → Who can submit tasks?
Layer 2: HMAC-SHA256 Webhook Signing   → Is the result authentic?
Layer 3: CORS Middleware               → Who can access from the browser?
Layer 4: Non-Root Container            → Minimum privilege in Docker
Layer 5: Swagger disabled in prod      → Less attack surface
```

---

## 1. API Key Authentication

### Implementation: `src/api/endpoints/tasks.py`

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

### How It Works:

1. The client sends the header `X-C2F-API-Key: <key>`
2. FastAPI extracts the value via `Header(None)`
3. Compares with the configured key in `C2F_API_KEY` from `.env`
4. If it doesn't match, returns `HTTP 401 Unauthorized`

### Design Decisions:

- **Production only**: in development, any request is accepted (facilitating testing)
- **Header instead of query param**: headers don't appear in URL logs
- **Simple comparison**: for an initial project, it's sufficient. In production, consider:
  - `hmac.compare_digest()` to prevent timing attacks
  - JWT tokens for stateless authentication
  - OAuth2 for scope-based authorization

---

## 2. HMAC-SHA256 — Webhook Signing

### Implementation: `src/workers/delivery_worker.py`

```python
def _sign_payload(payload_bytes: bytes, secret: str) -> str:
    return hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()
```

### Flow:

```
Nexus AI (sender)                           Conn2Flow (recipient)
─────────────────                           ────────────────────
1. Serialize payload → bytes
2. HMAC(bytes, secret) → signature
3. Send POST with header:
   X-C2F-Signature: sha256=<signature>
                                            4. Receive POST
                                            5. Read body as bytes
                                            6. HMAC(bytes, secret) → local signature
                                            7. Compare signatures
                                               ✓ Equal → authentic payload
                                               ✗ Different → tampered payload
```

### Why Is HMAC Necessary?

Without signing, anyone could send a POST to Conn2Flow's webhook pretending to be Nexus AI. With HMAC:
- **Authenticity**: proves the payload came from Nexus AI
- **Integrity**: proves the payload was not modified in transit
- **Shared secret**: only those with `C2F_WEBHOOK_SECRET` can generate valid signatures

### Secure Comparison (Best Practice)

On the **receiver** side (Conn2Flow), always use:
```python
import hmac
is_valid = hmac.compare_digest(expected_signature, received_signature)
```

`compare_digest()` is **constant-time** — it doesn't leak information about where the comparison failed (prevents timing attacks).

---

## 3. CORS — Cross-Origin Resource Sharing

### Implementation: `src/main.py`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### What Is CORS?

Browsers block JavaScript requests to different domains (Same-Origin Policy). CORS is the mechanism to relax this restriction in a controlled way.

### In the project:
- **Development**: `allow_origins=["*"]` → any origin can access (convenience)
- **Production**: `allow_origins=[]` → no browser origin allowed (the API is called server-to-server by Conn2Flow, not by a browser)

---

## 4. Non-Root Container

### Implementation: `Dockerfile`

```dockerfile
RUN addgroup --system c2f && adduser --system --ingroup c2f c2f
USER c2f
```

### Risk without it:
- If an attacker exploits a vulnerability in Python/FastAPI, they'd have **root** inside the container
- With root, they could: install packages, access volumes, escape the container in certain configurations

### With non-root:
- The process runs as `c2f` user without privileges
- Cannot install packages, modify system files, etc.
- Principle of **least privilege**

---

## 5. Swagger Disabled in Production

### Implementation: `src/main.py`

```python
docs_url="/docs" if settings.app_debug else None,
redoc_url="/redoc" if settings.app_debug else None,
```

### Why?
- Swagger UI exposes **all endpoints**, schemas, and examples
- An attacker could use this to map the API
- In production: `APP_DEBUG=false` → Swagger and ReDoc disabled
- In development: `APP_DEBUG=true` → available at `/docs`

---

## 6. Sensitive Variables in `.env`

### `.env` (NOT versioned)
```env
OPENAI_API_KEY=sk-real-key-here
C2F_WEBHOOK_SECRET=real-secret
```

### `.env.example` (versioned)
```env
OPENAI_API_KEY=sk-your-openai-key-here
C2F_WEBHOOK_SECRET=your-webhook-signing-secret-here
```

### `.gitignore`
```
.env
!.env.example
```

- `.env` with real values **never** enters Git
- `.env.example` is a template with placeholders — serves as reference
- In production, variables are injected via Docker secrets or host environment variables

---

## Security Checklist

| Item | Status | Where |
|------|--------|-------|
| API Key Authentication | ✅ | `tasks.py` |
| HMAC Webhook Signing | ✅ | `delivery_worker.py` |
| Restrictive CORS in prod | ✅ | `main.py` |
| Non-root container | ✅ | `Dockerfile` |
| Swagger disabled in prod | ✅ | `main.py` |
| `.env` in `.gitignore` | ✅ | `.gitignore` |
| Strict input validation | ✅ | Pydantic schemas |
| API keys not in code | ✅ | `settings.py` → `.env` |

---
