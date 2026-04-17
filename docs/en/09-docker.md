# 9. Docker & Docker Compose

## What Is Docker?

**Docker** packages an application and **all** its dependencies into a **container** — an isolated environment that runs the same on any machine.

### Container vs Virtual Machine

| | VM | Container |
|---|---|---|
| Includes | Entire OS + App | Only App + libs |
| Size | ~GB | ~MB |
| Startup | Minutes | Seconds |
| Isolation | Full (hypervisor) | Processes (kernel) |
| Performance | ~90% | ~99% of host |

---

## Dockerfile: `Dockerfile`

### Multi-Stage Build

```dockerfile
# --- Stage 1: Builder ---
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt
```

**Concept: Multi-Stage Build**
- Stage 1 (`builder`) installs Python dependencies in `/install`
- Stage 2 (`runtime`) copies **only** the installed packages
- The build stage is **discarded** — it doesn't go into the final image
- Result: smaller image (no compilers, headers, pip cache)

**`--no-cache-dir`** → doesn't save pip cache (space savings)
**`--prefix=/install`** → installs in a separate directory for later copying

```dockerfile
# --- Stage 2: Runtime ---
FROM python:3.11-slim AS runtime
LABEL maintainer="Conn2Flow <dev@conn2flow.com>"
LABEL description="Conn2Flow Nexus AI - AI Gateway"
```

**`python:3.11-slim`** → minimal Python base image (~150MB vs ~900MB for the full version)

### Environment Variables

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app
```

| Variable | Effect |
|----------|--------|
| `PYTHONDONTWRITEBYTECODE=1` | Doesn't generate `.pyc` files (space savings) |
| `PYTHONUNBUFFERED=1` | Logs appear **immediately** (no buffer) |
| `PYTHONPATH=/app` | Python finds modules in `/app` (e.g., `from src.main import app`) |

### Copying Dependencies

```dockerfile
COPY --from=builder /install /usr/local
COPY src/ ./src/
```

- `--from=builder` copies from the previous stage
- Only `/install` (Python packages) and `src/` (our code) go into the image

### Security: Non-Root User

```dockerfile
RUN addgroup --system c2f && adduser --system --ingroup c2f c2f
USER c2f
```

**Concept: Principle of Least Privilege**
- By default, containers run as `root` — dangerous if there's a vulnerability
- We create a `c2f` user without admin permissions
- If an attacker compromises the container, they don't have root access

### CMD — Startup Command

```dockerfile
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- `EXPOSE 8000` documents the port (doesn't open it automatically)
- `CMD` is the command executed when the container starts
- Workers override it with `command` in docker-compose

---

## Docker Compose: `docker-compose.yml`

### Kafka (KRaft Mode)

```yaml
kafka:
  image: apache/kafka:latest
  container_name: c2f-kafka
  ports:
    - "9092:9092"       # Host → Container
    - "29092:29092"     # Debug tools
  environment:
    KAFKA_NODE_ID: 1
    KAFKA_PROCESS_ROLES: broker,controller
    KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:29092,CONTROLLER://0.0.0.0:9093,PLAINTEXT_HOST://0.0.0.0:9092
    KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
```

**Concept: Port Mapping `host:container`**
- `9092:9092` → port 9092 on your PC points to port 9092 in the container
- Allows accessing Kafka from outside Docker (tools, debugging)

**Concept: Healthcheck**
```yaml
healthcheck:
  test: /opt/kafka/bin/kafka-broker-api-versions.sh --bootstrap-server localhost:9092
  interval: 15s
  timeout: 10s
  retries: 5
  start_period: 30s
```
- Periodically checks if Kafka is healthy
- `start_period: 30s` → waits 30s before starting to check (Kafka takes time to start)
- Other containers use `condition: service_healthy` to wait

### Redis

```yaml
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
  volumes:
    - redis_data:/data
```

**Concept: Named Volumes**
```yaml
volumes:
  kafka_data:
    driver: local
  redis_data:
    driver: local
```
- Volumes persist data **across restarts** of the container
- `redis_data:/data` → Redis data is stored in a Docker volume
- Even with `docker compose down`, data is preserved
- To delete: `docker compose down -v` (removes volumes)

### API

```yaml
api:
  build:
    context: .
    dockerfile: Dockerfile
  ports:
    - "8000:8000"
  env_file:
    - .env
  environment:
    KAFKA_BOOTSTRAP_SERVERS: kafka:29092
    REDIS_URL: redis://redis:6379/0
  depends_on:
    kafka: { condition: service_healthy }
    redis: { condition: service_healthy }
  volumes:
    - ./src:/app/src  # Hot-reload in dev
```

**Concept: `env_file` vs `environment`**
- `env_file: .env` → loads all variables from the file
- `environment:` → overrides specific variables
- `KAFKA_BOOTSTRAP_SERVERS: kafka:29092` → inside Docker, uses the service name as hostname

**Concept: Bind Mount for Dev**
```yaml
volumes:
  - ./src:/app/src
```
- Maps `./src` from the host to `/app/src` in the container
- Code changes appear **instantly** in the container
- Combined with uvicorn hot-reload → development without rebuild

**Concept: `depends_on` with Health Check**
```yaml
depends_on:
  kafka:
    condition: service_healthy
```
- The API container **doesn't start** until Kafka is healthy
- Without this, the API would try to connect to Kafka before it's ready → error

### Workers

```yaml
worker-task:
  build: { context: ., dockerfile: Dockerfile }
  command: ["python", "-m", "src.workers.task_processor"]
  restart: unless-stopped
```

**Concept: `restart: unless-stopped`**
- If the container crashes, Docker restarts automatically
- If you stop it manually (`docker stop`), it doesn't restart
- Essential for workers: if the worker crashes from a temporary error, it comes back automatically

---

## Useful Commands

```bash
# Start everything (build + start)
docker compose up -d --build

# View logs
docker compose logs -f api
docker compose logs -f worker-task

# Status
docker compose ps

# Stop
docker compose down

# Stop and remove volumes (data)
docker compose down -v

# Rebuild only one service
docker compose build api
docker compose up -d api
```

---

## Docker Network

```
┌─────────────────────────────────────────────────────────┐
│ Docker Network (bridge)                                  │
│                                                          │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  kafka   │  │  redis    │  │  api      │  │ worker-* │ │
│  │ :29092   │  │ :6379     │  │ :8000     │  │          │ │
│  └─────────┘  └──────────┘  └──────────┘  └──────────┘ │
│       ↑              ↑            ↑                      │
└───────┼──────────────┼────────────┼──────────────────────┘
        │              │            │
   localhost:9092  localhost:6379  localhost:8000
        ↑              ↑            ↑
   ┌────┴──────────────┴────────────┴────┐
   │          Your PC (Host)              │
   └──────────────────────────────────────┘
```

---

## Previous: [← Workers](08-workers.md) | Next: [Testing →](10-testing.md)
