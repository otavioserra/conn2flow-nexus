# 📚 Conn2Flow Nexus AI — Documentation

Welcome to the technical and educational documentation for **Conn2Flow Nexus AI**.

This guide was created as **learning material**, explaining each concept, design pattern, and technology used in the project, with direct references to the source code.

## 📖 Index

| # | Document | Description |
|---|----------|-------------|
| 1 | [Architecture Overview](01-architecture-overview.md) | Event-driven microservice architecture, data flow and design decisions |
| 2 | [FastAPI — Web Framework](02-fastapi.md) | Concepts: ASGI, lifespan, dependency injection, middleware, Pydantic schemas |
| 3 | [Pydantic — Validation & Schemas](03-pydantic.md) | Data validation, BaseModel, Field, model_validator, pydantic-settings |
| 4 | [Apache Kafka — Event Streaming](04-kafka.md) | Concepts: brokers, topics, partitions, consumer groups, KRaft, aiokafka |
| 5 | [Redis — Cache & State](05-redis.md) | Concepts: key-value store, TTL, async client, usage patterns |
| 6 | [LiteLLM — Multi-Provider LLM](06-litellm.md) | Multi-model abstraction, fallback, retry, cost tracking |
| 7 | [LangGraph — Graph Orchestration](07-langgraph.md) | StateGraph, nodes, edges, conditional routing, state machines |
| 8 | [Workers — Async Processing](08-workers.md) | Consumer/Producer pattern, task processing, webhook delivery, HMAC |
| 9 | [Docker & Docker Compose](09-docker.md) | Multi-stage build, service orchestration, healthchecks, volumes |
| 10 | [Testing — Pytest & Mocking](10-testing.md) | pytest-asyncio, fixtures, monkeypatch, unittest.mock, TestClient |
| 11 | [Security](11-security.md) | API key auth, HMAC-SHA256, CORS, non-root containers, webhook signing |
| 12 | [Glossary](12-glossary.md) | Technical terms used in the project |

## 🎯 How to Use

1. Read documents in numerical order to understand the full stack
2. Each document includes **real code snippets** from the project with explanations
3. Theoretical concepts are presented **before** the code that implements them
4. Links for further reading are provided at the end of each section

## 🏗️ Full Stack

```
Python 3.11+ │ FastAPI │ Pydantic v2 │ LiteLLM │ LangGraph
aiokafka │ redis.asyncio │ httpx │ orjson │ Docker Compose
```

---

> **Note**: This documentation is a living document — it grows alongside the project.
