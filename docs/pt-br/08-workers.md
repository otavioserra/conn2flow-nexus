# 8. Workers — Processamento Assíncrono

## Conceito: Worker Pattern

**Workers** são processos independentes que rodam em containers separados. No nosso projeto:

| Worker | Consome de | Produz em | Função |
|--------|-----------|-----------|--------|
| `TaskProcessorWorker` | `c2f_incoming_tasks` | `c2f_completed_tasks` | Roda LangGraph + LiteLLM |
| `DeliveryWorker` | `c2f_completed_tasks` | — | Envia webhook para Conn2Flow |

### Por que processos separados?

1. **Isolamento de falhas** — se o worker LLM travar, a API continua recebendo tasks
2. **Escala independente** — podemos ter 1 API e 10 workers LLM
3. **Recursos dedicados** — workers LLM usam mais memória que a API
4. **Restart granular** — reiniciar um worker não afeta os outros

---

## Task Processor Worker: `src/workers/task_processor.py`

### Herança do BaseKafkaConsumer

```python
class TaskProcessorWorker(BaseKafkaConsumer):
    async def process_message(self, payload: dict[str, Any]) -> None:
        task_id = payload.get("task_id", "unknown")
        model = payload.get("model", self.settings.default_model)
        messages = payload.get("messages", [])
```

**Conceito: Template Method Pattern**
- `BaseKafkaConsumer.run()` define o **algoritmo**: conectar → loop → processar → tratar erro
- `process_message()` é o **step customizável** — cada worker implementa sua lógica
- O loop, retry e shutdown são herdados — zero duplicação

### Fluxo de Processamento

```python
# 1. Atualiza status para "processing"
await set_task_status(task_id, "processing", {"model": model})

# 2. Executa o grafo LangGraph
result_state = await run_task_graph(
    task_id=task_id,
    model=model,
    messages=messages,
    temperature=temperature,
    max_tokens=max_tokens,
)

# 3. Monta o evento de resultado
if result_state.get("error"):
    result_event = TaskResultEvent(
        task_id=task_id,
        status="failed",
        error=result_state["error"],
        ...
    )
    await set_task_status(task_id, "failed", {"error": ...})
    await incr_metric("tasks_failed")
else:
    result_event = TaskResultEvent(
        task_id=task_id,
        status="completed",
        result={"content": llm_response.get("content", "")},
        usage=llm_response.get("usage"),
        ...
    )
    await set_task_status(task_id, "completed", {...})
    await incr_metric("tasks_completed")

# 4. Publica resultado no Kafka
await send_event(
    topic=self.settings.kafka_topic_completed,
    value=result_event,
    key=task_id,
)
```

### Entry Point do Worker

```python
async def main() -> None:
    settings = get_settings()
    logging.basicConfig(...)

    await start_redis()
    await start_producer()

    worker = TaskProcessorWorker(
        topic=settings.kafka_topic_incoming,
        settings=settings,
    )

    try:
        await worker.run()  # ← Loop infinito
    finally:
        await stop_producer()
        await stop_redis()

if __name__ == "__main__":
    asyncio.run(main())
```

**Conceito: `asyncio.run()`**
- Cria um event loop, roda a coroutine `main()` e fecha o loop quando terminar
- É o ponto de entrada para código assíncrono Python
- Equivalente a `new Promise().then()` no JavaScript

**Conceito: `if __name__ == "__main__"`**
- Roda **apenas** quando o arquivo é executado diretamente
- Não roda quando é importado por outro módulo
- No Docker: `command: ["python", "-m", "src.workers.task_processor"]`

---

## Delivery Worker: `src/workers/delivery_worker.py`

### HMAC-SHA256 — Assinatura de Webhook

```python
import hmac
import hashlib

def _sign_payload(payload_bytes: bytes, secret: str) -> str:
    return hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()
```

**Conceito: HMAC (Hash-based Message Authentication Code)**
- HMAC garante que a mensagem **não foi alterada** e **veio de quem diz**
- O remetente (Nexus AI) e o destinatário (Conn2Flow) compartilham um **segredo**
- O remetente calcula: `HMAC(payload, segredo)` → assinatura
- O destinatário recalcula e compara — se diferente, a mensagem foi adulterada

**Como funciona:**
```
Payload: {"task_id": "abc", "result": "Hello"}
Segredo: "minha-chave-secreta"
HMAC-SHA256 → "a1b2c3d4e5f6..." (64 caracteres hex)
```

**Headers do webhook:**
```python
headers = {
    "Content-Type": "application/json",
    "X-C2F-Signature": f"sha256={signature}",   # Assinatura HMAC
    "X-C2F-Task-ID": task_id,                   # ID da task
    "User-Agent": "Conn2Flow-Nexus-AI/0.1",     # Identifica o remetente
}
```

### Retry com Backoff Exponencial

```python
MAX_RETRIES = 5
RETRY_BASE_DELAY = 2  # segundos

for attempt in range(1, MAX_RETRIES + 1):
    try:
        response = await client.post(webhook_url, content=body_bytes, headers=headers)
        if response.status_code < 300:
            delivered = True
            break
    except httpx.TimeoutException:
        ...
    except httpx.RequestError as exc:
        ...

    # Backoff exponencial: 2s, 4s, 8s, 16s, 32s
    if attempt < MAX_RETRIES:
        delay = RETRY_BASE_DELAY ** attempt
        await asyncio.sleep(delay)
```

**Conceito: Exponential Backoff**
- Em vez de tentar imediatamente, espera cada vez mais entre tentativas
- Tentativa 1: espera 2¹ = 2s
- Tentativa 2: espera 2² = 4s
- Tentativa 3: espera 2³ = 8s
- Tentativa 4: espera 2⁴ = 16s
- Tentativa 5: falha definitiva

**Por que backoff exponencial?**
- Se o servidor destino está sobrecarregado, retry imediato **piora** o problema
- Esperar mais a cada vez dá tempo para o servidor se recuperar
- É o padrão da indústria para retry de chamadas de rede

### httpx — Client HTTP Assíncrono

```python
async with httpx.AsyncClient(timeout=30) as client:
    response = await client.post(
        webhook_url,
        content=body_bytes,
        headers=headers,
    )
```

**Conceito: `async with` (Async Context Manager)**
- `async with httpx.AsyncClient()` garante que o client é **fechado** ao final
- Mesmo em caso de exceção, os recursos de rede são liberados
- `content=body_bytes` envia bytes brutos (já serializados com orjson)

---

## Como Workers Rodam no Docker

```yaml
# docker-compose.yml:
worker-task:
  command: ["python", "-m", "src.workers.task_processor"]
  depends_on:
    kafka: { condition: service_healthy }
    redis: { condition: service_healthy }

worker-delivery:
  command: ["python", "-m", "src.workers.delivery_worker"]
  depends_on:
    kafka: { condition: service_healthy }
    redis: { condition: service_healthy }
```

- Cada worker é um **container separado** usando a mesma imagem Docker
- `command` sobrescreve o `CMD` do Dockerfile (que roda uvicorn por padrão)
- `depends_on + condition: service_healthy` garante que Kafka e Redis estão prontos

---

## Anterior: [← LangGraph](07-langgraph.md) | Próximo: [Docker →](09-docker.md)
