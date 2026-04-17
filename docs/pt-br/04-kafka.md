# 4. Apache Kafka — Event Streaming

## O Que É Apache Kafka?

**Apache Kafka** é uma plataforma de **streaming de eventos distribuída**. Pense nele como um "log distribuído" onde:
- **Produtores** publicam mensagens em **tópicos**
- **Consumidores** leem mensagens dos tópicos
- Mensagens são **persistidas no disco** (não perdem dados)
- Múltiplos consumidores podem ler o mesmo tópico independentemente

### Analogia Simples

Imagine uma esteira de fábrica (tópico). Um operário coloca caixas na esteira (produtor). Vários robôs pegam caixas da esteira para processar (consumidores). Se um robô quebrar, as caixas ficam na esteira esperando.

---

## Conceitos Fundamentais

### Tópicos (Topics)

Um tópico é como um "canal" ou "fila" onde mensagens são organizadas por categoria:

```yaml
# No projeto:
c2f_incoming_tasks     # Tarefas recebidas, esperando processamento
c2f_completed_tasks    # Tarefas processadas, esperando entrega
```

### Partições (Partitions)

Cada tópico é dividido em **partições** para paralelismo:

```yaml
# docker-compose.yml:
KAFKA_NUM_PARTITIONS: 3
```

```
Tópico: c2f_incoming_tasks
├── Partição 0: [msg1, msg4, msg7, ...]
├── Partição 1: [msg2, msg5, msg8, ...]
└── Partição 2: [msg3, msg6, msg9, ...]
```

- Cada partição é uma **fila ordenada**
- Mensagens com a mesma **key** vão para a mesma partição (garantia de ordem)
- No nosso caso, `task_id` é a key → todas as mensagens de uma task ficam na mesma partição

### Consumer Groups

```yaml
KAFKA_CONSUMER_GROUP: c2f-workers
```

Um consumer group permite que **múltiplos workers** dividam o trabalho:

```
Consumer Group: c2f-workers
├── Worker 1 ← Partição 0
├── Worker 2 ← Partição 1
└── Worker 3 ← Partição 2
```

- Cada partição é atribuída a **um único consumer** dentro do grupo
- Se Worker 2 cair, suas partições são redistribuídas (rebalance)
- Isso é a base da **escalabilidade horizontal**

### Offsets

Cada mensagem tem um **offset** (posição) na partição:

```
Partição 0: [offset=0] [offset=1] [offset=2] [offset=3] ...
                                      ↑
                              Consumer está aqui
```

- O consumer rastreia até onde leu via **committed offset**
- Se reiniciar, continua de onde parou
- `auto_offset_reset="earliest"` → se não houver offset salvo, começa do início

---

## KRaft Mode — Kafka Sem Zookeeper

Historicamente, Kafka dependia do **Apache Zookeeper** para coordenação. Desde a versão 3.3, Kafka suporta **KRaft** (Kafka Raft), eliminando essa dependência:

```yaml
# docker-compose.yml:
kafka:
  image: apache/kafka:latest
  environment:
    KAFKA_NODE_ID: 1
    KAFKA_PROCESS_ROLES: broker,controller    # Combina broker + controller
    KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
```

**Por que KRaft?**
- Menos um serviço para gerenciar (sem Zookeeper)
- Startup mais rápido
- Menor footprint de memória
- Arquitetura mais simples

---

## Listeners — Rede do Kafka

```yaml
KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:29092,CONTROLLER://0.0.0.0:9093,PLAINTEXT_HOST://0.0.0.0:9092
KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
```

Kafka precisa de múltiplos listeners porque existem diferentes "caminhos" de acesso:

| Listener | Porta | Usado por |
|----------|-------|-----------|
| `PLAINTEXT` | 29092 | Containers Docker (api, workers) |
| `PLAINTEXT_HOST` | 9092 | Host (seu PC, ferramentas de debug) |
| `CONTROLLER` | 9093 | Protocolo interno de consenso Raft |

---

## Implementação: Producer — `src/core/kafka_producer.py`

### Serialização

```python
def _serialize(value: Any) -> bytes:
    if isinstance(value, BaseModel):
        return orjson.dumps(value.model_dump(mode="json"))
    if isinstance(value, (dict, list)):
        return orjson.dumps(value)
    return orjson.dumps(value)
```

O Kafka trabalha com **bytes brutos**. Precisamos converter nossos objetos Python para bytes:
- `orjson.dumps()` é 3-10x mais rápido que `json.dumps()`
- Pydantic models são convertidos para dict primeiro com `model_dump()`

### Producer Singleton

```python
_producer: AIOKafkaProducer | None = None

async def start_producer() -> AIOKafkaProducer:
    global _producer
    _producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_serializer=_serialize,
        key_serializer=lambda k: k.encode("utf-8") if isinstance(k, str) else k,
        acks="all",                    # Espera confirmação de TODAS as réplicas
        enable_idempotence=True,       # Evita duplicação de mensagens
        retry_backoff_ms=100,          # Espera 100ms entre retries
        request_timeout_ms=30_000,     # Timeout de 30s
    )
    await _producer.start()
```

**Conceito: `acks="all"` (Acknowledgments)**
- `acks=0` → Não espera confirmação (rápido, mas pode perder dados)
- `acks=1` → Espera confirmação do líder
- `acks="all"` → Espera confirmação de **todas** as réplicas (mais seguro)

**Conceito: Idempotência**
- `enable_idempotence=True` garante que se o producer enviar a mesma mensagem 2x (por retry), o Kafka **deduplica** automaticamente
- Usa um ID de sequência interno para detectar duplicatas

### Publicando Eventos

```python
async def send_event(topic: str, value: Any, key: str | None = None) -> None:
    metadata = await _producer.send_and_wait(topic, value=value, key=key)
```

- `send_and_wait()` é **assíncrono** — libera o event loop enquanto espera o Kafka confirmar
- `key=task_id` garante que todas as mensagens da mesma task vão para a mesma partição

---

## Implementação: Consumer — `src/core/kafka_consumer.py`

### Classe Base Abstrata

```python
class BaseKafkaConsumer(ABC):
    def __init__(self, topic: str, settings: Settings | None = None):
        self.topic = topic
        self._consumer: AIOKafkaConsumer | None = None

    async def run(self) -> None:
        await self.start()
        async for msg in self._consumer:      # ← Loop infinito assíncrono
            await self.process_message(msg.value)

    @abstractmethod
    async def process_message(self, payload: dict[str, Any]) -> None:
        ...  # Subclasses implementam
```

**Conceito: Abstract Base Class (ABC)**
- `ABC` + `@abstractmethod` definem um **contrato**: "toda subclasse DEVE implementar `process_message()`"
- Se você tentar instanciar `BaseKafkaConsumer` diretamente, Python lança `TypeError`
- Permite que `TaskProcessorWorker` e `DeliveryWorker` compartilhem toda a lógica de conexão/loop

**Conceito: `async for`**
- `async for msg in self._consumer` é um **iterador assíncrono**
- Ele "pausa" esperando a próxima mensagem sem bloquear o event loop
- Quando uma mensagem chega, o loop continua

### Configuração do Consumer

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

- `auto_offset_reset="earliest"` → lê desde o início se nunca consumiu antes
- `enable_auto_commit=True` → salva o offset automaticamente a cada 5s
- `value_deserializer` → converte bytes de volta para dict Python

---

## Fluxo Kafka no Projeto

```
1. API recebe POST /submit
   │
2. send_event("c2f_incoming_tasks", TaskEvent, key=task_id)
   │
3. Kafka persiste no tópico, distribui nas partições
   │
4. TaskProcessorWorker.process_message() consome
   │
5. Processa no LangGraph + LiteLLM
   │
6. send_event("c2f_completed_tasks", TaskResultEvent, key=task_id)
   │
7. DeliveryWorker.process_message() consome
   │
8. Envia webhook POST para o Conn2Flow
```

---

## Anterior: [← Pydantic](03-pydantic.md) | Próximo: [Redis →](05-redis.md)
