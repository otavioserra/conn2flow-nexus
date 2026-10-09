# SPEC-00: System Overview

> **Status**: ✅ Approved
> **Version**: 1.0.0
> **Created**: 2025-07-16
> **Last updated**: 2025-07-16

---

## 1. Purpose

**Conn2Flow Nexus AI** is an AI Gateway microservice that acts as a **Man-in-the-Middle** between the Conn2Flow platform (PHP) and multiple AI providers (OpenAI, Anthropic, Google Gemini, Groq).

### Problem It Solves

The Conn2Flow platform needs to consume AI models from different providers, but:

- LLM calls are slow (seconds to minutes)
- Each provider has its own API
- Failures in one provider should not bring down the system
- The PHP platform is synchronous by nature

### Solution

An asynchronous Python microservice that:

1. **Receives** HTTP requests from the Conn2Flow platform
2. **Enqueues** tasks in Apache Kafka
3. **Processes** asynchronously via workers with LangGraph
4. **Routes** between LLM providers with automatic fallback (LiteLLM)
5. **Delivers** results via Webhook with HMAC-SHA256 signature

## 2. System Context

```
┌──────────────────────────────────────────────────────────────────┐
│                        Conn2Flow (PHP)                           │
│                                                                  │
│  ┌─────────┐    POST /api/v1/tasks/submit    ┌───────────────┐  │
│  │ Modules  │──────────────────────────────▶ │   Nexus AI    │  │
│  │   PHP    │                                │   Gateway     │  │
│  │         │◀────── Webhook POST ◀───────── │   (Python)    │  │
│  └─────────┘    X-C2F-Signature: sha256=...  └───────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Conn2Flow (PHP)
    │
    ▼  HTTP POST
┌────────────────┐
│  FastAPI (API)  │  ← Validation + Auth
│  :8000          │
└───────┬────────┘
        │ Kafka produce
        ▼
┌────────────────┐
│  Apache Kafka   │  ← Event broker
│  c2f_incoming   │
│  _tasks         │
└───────┬────────┘
        │ Kafka consume
        ▼
┌────────────────┐
│  Task Worker    │  ← LangGraph + LiteLLM
│  (processor)    │
└───────┬────────┘
        │ Kafka produce
        ▼
┌────────────────┐
│  Apache Kafka   │
│  c2f_completed  │
│  _tasks         │
└───────┬────────┘
        │ Kafka consume
        ▼
┌────────────────┐
│  Delivery       │  ← Webhook + HMAC
│  Worker         │
└───────┬────────┘
        │ HTTP POST + HMAC
        ▼
Conn2Flow (PHP)
```

## 3. Technology Stack

| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11+ | Primary language |
| FastAPI | ≥0.115 | ASGI web framework |
| Pydantic | ≥2.10 | Data validation + settings |
| Apache Kafka | latest (KRaft) | Message broker (no Zookeeper) |
| Redis | 7-alpine | Status cache, metrics |
| LiteLLM | ≥1.50 | Multi-model LLM abstraction |
| LangGraph | ≥1.0 | Task graph orchestration |
| aiokafka | ≥0.11 | Async Kafka client |
| httpx | ≥0.27 | Async HTTP client (webhooks) |
| Docker Compose | v2 | Container orchestration |

## 4. Non-Functional Requirements

### Performance
- API must respond in < 100ms (HTTP 202 Accepted)
- LLM processing is asynchronous, no client-side timeout
- Redis must have < 5ms latency for get/set operations

### Scalability
- Kafka with 3 partitions allows up to 3 parallel workers
- Workers are stateless and horizontally scalable
- Redis in single-node mode is sufficient for v0.1

### Reliability
- Kafka with `acks=all` and `enable_idempotence=True`
- Webhooks with exponential backoff retry (5 attempts)
- Automatic fallback between LLM providers

### Observability
- Structured logs with configurable level
- Metrics via Redis counters (`tasks_completed`, `tasks_failed`, `webhooks_delivered`)
- Health check endpoint with dependency status

## 5. Scope Boundaries (v0.1)

### Included
- [x] Asynchronous task submission
- [x] Multi-model routing with fallback
- [x] Status tracking via Redis
- [x] Webhook delivery with HMAC
- [x] Health check

### Not Included (Future)
- [ ] Streaming (SSE/WebSocket)
- [ ] Rate limiting
- [ ] Billing/cost tracking
- [ ] Metrics dashboard
- [ ] Dead Letter Queue (DLQ)
- [ ] Circuit breaker per provider
- [ ] OAuth2 authentication
- [ ] Multi-tenancy

## 6. Quick Glossary

| Term | Definition |
|------|-----------|
| **Gateway** | Single entry point between Conn2Flow and AI providers |
| **Task** | A queued LLM processing request |
| **Worker** | Process that consumes Kafka messages and executes logic |
| **Webhook** | HTTP POST callback sent back to Conn2Flow |
| **Fallback** | Automatic retry with alternative model on failure |
