# 1. Architecture Overview

## What Is Conn2Flow Nexus AI?

**Conn2Flow Nexus AI** is a **microservice** that works as an **AI Gateway** — an intermediary (Man-in-the-Middle) between the Conn2Flow platform and multiple Artificial Intelligence providers (OpenAI, Anthropic, Google, Groq, etc.).

### Why an AI Gateway?

Without a gateway, each Conn2Flow module would need to:
- Implement integration with each AI provider separately
- Handle rate limiting, retries, and fallbacks
- Manage API keys in multiple locations
- Monitor costs and token usage

With Nexus AI, all of this is **centralized in a single point**.

---

## Architectural Pattern: Event-Driven Architecture (EDA)

The project uses the **Event-Driven Architecture** pattern, where components communicate through **events** instead of direct calls (synchronous REST).

### How It Works:

```
┌─────────────┐        ┌──────────────┐        ┌─────────────────────┐
│  Conn2Flow   │──POST──►  FastAPI API  │──pub──►  Kafka               │
│  (Client)    │◄──202──│  (Gateway)    │        │  c2f_incoming_tasks  │
└─────────────┘        └──────────────┘        └──────────┬──────────┘
                                                          │ consume
                                                ┌─────────▼──────────┐
                                                │  Task Worker        │
                                                │  (LangGraph +       │
                                                │   LiteLLM)          │
                                                └─────────┬──────────┘
                                                          │ pub
                                               ┌──────────▼──────────┐
                                               │  Kafka               │
                                               │  c2f_completed_tasks │
                                               └──────────┬──────────┘
                                                          │ consume
                                               ┌──────────▼──────────┐
                                               │  Delivery Worker     │
                                               │  (Webhook POST)      │
                                               └──────────┬──────────┘
                                                          │
                                               ┌──────────▼──────────┐
                                               │  Conn2Flow           │
                                               │  (Webhook Receiver)  │
                                               └─────────────────────┘
```

### Advantages of EDA:

| Advantage | Explanation |
|-----------|-------------|
| **Decoupling** | The API doesn't need to wait for the LLM to finish — returns 202 immediately |
| **Resilience** | If the worker crashes, messages stay in Kafka until processed |
| **Scalability** | We can add N workers to process in parallel |
| **Auditing** | All events are recorded in Kafka topics |

---

## Pattern: Async Request-Reply

The full flow implements the **Async Request-Reply** pattern:

1. **Request**: Conn2Flow sends a task via `POST /api/v1/tasks/submit`
2. **Accept**: The API returns `HTTP 202 Accepted` with a `task_id`
3. **Process**: The worker consumes from Kafka, processes via the LLM, and publishes the result
4. **Reply**: The delivery worker sends the result back via webhook

This is fundamentally different from a synchronous pattern where the client would wait 30+ seconds for the LLM response.

---

## Directory Structure

```
conn2flow-nexus/
├── src/                          # Main source code
│   ├── main.py                   # Entry point — creates the FastAPI app
│   ├── config/
│   │   └── settings.py           # Centralized configuration (pydantic-settings)
│   ├── api/
│   │   ├── router.py             # Aggregates API routes
│   │   ├── endpoints/
│   │   │   ├── health.py         # GET /health — health check
│   │   │   └── tasks.py          # POST /submit + GET /status/{id}
│   │   └── schemas/
│   │       ├── requests.py       # Input schema (TaskRequest)
│   │       └── responses.py      # Response schemas
│   ├── core/                     # Shared infrastructure
│   │   ├── kafka_producer.py     # Publish events to Kafka
│   │   ├── kafka_consumer.py     # Base class for consumers
│   │   ├── redis_client.py       # Async Redis client (status + metrics)
│   │   └── llm_router.py        # Multi-provider LLM router
│   ├── workers/                  # Independent processes
│   │   ├── task_processor.py     # Consumer: processes tasks with LLM
│   │   └── delivery_worker.py    # Consumer: delivers results via webhook
│   ├── graphs/
│   │   └── base_graph.py         # LangGraph pipeline (validate → llm → format)
│   └── models/
│       └── events.py             # Kafka event models
├── tests/                        # Unit tests
├── docs/                         # Documentation (this folder)
├── specs/                        # SDD specifications
├── docker-compose.yml            # Docker orchestration
├── Dockerfile                    # Container build
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables (local)
└── .env.example                  # .env template
```

---

## Key Concepts

### Singleton Pattern
Used in `kafka_producer.py` and `redis_client.py` — a single instance is shared across the entire application via a module-level global variable.

### Dependency Injection
FastAPI uses native DI via `Depends()` — for example, `verify_api_key` is automatically injected into endpoints.

### Abstract Base Class (ABC)
`BaseKafkaConsumer` is an abstract class that defines the contract every consumer must follow, allowing easy extension.

### Separation of Concerns
Each layer has a single responsibility:
- `api/` → Receives and validates HTTP
- `core/` → Infrastructure (Kafka, Redis, LLM)
- `workers/` → Processing logic
- `graphs/` → Pipeline orchestration
- `models/` → Data contracts

---

## Next: [FastAPI — Web Framework →](02-fastapi.md)
