# SPEC-07: Infrastructure

> **Status**: ✅ Approved
> **Version**: 1.0.0
> **Created**: 2025-07-16
> **Last updated**: 2025-07-16

---

## 1. Docker Compose Services

The system is composed of **5 Docker services**:

| Service | Image | Container Name | Port |
|---------|-------|---------------|------|
| `kafka` | `apache/kafka:latest` | `c2f-kafka` | 9092, 29092 |
| `redis` | `redis:7-alpine` | `c2f-redis` | 6379 |
| `api` | Local build (Dockerfile) | `c2f-api` | 8000 |
| `worker-task` | Local build (Dockerfile) | `c2f-worker-task` | — |
| `worker-delivery` | Local build (Dockerfile) | `c2f-worker-delivery` | — |

## 2. Dockerfile (Multi-Stage Build)

### Stage 1: Builder

```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt
```

### Stage 2: Runtime

```dockerfile
FROM python:3.11-slim AS runtime
WORKDIR /app
COPY --from=builder /install /usr/local
COPY src/ ./src/
RUN addgroup --system c2f && adduser --system --ingroup c2f c2f
USER c2f
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Rules**:
- Multi-stage to minimize image size
- `PYTHONDONTWRITEBYTECODE=1` — no `.pyc` files
- `PYTHONUNBUFFERED=1` — real-time logs
- `PYTHONPATH=/app` — allows `from src.xxx import yyy`
- Non-root user `c2f` for security

## 3. Kafka Configuration (KRaft)

| Property | Value |
|----------|-------|
| `KAFKA_NODE_ID` | `1` |
| `KAFKA_PROCESS_ROLES` | `broker,controller` |
| `KAFKA_NUM_PARTITIONS` | `3` |
| `KAFKA_AUTO_CREATE_TOPICS_ENABLE` | `true` |
| `KAFKA_LOG_RETENTION_HOURS` | `168` (7 days) |
| `KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR` | `1` |
| `KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR` | `1` |
| `KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS` | `0` |

### Listeners

| Listener | Address | Purpose |
|----------|---------|---------|
| `PLAINTEXT` | `0.0.0.0:29092` | Inter-container |
| `PLAINTEXT_HOST` | `0.0.0.0:9092` | Host access |
| `CONTROLLER` | `0.0.0.0:9093` | Controller quorum |

### Advertised Listeners

| Listener | Address |
|----------|---------|
| `PLAINTEXT` | `kafka:29092` |
| `PLAINTEXT_HOST` | `localhost:9092` |

**Rule**: Application containers use `kafka:29092` (Docker network). The host uses `localhost:9092`.

## 4. Redis Configuration

| Property | Value |
|----------|-------|
| **Image** | `redis:7-alpine` |
| **Command** | `redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru` |
| **Persistence** | AOF (Append Only File) |
| **Max Memory** | 256MB |
| **Eviction** | `allkeys-lru` (Least Recently Used) |
| **Volume** | `redis_data:/data` |

## 5. Volumes

| Volume | Driver | Used by | Purpose |
|--------|--------|---------|---------|
| `kafka_data` | local | Kafka | Broker data and logs |
| `redis_data` | local | Redis | AOF and snapshots |

## 6. Health Checks

### Kafka

```yaml
test: /opt/kafka/bin/kafka-broker-api-versions.sh --bootstrap-server localhost:9092 > /dev/null 2>&1
interval: 15s
timeout: 10s
retries: 5
start_period: 30s
```

### Redis

```yaml
test: ["CMD", "redis-cli", "ping"]
interval: 10s
timeout: 5s
retries: 3
```

## 7. Service Dependencies

```
kafka ─────────┐
               ├──▶ api (depends_on: kafka + redis healthy)
redis ─────────┤
               ├──▶ worker-task (depends_on: kafka + redis healthy)
               │
               └──▶ worker-delivery (depends_on: kafka + redis healthy)
```

**Rule**: All application services wait for `service_healthy` from Kafka and Redis before starting.

## 8. Networking

All services share the **default** Docker Compose network.

| From | To | Address |
|------|----|---------|
| `api` | `kafka` | `kafka:29092` |
| `api` | `redis` | `redis://redis:6379/0` |
| `worker-task` | `kafka` | `kafka:29092` |
| `worker-task` | `redis` | `redis://redis:6379/0` |
| `worker-delivery` | `kafka` | `kafka:29092` |
| `worker-delivery` | `redis` | `redis://redis:6379/0` |
| `worker-delivery` | `Conn2Flow` | `http://host.docker.internal/...` |

## 9. Environment Variables (Docker)

Environment variables are injected via:

1. **`env_file: .env`** — `.env` file at the project root
2. **`environment:`** — Per-container overrides

### Per-container Overrides

| Container | Variable | Value | Reason |
|-----------|----------|-------|--------|
| `api` | `KAFKA_BOOTSTRAP_SERVERS` | `kafka:29092` | Uses inter-container listener |
| `api` | `REDIS_URL` | `redis://redis:6379/0` | Uses Docker hostname |
| `worker-task` | (same above) | (same) | (same) |
| `worker-delivery` | (same above) | (same) | (same) |

## 10. Hot-Reload (Development)

```yaml
volumes:
  - ./src:/app/src  # Mount local src/ into the container
```

**Rule**: In development, the `src/` directory is mounted as a volume to allow changes without rebuild. In production, this volume must be removed.

## 11. Restart Policy

| Container | Policy |
|-----------|--------|
| `kafka` | (default: no) |
| `redis` | (default: no) |
| `api` | `unless-stopped` |
| `worker-task` | `unless-stopped` |
| `worker-delivery` | `unless-stopped` |

## 12. Operational Commands

```bash
# Build and start everything
docker compose up -d --build

# View logs for all services
docker compose logs -f

# View logs for a specific service
docker compose logs -f api

# Stop everything
docker compose down

# Stop and remove volumes (CAUTION: loses Kafka and Redis data)
docker compose down -v
```
# SPEC-07: Infrastructure

> **Status**: ✅ Aprovada
> **Versão**: 1.0.0
> **Criada em**: 2025-07-16
> **Última atualização**: 2025-07-16

---

## 1. Docker Compose Services

O sistema é composto por **5 serviços** Docker:

| Service | Image | Container Name | Porta |
|---------|-------|---------------|-------|
| `kafka` | `apache/kafka:latest` | `c2f-kafka` | 9092, 29092 |
| `redis` | `redis:7-alpine` | `c2f-redis` | 6379 |
| `api` | Build local (Dockerfile) | `c2f-api` | 8000 |
| `worker-task` | Build local (Dockerfile) | `c2f-worker-task` | — |
| `worker-delivery` | Build local (Dockerfile) | `c2f-worker-delivery` | — |

## 2. Dockerfile (Multi-Stage Build)

### Stage 1: Builder

```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt
```

### Stage 2: Runtime

```dockerfile
FROM python:3.11-slim AS runtime
WORKDIR /app
COPY --from=builder /install /usr/local
COPY src/ ./src/
RUN addgroup --system c2f && adduser --system --ingroup c2f c2f
USER c2f
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Regras**:
- Multi-stage para minimizar tamanho da imagem
- `PYTHONDONTWRITEBYTECODE=1` — sem arquivos `.pyc`
- `PYTHONUNBUFFERED=1` — logs em tempo real
- `PYTHONPATH=/app` — permite `from src.xxx import yyy`
- Usuário não-root `c2f` para segurança

## 3. Kafka Configuration (KRaft)

| Propriedade | Valor |
|-------------|-------|
| `KAFKA_NODE_ID` | `1` |
| `KAFKA_PROCESS_ROLES` | `broker,controller` |
| `KAFKA_NUM_PARTITIONS` | `3` |
| `KAFKA_AUTO_CREATE_TOPICS_ENABLE` | `true` |
| `KAFKA_LOG_RETENTION_HOURS` | `168` (7 dias) |
| `KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR` | `1` |
| `KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR` | `1` |
| `KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS` | `0` |

### Listeners

| Listener | Endereço | Propósito |
|----------|----------|-----------|
| `PLAINTEXT` | `0.0.0.0:29092` | Inter-container |
| `PLAINTEXT_HOST` | `0.0.0.0:9092` | Host access |
| `CONTROLLER` | `0.0.0.0:9093` | Controller quorum |

### Advertised Listeners

| Listener | Endereço |
|----------|----------|
| `PLAINTEXT` | `kafka:29092` |
| `PLAINTEXT_HOST` | `localhost:9092` |

**Regra**: Os containers da aplicação usam `kafka:29092` (rede Docker). O host usa `localhost:9092`.

## 4. Redis Configuration

| Propriedade | Valor |
|-------------|-------|
| **Image** | `redis:7-alpine` |
| **Command** | `redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru` |
| **Persistência** | AOF (Append Only File) |
| **Max Memory** | 256MB |
| **Eviction** | `allkeys-lru` (Least Recently Used) |
| **Volume** | `redis_data:/data` |

## 5. Volumes

| Volume | Driver | Usado por | Propósito |
|--------|--------|-----------|-----------|
| `kafka_data` | local | Kafka | Dados do broker e logs |
| `redis_data` | local | Redis | AOF e snapshots |

## 6. Health Checks

### Kafka

```yaml
test: /opt/kafka/bin/kafka-broker-api-versions.sh --bootstrap-server localhost:9092 > /dev/null 2>&1
interval: 15s
timeout: 10s
retries: 5
start_period: 30s
```

### Redis

```yaml
test: ["CMD", "redis-cli", "ping"]
interval: 10s
timeout: 5s
retries: 3
```

## 7. Dependências entre Services

```
kafka ─────────┐
               ├──▶ api (depends_on: kafka + redis healthy)
redis ─────────┤
               ├──▶ worker-task (depends_on: kafka + redis healthy)
               │
               └──▶ worker-delivery (depends_on: kafka + redis healthy)
```

**Regra**: Todos os serviços da aplicação aguardam `service_healthy` do Kafka e Redis antes de iniciar.

## 8. Networking

Todos os serviços compartilham a **rede default** do Docker Compose.

| De | Para | Endereço |
|----|------|----------|
| `api` | `kafka` | `kafka:29092` |
| `api` | `redis` | `redis://redis:6379/0` |
| `worker-task` | `kafka` | `kafka:29092` |
| `worker-task` | `redis` | `redis://redis:6379/0` |
| `worker-delivery` | `kafka` | `kafka:29092` |
| `worker-delivery` | `redis` | `redis://redis:6379/0` |
| `worker-delivery` | `Conn2Flow` | `http://host.docker.internal/...` |

## 9. Environment Variables (Docker)

As variáveis de ambiente são injetadas via:

1. **`env_file: .env`** — Arquivo `.env` na raiz do projeto
2. **`environment:`** — Overrides específicos por container

### Overrides por container

| Container | Variável | Valor | Razão |
|-----------|----------|-------|-------|
| `api` | `KAFKA_BOOTSTRAP_SERVERS` | `kafka:29092` | Usa listener inter-container |
| `api` | `REDIS_URL` | `redis://redis:6379/0` | Usa hostname Docker |
| `worker-task` | (mesmo acima) | (mesmo) | (mesmo) |
| `worker-delivery` | (mesmo acima) | (mesmo) | (mesmo) |

## 10. Hot-Reload (Development)

```yaml
volumes:
  - ./src:/app/src  # Monta src/ local no container
```

**Regra**: Em desenvolvimento, o diretório `src/` é montado como volume para permitir alterações sem rebuild. Em produção, este volume deve ser removido.

## 11. Restart Policy

| Container | Policy |
|-----------|--------|
| `kafka` | (default: no) |
| `redis` | (default: no) |
| `api` | `unless-stopped` |
| `worker-task` | `unless-stopped` |
| `worker-delivery` | `unless-stopped` |

## 12. Comandos de Operação

```bash
# Build e iniciar tudo
docker compose up -d --build

# Ver logs de todos os serviços
docker compose logs -f

# Ver logs de um serviço específico
docker compose logs -f api

# Parar tudo
docker compose down

# Parar e remover volumes (CUIDADO: perde dados Kafka e Redis)
docker compose down -v

# Rebuild apenas a API
docker compose build api
docker compose up -d api
```
