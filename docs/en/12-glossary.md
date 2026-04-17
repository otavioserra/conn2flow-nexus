# 12. Glossary

## A

**API (Application Programming Interface)** — Interface that defines how systems communicate with each other.

**API Key** — Secret string used to authenticate requests to an API.

**asyncio** — Python standard library for asynchronous programming using `async`/`await`.

**AsyncMock** — Mock from `unittest.mock` that supports `await`, used in async tests.

**await** — Keyword that pauses execution of a coroutine until the awaited operation completes.

## B

**Bind Mount** — Docker volume that maps a host directory directly into the container.

**Broker** — Kafka server that receives, stores, and delivers messages.

## C

**Consumer** — Component that reads messages from a Kafka topic.

**Consumer Group** — Set of consumers that share message processing. Each message is delivered to **one** consumer in the group.

**CORS (Cross-Origin Resource Sharing)** — HTTP mechanism that controls which domains can make cross-origin requests.

**Coroutine** — Async function (`async def`) that can be paused and resumed with `await`.

## D

**Dead Letter Queue (DLQ)** — Special topic/queue where failed messages are sent after exceeding retry attempts.

**Dependency Injection** — Pattern where dependencies are provided externally rather than created internally. In FastAPI, implemented with `Depends()`.

**Docker** — Platform for running applications in containers (isolated environments).

**Docker Compose** — Tool for defining and running multi-container Docker applications via a YAML file.

## E

**Endpoint** — Specific URL + HTTP method that responds to a request (e.g., `POST /api/v1/tasks/submit`).

**Event-Driven** — Architecture where components communicate via events/messages rather than direct calls.

**Event Loop** — Core asyncio mechanism that schedules and runs coroutines.

## F

**FastAPI** — Modern Python web framework built on Starlette and Pydantic, with automatic OpenAPI docs.

**Fixture** — pytest function that prepares the environment for tests (setup and teardown).

## G

**Graph (LangGraph)** — Directed graph of nodes, where each node is a function that transforms a state.

## H

**Healthcheck** — Endpoint or command that verifies if a service is running correctly.

**HMAC (Hash-based Message Authentication Code)** — Cryptographic signature that guarantees authenticity and integrity of a message.

**Hot-Reload** — Automatic code reloading when changes are detected (without manual restart).

## I

**Idempotent** — Operation that can be repeated multiple times with the same result.

## J

**JSON (JavaScript Object Notation)** — Lightweight data exchange format, used by the Nexus API.

## K

**Kafka** — Distributed streaming platform for high-throughput real-time messaging.

**KRaft** — Kafka mode without Zookeeper, using Raft protocol for metadata management.

## L

**LangGraph** — Library for building AI workflows as state graphs (part of the LangChain ecosystem).

**LiteLLM** — Library that provides a unified interface for multiple LLM providers (OpenAI, Anthropic, Ollama, etc.).

**LLM (Large Language Model)** — Large language model (GPT, Claude, Llama, etc.).

## M

**Middleware** — Code that runs **before** or **after** each request (e.g., CORS, auth, logging).

**Mock** — Simulated object that replaces a real dependency during tests.

**Monkeypatch** — pytest feature for temporarily modifying objects/variables during a test.

## N

**Named Volume** — Docker storage that persists data independently from containers.

## O

**Offset** — Sequential position of a message within a Kafka partition.

**OpenAPI** — Standard specification for describing REST APIs (used by Swagger/ReDoc).

## P

**Partition** — Kafka subdivision of a topic. Each partition is an ordered, immutable message log.

**Phinx** — PHP database migration tool (used in Conn2Flow Manager).

**Producer** — Component that publishes messages to a Kafka topic.

**Pydantic** — Python library for data validation using Python type annotations.

## R

**Redis** — In-memory key-value database, used for cache and task status tracking.

**REST (Representational State Transfer)** — API architecture style that uses HTTP methods (GET, POST, PUT, DELETE).

**Retry (Exponential Backoff)** — Strategy of retrying with progressively longer wait times between attempts.

## S

**Schema** — Data structure definition (in Pydantic, a class that validates input/output).

**Singleton** — Design pattern that ensures only one instance of an object (e.g., `KafkaProducer`, `Redis`).

**State Machine** — System that transitions between defined states (used in task lifecycle: pending → processing → completed/failed).

**Swagger UI** — Visual interface for exploring and testing an OpenAPI-described API.

## T

**TestClient** — FastAPI tool for simulating HTTP requests in tests without a real server.

**Topic** — Named channel in Kafka where messages are published and consumed.

**TTL (Time-To-Live)** — Lifespan of a record in Redis (after TTL, the key is automatically deleted).

## U

**UUID (Universally Unique Identifier)** — 128-bit unique identifier (e.g., `550e8400-e29b-41d4-a716-446655440000`).

**Uvicorn** — ASGI server that runs FastAPI (supports async and HTTP/2).

## W

**Webhook** — HTTP callback — Nexus sends results to a Conn2Flow URL upon task completion.

**Worker** — Background process that continuously consumes messages from Kafka and processes them.

---

## Previous: [← Security](11-security.md)
