# 9. Docker & Docker Compose

## O Que É Docker?

**Docker** empacota uma aplicação e **todas** suas dependências em um **container** — um ambiente isolado que roda igual em qualquer máquina.

### Container vs Virtual Machine

| | VM | Container |
|---|---|---|
| Inclui | SO inteiro + App | Apenas App + libs |
| Tamanho | ~GB | ~MB |
| Startup | Minutos | Segundos |
| Isolamento | Total (hypervisor) | Processos (kernel) |
| Performance | ~90% | ~99% do host |

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

**Conceito: Multi-Stage Build**
- Stage 1 (`builder`) instala dependências Python em `/install`
- Stage 2 (`runtime`) copia **apenas** os pacotes instalados
- O stage de build é **descartado** — não entra na imagem final
- Resultado: imagem menor (sem compiladores, headers, cache do pip)

**`--no-cache-dir`** → não salva cache do pip (economia de espaço)
**`--prefix=/install`** → instala em diretório separado para copiar depois

```dockerfile
# --- Stage 2: Runtime ---
FROM python:3.11-slim AS runtime
LABEL maintainer="Conn2Flow <dev@conn2flow.com>"
LABEL description="Conn2Flow Nexus AI - AI Gateway"
```

**`python:3.11-slim`** → imagem base minimalista do Python (~150MB vs ~900MB da versão full)

### Variáveis de Ambiente

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app
```

| Variável | Efeito |
|----------|--------|
| `PYTHONDONTWRITEBYTECODE=1` | Não gera arquivos `.pyc` (economia de espaço) |
| `PYTHONUNBUFFERED=1` | Logs aparecem **imediatamente** (sem buffer) |
| `PYTHONPATH=/app` | Python encontra módulos em `/app` (ex: `from src.main import app`) |

### Copiando Dependências

```dockerfile
COPY --from=builder /install /usr/local
COPY src/ ./src/
```

- `--from=builder` copia do stage anterior
- Apenas `/install` (pacotes Python) e `src/` (nosso código) entram na imagem

### Segurança: Non-Root User

```dockerfile
RUN addgroup --system c2f && adduser --system --ingroup c2f c2f
USER c2f
```

**Conceito: Princípio do Menor Privilégio**
- Por padrão, containers rodam como `root` — perigoso se houver vulnerabilidade
- Criamos um usuário `c2f` sem permissões de administrador
- Se um atacante comprometer o container, não tem acesso root

### CMD — Comando de Inicialização

```dockerfile
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- `EXPOSE 8000` documenta a porta (não abre automaticamente)
- `CMD` é o comando executado quando o container inicia
- Workers sobrescrevem com `command` no docker-compose

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

**Conceito: Port Mapping `host:container`**
- `9092:9092` → porta 9092 do seu PC aponta para porta 9092 do container
- Permite acessar o Kafka de fora do Docker (ferramentas, debug)

**Conceito: Healthcheck**
```yaml
healthcheck:
  test: /opt/kafka/bin/kafka-broker-api-versions.sh --bootstrap-server localhost:9092
  interval: 15s
  timeout: 10s
  retries: 5
  start_period: 30s
```
- Verifica periodicamente se o Kafka está saudável
- `start_period: 30s` → espera 30s antes de começar a verificar (Kafka demora para iniciar)
- Outros containers usam `condition: service_healthy` para esperar

### Redis

```yaml
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
  volumes:
    - redis_data:/data
```

**Conceito: Named Volumes**
```yaml
volumes:
  kafka_data:
    driver: local
  redis_data:
    driver: local
```
- Volumes persistem dados **entre restarts** do container
- `redis_data:/data` → dados do Redis ficam em um volume Docker
- Mesmo se `docker compose down`, dados são preservados
- Para apagar: `docker compose down -v` (remove volumes)

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
    - ./src:/app/src  # Hot-reload em dev
```

**Conceito: `env_file` vs `environment`**
- `env_file: .env` → carrega todas as variáveis do arquivo
- `environment:` → sobrescreve variáveis específicas
- `KAFKA_BOOTSTRAP_SERVERS: kafka:29092` → dentro do Docker, usa o nome do serviço como hostname

**Conceito: Bind Mount para Dev**
```yaml
volumes:
  - ./src:/app/src
```
- Mapeia `./src` do host para `/app/src` no container
- Alterações no código aparecem **instantaneamente** no container
- Combinado com hot-reload do uvicorn → desenvolvimento sem rebuild

**Conceito: `depends_on` com Health Check**
```yaml
depends_on:
  kafka:
    condition: service_healthy
```
- O container da API **não inicia** até o Kafka estar healthy
- Sem isso, a API tentaria conectar ao Kafka antes dele estar pronto → erro

### Workers

```yaml
worker-task:
  build: { context: ., dockerfile: Dockerfile }
  command: ["python", "-m", "src.workers.task_processor"]
  restart: unless-stopped
```

**Conceito: `restart: unless-stopped`**
- Se o container crashar, Docker reinicia automaticamente
- Se você parar manualmente (`docker stop`), não reinicia
- Essencial para workers: se o worker crashar por erro temporário, volta automaticamente

---

## Comandos Úteis

```bash
# Subir tudo (build + start)
docker compose up -d --build

# Ver logs
docker compose logs -f api
docker compose logs -f worker-task

# Status
docker compose ps

# Parar
docker compose down

# Parar e remover volumes (dados)
docker compose down -v

# Rebuild apenas um serviço
docker compose build api
docker compose up -d api
```

---

## Rede Docker

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
   │          Seu PC (Host)               │
   └──────────────────────────────────────┘
```

---

## Anterior: [← Workers](08-workers.md) | Próximo: [Testes →](10-testes.md)
