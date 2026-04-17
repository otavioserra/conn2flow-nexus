# SPEC-01: Architecture

> **Status**: ✅ Approved
> **Version**: 1.0.0
> **Created**: 2025-07-16
> **Last updated**: 2025-07-16

---

## 1. Architectural Pattern

The system follows **Event-Driven Architecture (EDA)** with the **Async Request-Reply** pattern:

- The API receives synchronous requests and responds immediately (202 Accepted)
- Actual processing happens asynchronously via Kafka
- Results are delivered via Webhook (push) or queried via polling (pull)

## 2. System Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Docker Compose Network                         │
│                                                                     │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                        │
│  │ c2f-api  │   │ c2f-     │   │ c2f-     │                        │
│  │ :8000    │   │ worker-  │   │ worker-  │                        │
│  │ FastAPI  │   │ task     │   │ delivery │                        │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘                        │
│       │              │              │                               │
│       ▼              ▼              ▼                               │
│  ┌─────────────────────────────────────┐                            │
│  │        Apache Kafka (KRaft)         │                            │
│  │   c2f_incoming_tasks (3 partitions) │                            │
│  │   c2f_completed_tasks (3 partitions)│                            │
│  └─────────────────────────────────────┘                            │
│                                                                     │
│  ┌─────────────────────────────────────┐                            │
│  │          Redis 7-alpine             │                            │
│  │   Task status + Metrics             │                            │
│  └─────────────────────────────────────┘                            │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.1. API Service (`c2f-api`)

| Property | Value |
|----------|-------|
| **Framework** | FastAPI (ASGI) |
| **Port** | 8000 |
| **Responsibility** | Receive requests, validate, enqueue to Kafka |
| **Pattern** | Factory Pattern (`create_app()`) |
| **Lifecycle** | Lifespan context manager (startup/shutdown) |

### 2.2. Task Worker (`c2f-worker-task`)

| Property | Value |
|----------|-------|
| **Base** | `BaseKafkaConsumer` (Template Method Pattern) |
| **Input topic** | `c2f_incoming_tasks` |
| **Output topic** | `c2f_completed_tasks` |
| **Processing** | LangGraph StateGraph → LiteLLM |
| **Responsibility** | Consume tasks, execute LLM, publish results |

### 2.3. Delivery Worker (`c2f-worker-delivery`)

| Property | Value |
|----------|-------|
| **Base** | `BaseKafkaConsumer` (Template Method Pattern) |
| **Input topic** | `c2f_completed_tasks` |
| **Responsibility** | Deliver results via Webhook with HMAC |
| **Retry** | Exponential backoff (5 attempts, base 2s) |

### 2.4. Apache Kafka

| Property | Value |
|----------|-------|
| **Mode** | KRaft (no Zookeeper) |
| **Roles** | Combined broker + controller |
| **Topics** | `c2f_incoming_tasks`, `c2f_completed_tasks` |
| **Partitions** | 3 per topic |
| **Retention** | 168 hours (7 days) |
| **Auto-create** | Enabled |

### 2.5. Redis

| Property | Value |
|----------|-------|
| **Version** | 7-alpine |
| **Persistence** | AOF (appendonly yes) |
| **Max Memory** | 256MB |
| **Eviction** | allkeys-lru |
| **Usage** | Task status, metrics, health check |
| **Default TTL** | 24 hours |

## 3. Directory Structure

```
conn2flow-nexus/
├── src/
│   ├── __init__.py
│   ├── main.py                    # FastAPI entry point
│   ├── api/
│   │   ├── router.py              # Route aggregator
│   │   ├── endpoints/
│   │   │   ├── health.py          # GET /health
│   │   │   └── tasks.py           # POST /submit, GET /status/{id}
│   │   └── schemas/
│   │       ├── requests.py        # TaskRequest
│   │       └── responses.py       # TaskAcceptedResponse, TaskStatusResponse
│   ├── config/
│   │   └── settings.py            # Pydantic BaseSettings + @lru_cache
│   ├── core/
│   │   ├── kafka_producer.py      # Singleton AIOKafkaProducer
│   │   ├── kafka_consumer.py      # BaseKafkaConsumer ABC
│   │   ├── redis_client.py        # Singleton Redis client
│   │   └── llm_router.py          # LiteLLM wrapper + fallback
│   ├── graphs/
│   │   └── base_graph.py          # LangGraph StateGraph
│   ├── models/
│   │   └── events.py              # TaskEvent, TaskResultEvent
│   └── workers/
│       ├── task_processor.py      # TaskProcessorWorker
│       └── delivery_worker.py     # DeliveryWorker
├── tests/
│   ├── conftest.py                # Global fixtures
│   ├── test_schemas.py            # 18 schema tests
│   ├── test_settings.py           # 5 settings tests
│   ├── test_api.py                # 7 API tests
│   ├── test_llm_router.py         # 6 LLM router tests
│   └── test_graph.py              # 4 graph tests
├── specs/                          # ← You are here
├── docs/                           # Educational documentation
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── pyproject.toml
├── .env
└── .env.example
```

## 4. Design Patterns Used

| Pattern | Where | Purpose |
|---------|-------|---------|
| **Factory Pattern** | `create_app()` in `main.py` | Configurable FastAPI app construction |
| **Singleton** | `_producer`, `_redis`, `get_settings()` | Single instance of shared resources |
| **Template Method** | `BaseKafkaConsumer` | Standard interface for consumers, with hooks |
| **Dependency Injection** | `Depends(verify_api_key)` | Settings and auth injection via FastAPI |
| **Observer/Pub-Sub** | Kafka topics | Decoupling between producer and consumers |
| **State Machine** | LangGraph `StateGraph` | Typed state node orchestration |

## 5. Architectural Decision Records (ADRs)

### ADR-001: Kafka as Message Broker

**Context**: We need a broker for asynchronous processing.
**Decision**: Apache Kafka in KRaft mode (no Zookeeper).
**Rationale**: Ordering guarantees, persistence, scalability, and native support for consumer groups.
**Consequence**: Greater operational complexity than Redis Streams, but better durability.

### ADR-002: Redis for Status (not Kafka)

**Context**: Conn2Flow needs to query task status (polling).
**Decision**: Redis as key-value store for task status.
**Rationale**: Sub-millisecond latency for reads, automatic TTL, atomic operations.
**Consequence**: Data is ephemeral (24h TTL), suitable for temporary status.

### ADR-003: LiteLLM as Abstraction

**Context**: Support multiple LLM providers with a unified API.
**Decision**: LiteLLM as the abstraction layer.
**Rationale**: Single interface for 100+ models, native fallback, built-in retry.
**Consequence**: Third-party dependency, but saves hundreds of lines of code.

### ADR-004: LangGraph for Orchestration

**Context**: Processing pipeline with conditional steps.
**Decision**: LangGraph StateGraph with 3 nodes.
**Rationale**: Explicit graph, typed state (TypedDict), conditional routing, extensible.
**Consequence**: Overhead for the current simple case, but ready for complex pipelines.

### ADR-005: Webhook with HMAC-SHA256

**Context**: Securely deliver results back to Conn2Flow.
**Decision**: HTTP POST with HMAC-SHA256 signature in `X-C2F-Signature` header.
**Rationale**: Industry standard (GitHub, Stripe), integrity verification without PKI.
**Consequence**: Conn2Flow needs to implement HMAC verification on the receiver side.
