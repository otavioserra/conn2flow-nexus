# 5. Redis — Cache e Gerenciamento de Estado

## O Que É Redis?

**Redis** (Remote Dictionary Server) é um banco de dados **in-memory** que funciona como:
- **Key-Value Store** — armazena dados como pares chave/valor
- **Cache** — dados temporários de acesso rápido
- **Message Broker** — pub/sub (não usado aqui, usamos Kafka)
- **Contador** — operações atômicas de incremento

### Por que Redis neste projeto?

| Uso | Motivo |
|-----|--------|
| **Status de tarefas** | Consultar `GET /status/{task_id}` sem ir ao Kafka |
| **Métricas** | Contadores atômicos (tasks processadas, webhooks entregues) |
| **Health check** | Verificar se o Redis está ativo |

Redis é **extremamente rápido** (~100k operações/segundo) porque mantém tudo na RAM.

---

## Conceitos Fundamentais

### Key-Value Store

```
Chave                          Valor (JSON em bytes)
─────────────────────────────  ──────────────────────────────
c2f:task:abc-123               {"status": "completed", "result": {...}}
c2f:task:def-456               {"status": "processing", "model": "gpt-4o"}
c2f:metrics:tasks_completed    42
c2f:metrics:webhooks_failed    3
```

### TTL (Time To Live)

```python
DEFAULT_TTL = 60 * 60 * 24  # 24 horas em segundos
await r.set(key, value, ex=ttl)  # "ex" = expire in seconds
```

- Cada chave pode ter um **tempo de expiração**
- Após o TTL, Redis **remove automaticamente** a chave
- Evita que o Redis cresça infinitamente
- No projeto: status de tarefas expiram em 24h

### Serialização com orjson

```python
# Salvando:
value = orjson.dumps({"status": status, **(data or {})})
await r.set(f"{PREFIX_TASK}{task_id}", value, ex=ttl)

# Lendo:
raw = await r.get(f"{PREFIX_TASK}{task_id}")
return orjson.loads(raw)  # bytes → dict
```

- Redis armazena **bytes brutos** — não tem tipo "JSON"
- Usamos `orjson.dumps()` para converter dict → bytes
- Usamos `orjson.loads()` para converter bytes → dict

---

## Implementação: `src/core/redis_client.py`

### Singleton Async

```python
import redis.asyncio as aioredis

_redis: aioredis.Redis | None = None

async def start_redis() -> aioredis.Redis:
    global _redis
    _redis = aioredis.from_url(
        settings.redis_url,
        decode_responses=False,    # Trabalha com bytes brutos
        max_connections=20,        # Pool de 20 conexões
    )
    await _redis.ping()  # Testa a conexão imediatamente
```

**Conceito: Connection Pool**
- `max_connections=20` cria um **pool de conexões**
- Em vez de abrir/fechar conexão a cada operação, reutiliza conexões existentes
- Múltiplas coroutines podem usar o Redis ao mesmo tempo sem conflito

**Conceito: `decode_responses=False`**
- Por padrão, `redis-py` pode decodificar bytes → string automaticamente
- Desabilitamos porque usamos `orjson` para serializar/deserializar (mais rápido)

### Operações de Status

```python
# Prefixos organizam as chaves por categoria
PREFIX_TASK = "c2f:task:"
PREFIX_METRICS = "c2f:metrics:"

async def set_task_status(task_id: str, status: str, data: dict | None = None):
    r = get_redis()
    value = orjson.dumps({"status": status, **(data or {})})
    await r.set(f"{PREFIX_TASK}{task_id}", value, ex=DEFAULT_TTL)
```

**Conceito: Key Naming Convention**
- `c2f:task:abc-123` → namespace:tipo:identificador
- O `:` é uma convenção do Redis para organizar chaves hierarquicamente
- Ferramentas como RedisInsight agrupam chaves por namespace

**Conceito: `**(data or {})`**
- Spread operator (`**`) "espalha" o dict dentro de outro dict
- `data or {}` evita erro se `data` for `None`

### Contadores Atômicos

```python
async def incr_metric(name: str, amount: int = 1) -> int:
    r = get_redis()
    return await r.incrby(f"{PREFIX_METRICS}{name}", amount)
```

**Conceito: Operação Atômica**
- `INCRBY` é uma operação **atômica** no Redis
- Mesmo que 10 workers incrementem ao mesmo tempo, o valor final será correto
- Não há race condition — Redis é single-threaded para comandos

### Health Check

```python
# Em health.py:
r = get_redis()
await r.ping()  # Retorna True se Redis estiver ativo
```

---

## Configuração Docker

```yaml
redis:
  image: redis:7-alpine          # Imagem leve (Alpine Linux)
  command: >
    redis-server
    --appendonly yes               # Persiste dados no disco (AOF)
    --maxmemory 256mb             # Limite de memória
    --maxmemory-policy allkeys-lru # Remove chaves menos usadas quando cheio
  volumes:
    - redis_data:/data             # Persiste entre restarts
```

**Conceito: `appendonly yes` (AOF - Append Only File)**
- Redis é in-memory, mas `appendonly yes` salva cada operação em disco
- Se o container reiniciar, os dados são recuperados
- Trade-off: um pouco mais lento, mas não perde dados

**Conceito: `maxmemory-policy allkeys-lru`**
- LRU = Least Recently Used
- Quando Redis atinge 256MB, remove automaticamente as chaves **menos acessadas**
- Perfeito para cache e status temporários

---

## Fluxo no Projeto

```
1. POST /submit
   └── set_task_status(task_id, "queued")          ← Redis SET

2. TaskProcessorWorker inicia
   └── set_task_status(task_id, "processing")      ← Redis SET

3. LLM responde
   ├── set_task_status(task_id, "completed", {...}) ← Redis SET
   └── incr_metric("tasks_completed")               ← Redis INCRBY

4. GET /status/{task_id}
   └── get_task_status(task_id)                     ← Redis GET

5. Webhook falha
   ├── set_task_status(task_id, "delivery_failed")  ← Redis SET
   └── incr_metric("webhooks_failed")               ← Redis INCRBY
```

---

## Anterior: [← Kafka](04-kafka.md) | Próximo: [LiteLLM →](06-litellm.md)
