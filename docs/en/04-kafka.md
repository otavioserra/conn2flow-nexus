# 4. Apache Kafka — Event Streaming

## What Is Apache Kafka?

**Apache Kafka** is a **distributed event streaming platform**. Think of it as a "distributed log" where:
- **Producers** publish messages to **topics**
- **Consumers** read messages from topics
- Messages are **persisted to disk** (data is not lost)
- Multiple consumers can read the same topic independently

### Simple Analogy

Imagine a factory conveyor belt (topic). A worker places boxes on the belt (producer). Several robots pick boxes from the belt to process (consumers). If a robot breaks down, the boxes stay on the belt waiting.

---

## Fundamental Concepts

### Topics

A topic is like a "channel" or "queue" where messages are organized by category:

```yaml
# In the project:
c2f_incoming_tasks     # Received tasks, waiting for processing
c2f_completed_tasks    # Processed tasks, waiting for delivery
```

### Partitions

Each topic is divided into **partitions** for parallelism:

```yaml
# docker-compose.yml:
KAFKA_NUM_PARTITIONS: 3
```

```
Topic: c2f_incoming_tasks
├── Partition 0: [msg1, msg4, msg7, ...]
├── Partition 1: [msg2, msg5, msg8, ...]
└── Partition 2: [msg3, msg6, msg9, ...]
```

- Each partition is an **ordered queue**
- Messages with the same **key** go to the same partition (order guarantee)
- In our case, `task_id` is the key → all messages for a task stay in the same partition

### Consumer Groups

```yaml
KAFKA_CONSUMER_GROUP: c2f-workers
```

A consumer group allows **multiple workers** to share the work:

```
Consumer Group: c2f-workers
├── Worker 1 ← Partition 0
├── Worker 2 ← Partition 1
└── Worker 3 ← Partition 2
```

- Each partition is assigned to **one consumer** within the group
- If Worker 2 crashes, its partitions are redistributed (rebalance)
- This is the foundation of **horizontal scalability**

### Offsets

Each message has an **offset** (position) within the partition:

```
Partition 0: [offset=0] [offset=1] [offset=2] [offset=3] ...
                                      ↑
                              Consumer is here
```

- The consumer tracks how far it has read via **committed offset**
- If it restarts, it continues from where it left off
- `auto_offset_reset="earliest"` → if no saved offset, starts from the beginning

---

## KRaft Mode — Kafka Without Zookeeper

Historically, Kafka depended on **Apache Zookeeper** for coordination. Since version 3.3, Kafka supports **KRaft** (Kafka Raft), eliminating this dependency:

```yaml
# docker-compose.yml:
kafka:
  image: apache/kafka:latest
  environment:
    KAFKA_NODE_ID: 1
    KAFKA_PROCESS_ROLES: broker,controller    # Combines broker + controller
    KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
```

**Why KRaft?**
- One less service to manage (no Zookeeper)
- Faster startup
- Smaller memory footprint
- Simpler architecture

---

## Listeners — Kafka Networking

```yaml
KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:29092,CONTROLLER://0.0.0.0:9093,PLAINTEXT_HOST://0.0.0.0:9092
KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
```

Kafka needs multiple listeners because there are different access paths:

| Listener | Port | Used By |
|----------|------|---------|
| `PLAINTEXT` | 29092 | Docker containers (api, workers) |
| `PLAINTEXT_HOST` | 9092 | Host (your PC, debug tools) |
| `CONTROLLER` | 9093 | Internal Raft consensus protocol |

---

## Implementation: Producer — `src/core/kafka_producer.py`

### Serialization

```python
def _serialize(value: Any) -> bytes:
    if isinstance(value, BaseModel):
        return orjson.dumps(value.model_dump(mode="json"))
    if isinstance(value, (dict, list)):
        return orjson.dumps(value)
    return orjson.dumps(value)
```

Kafka works with **raw bytes**. We need to convert our Python objects to bytes:
- `orjson.dumps()` is 3-10x faster than `json.dumps()`
- Pydantic models are converted to dict first with `model_dump()`

### Producer Singleton

```python
_producer: AIOKafkaProducer | None = None

async def start_producer() -> AIOKafkaProducer:
    global _producer
    _producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_serializer=_serialize,
        key_serializer=lambda k: k.encode("utf-8") if isinstance(k, str) else k,
        acks="all",                    # Waits for ALL replicas to confirm
        enable_idempotence=True,       # Prevents message duplication
        retry_backoff_ms=100,          # Waits 100ms between retries
        request_timeout_ms=30_000,     # 30s timeout
    )
    await _producer.start()
```

**Concept: `acks="all"` (Acknowledgments)**
- `acks=0` → Doesn't wait for confirmation (fast, but may lose data)
- `acks=1` → Waits for leader confirmation
- `acks="all"` → Waits for confirmation from **all** replicas (most secure)

**Concept: Idempotence**
- `enable_idempotence=True` ensures that if the producer sends the same message twice (due to retry), Kafka **deduplicates** automatically
- Uses an internal sequence ID to detect duplicates

### Publishing Events

```python
async def send_event(topic: str, value: Any, key: str | None = None) -> None:
    metadata = await _producer.send_and_wait(topic, value=value, key=key)
```

- `send_and_wait()` is **asynchronous** — frees the event loop while waiting for Kafka confirmation
- `key=task_id` ensures all messages for the same task go to the same partition

---

## Implementation: Consumer — `src/core/kafka_consumer.py`

### Abstract Base Class

```python
class BaseKafkaConsumer(ABC):
    def __init__(self, topic: str, settings: Settings | None = None):
        self.topic = topic
        self._consumer: AIOKafkaConsumer | None = None

    async def run(self) -> None:
        await self.start()
        async for msg in self._consumer:      # ← Infinite async loop
            await self.process_message(msg.value)

    @abstractmethod
    async def process_message(self, payload: dict[str, Any]) -> None:
        ...  # Subclasses implement
```

**Concept: Abstract Base Class (ABC)**
- `ABC` + `@abstractmethod` define a **contract**: "every subclass MUST implement `process_message()`"
- If you try to instantiate `BaseKafkaConsumer` directly, Python raises `TypeError`
- Allows `TaskProcessorWorker` and `DeliveryWorker` to share all connection/loop logic

**Concept: `async for`**
- `async for msg in self._consumer` is an **asynchronous iterator**
- It "pauses" waiting for the next message without blocking the event loop
- When a message arrives, the loop continues

### Consumer Configuration

```python
self._consumer = AIOKafkaConsumer(
    self.topic,
    group_id=self.settings.kafka_consumer_group,
    value_deserializer=lambda v: orjson.loads(v) if v else None,
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    auto_commit_interval_ms=5_000,
)
```

- `auto_offset_reset="earliest"` → reads from the beginning if never consumed before
- `enable_auto_commit=True` → saves offset automatically every 5s
- `value_deserializer` → converts bytes back to Python dict

---

## Kafka Flow in the Project

```
1. API receives POST /submit
   │
2. send_event("c2f_incoming_tasks", TaskEvent, key=task_id)
   │
3. Kafka persists to topic, distributes across partitions
   │
4. TaskProcessorWorker.process_message() consumes
   │
5. Processes via LangGraph + LiteLLM
   │
6. send_event("c2f_completed_tasks", TaskResultEvent, key=task_id)
   │
7. DeliveryWorker.process_message() consumes
   │
8. Sends webhook POST to Conn2Flow
```

---

## Previous: [← Pydantic](03-pydantic.md) | Next: [Redis →](05-redis.md)
