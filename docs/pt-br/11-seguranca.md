# 11. Segurança

## Camadas de Segurança no Projeto

O Conn2Flow Nexus AI implementa segurança em múltiplas camadas:

```
Camada 1: Autenticação API Key         → Quem pode enviar tasks?
Camada 2: HMAC-SHA256 Webhook Signing  → O resultado é autêntico?
Camada 3: CORS Middleware              → Quem pode acessar do browser?
Camada 4: Non-Root Container           → Mínimo privilégio no Docker
Camada 5: Swagger desabilitado em prod → Menos superfície de ataque
```

---

## 1. API Key Authentication

### Implementação: `src/api/endpoints/tasks.py`

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

### Como Funciona:

1. O client envia o header `X-C2F-API-Key: <chave>`
2. O FastAPI extrai o valor via `Header(None)`
3. Compara com a chave configurada em `C2F_API_KEY` no `.env`
4. Se não bater, retorna `HTTP 401 Unauthorized`

### Decisões de Design:

- **Apenas em produção**: em desenvolvimento, qualquer request é aceita (facilitando testes)
- **Header em vez de query param**: headers não aparecem em logs de URL
- **Comparação simples**: para um projeto inicial, é suficiente. Em produção, considerar:
  - `hmac.compare_digest()` para evitar timing attacks
  - JWT tokens para autenticação stateless
  - OAuth2 para autorização baseada em escopos

---

## 2. HMAC-SHA256 — Webhook Signing

### Implementação: `src/workers/delivery_worker.py`

```python
def _sign_payload(payload_bytes: bytes, secret: str) -> str:
    return hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()
```

### Fluxo:

```
Nexus AI (remetente)                        Conn2Flow (destinatário)
─────────────────────                       ────────────────────────
1. Serializa payload → bytes
2. HMAC(bytes, segredo) → assinatura
3. Envia POST com header:
   X-C2F-Signature: sha256=<assinatura>
                                            4. Recebe POST
                                            5. Lê body como bytes
                                            6. HMAC(bytes, segredo) → assinatura local
                                            7. Compara assinaturas
                                               ✓ Iguais → payload autêntico
                                               ✗ Diferentes → payload adulterado
```

### Por que HMAC é necessário?

Sem assinatura, qualquer pessoa poderia enviar um POST para o webhook do Conn2Flow fingindo ser o Nexus AI. Com HMAC:
- **Autenticidade**: prova que o payload veio do Nexus AI
- **Integridade**: prova que o payload não foi modificado em trânsito
- **Segredo compartilhado**: apenas quem tem o `C2F_WEBHOOK_SECRET` pode gerar assinaturas válidas

### Comparação Segura (Best Practice)

No lado do **receptor** (Conn2Flow), sempre usar:
```python
import hmac
is_valid = hmac.compare_digest(expected_signature, received_signature)
```

`compare_digest()` é **constant-time** — não vaza informação sobre onde a comparação falhou (previne timing attacks).

---

## 3. CORS — Cross-Origin Resource Sharing

### Implementação: `src/main.py`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### O que é CORS?

Browsers bloqueiam requests JavaScript para domínios diferentes (Same-Origin Policy). CORS é o mecanismo para relaxar essa restrição de forma controlada.

### No projeto:
- **Desenvolvimento**: `allow_origins=["*"]` → qualquer origem pode acessar (conveniência)
- **Produção**: `allow_origins=[]` → nenhuma origem via browser (a API é chamada server-to-server pelo Conn2Flow, não por um browser)

---

## 4. Non-Root Container

### Implementação: `Dockerfile`

```dockerfile
RUN addgroup --system c2f && adduser --system --ingroup c2f c2f
USER c2f
```

### Risco sem isso:
- Se um atacante explorar uma vulnerabilidade no Python/FastAPI, ele teria **root** dentro do container
- Com root, poderia: instalar pacotes, acessar volumes, escapar do container em certas configurações

### Com non-root:
- O processo roda como usuário `c2f` sem privilégios
- Não pode instalar pacotes, modificar arquivos de sistema, etc.
- Princípio do **menor privilégio**

---

## 5. Swagger Desabilitado em Produção

### Implementação: `src/main.py`

```python
docs_url="/docs" if settings.app_debug else None,
redoc_url="/redoc" if settings.app_debug else None,
```

### Por quê?
- Swagger UI expõe **todos os endpoints**, schemas e exemplos
- Um atacante poderia usar isso para mapear a API
- Em produção: `APP_DEBUG=false` → Swagger e ReDoc desabilitados
- Em desenvolvimento: `APP_DEBUG=true` → disponível em `/docs`

---

## 6. Variáveis Sensíveis no `.env`

### `.env` (NÃO versionado)
```env
OPENAI_API_KEY=sk-real-key-here
C2F_WEBHOOK_SECRET=real-secret
```

### `.env.example` (versionado)
```env
OPENAI_API_KEY=sk-your-openai-key-here
C2F_WEBHOOK_SECRET=your-webhook-signing-secret-here
```

### `.gitignore`
```
.env
!.env.example
```

- `.env` com valores reais **nunca** entra no Git
- `.env.example` é um template com placeholders — serve de referência
- Em produção, variáveis são injetadas via Docker secrets ou variáveis de ambiente do host

---

## Checklist de Segurança

| Item | Status | Onde |
|------|--------|------|
| API Key Authentication | ✅ | `tasks.py` |
| HMAC Webhook Signing | ✅ | `delivery_worker.py` |
| CORS restritivo em prod | ✅ | `main.py` |
| Non-root container | ✅ | `Dockerfile` |
| Swagger desabilitado em prod | ✅ | `main.py` |
| `.env` no `.gitignore` | ✅ | `.gitignore` |
| Validação rigorosa de input | ✅ | Pydantic schemas |
| API keys não no código | ✅ | `settings.py` → `.env` |

---

## Anterior: [← Testes](10-testes.md) | Próximo: [Glossário →](12-glossario.md)
