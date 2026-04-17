# Conn2Flow Nexus AI

**AI Gateway** — Private microservice that acts as a Man-in-the-Middle between the Conn2Flow platform and multiple AI providers.

## Stack

| Component | Technology |
|---|---|
| Web Framework | FastAPI |
| Validation | Pydantic v2 |
| Configuration | pydantic-settings |
| Multi-LLM | LiteLLM |
| Agent Orchestration | LangGraph |
| Event Streaming | Apache Kafka (KRaft) |
| Cache / State | Redis |
| HTTP Client | httpx |
| Containerization | Docker Compose |

## Architecture

```
Conn2Flow ──► [FastAPI API] ──► Kafka (c2f_incoming_tasks)
                                        │
                                        ▼
                                [Task Worker] ──► LiteLLM ──► OpenAI / Claude / Gemini / Groq
                                        │
                                        ▼
                                Kafka (c2f_completed_tasks)
                                        │
                                        ▼
                                [Delivery Worker] ──► Webhook POST ──► Conn2Flow
```

## Quick Start

```bash
# 1. Clone
git clone https://github.com/otavioserra/conn2flow-nexus.git
cd conn2flow-nexus

# 2. Configure
cp .env.example .env
# Edit .env with your API keys

# 3. Start everything
docker compose up -d

# 4. Test
curl http://localhost:8000/api/v1/health
```

## Project Structure

```
conn2flow-nexus/
├── docker-compose.yml          # Kafka + Redis + API + Workers
├── Dockerfile                  # Multi-stage build
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── src/
│   ├── main.py                 # FastAPI app entry point
│   ├── config/
│   │   └── settings.py         # pydantic-settings (loads .env)
│   ├── api/
│   │   ├── router.py           # Aggregates endpoints
│   │   ├── endpoints/
│   │   │   ├── health.py       # GET /api/v1/health
│   │   │   └── tasks.py        # POST /api/v1/tasks/submit → 202
│   │   └── schemas/
│   │       ├── requests.py     # TaskRequest (Pydantic)
│   │       └── responses.py    # TaskAcceptedResponse (Pydantic)
│   ├── core/
│   │   ├── kafka_producer.py   # Async Kafka producer
│   │   ├── kafka_consumer.py   # Base consumer class
│   │   ├── redis_client.py     # Redis singleton
│   │   └── llm_router.py      # LiteLLM multi-model router
│   ├── workers/
│   │   ├── task_processor.py   # Consumer: incoming → LLM → completed
│   │   └── delivery_worker.py  # Consumer: completed → Webhook
│   ├── graphs/
│   │   └── base_graph.py       # LangGraph state machines
│   └── models/
│       └── events.py           # TaskEvent, TaskResultEvent
└── tests/
```

## License

Proprietary — Conn2Flow © 2026
