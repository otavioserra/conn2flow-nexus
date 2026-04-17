# 📚 Conn2Flow Nexus AI — Documentação

Bem-vindo à documentação técnica e didática do **Conn2Flow Nexus AI**.

Este guia foi criado para servir como **material de aprendizado**, explicando cada conceito, padrão de design e tecnologia utilizada no projeto, com referências diretas ao código-fonte.

## 📖 Índice

| # | Documento | Descrição |
|---|-----------|-----------|
| 1 | [Visão Geral da Arquitetura](01-arquitetura-geral.md) | Arquitetura de microsserviço event-driven, fluxo de dados e decisões de design |
| 2 | [FastAPI — Web Framework](02-fastapi.md) | Conceitos: ASGI, lifespan, dependency injection, middleware, Pydantic schemas |
| 3 | [Pydantic — Validação e Schemas](03-pydantic.md) | Validação de dados, BaseModel, Field, model_validator, pydantic-settings |
| 4 | [Apache Kafka — Event Streaming](04-kafka.md) | Conceitos: brokers, tópicos, partições, consumer groups, KRaft, aiokafka |
| 5 | [Redis — Cache e Estado](05-redis.md) | Conceitos: key-value store, TTL, async client, padrões de uso |
| 6 | [LiteLLM — Multi-Provider LLM](06-litellm.md) | Abstração multi-modelo, fallback, retry, cost tracking |
| 7 | [LangGraph — Orquestração com Grafos](07-langgraph.md) | StateGraph, nodes, edges, routing condicional, state machines |
| 8 | [Workers — Processamento Assíncrono](08-workers.md) | Padrão Consumer/Producer, task processing, webhook delivery, HMAC |
| 9 | [Docker & Docker Compose](09-docker.md) | Multi-stage build, orquestração de serviços, healthchecks, volumes |
| 10 | [Testes — Pytest & Mocking](10-testes.md) | pytest-asyncio, fixtures, monkeypatch, unittest.mock, TestClient |
| 11 | [Segurança](11-seguranca.md) | API key auth, HMAC-SHA256, CORS, non-root containers, webhook signing |
| 12 | [Glossário](12-glossario.md) | Termos técnicos utilizados no projeto |

## 🎯 Como Usar

1. Leia os documentos na ordem numérica para entender a stack completa
2. Cada documento inclui **trechos de código reais** do projeto com explicações
3. Conceitos teóricos são apresentados **antes** do código que os implementa
4. Ao final de cada seção há links para aprofundamento

## 🏗️ Stack Completa

```
Python 3.11+ │ FastAPI │ Pydantic v2 │ LiteLLM │ LangGraph
aiokafka │ redis.asyncio │ httpx │ orjson │ Docker Compose
```

---

> **Nota**: Esta documentação é viva — ela cresce junto com o projeto.
