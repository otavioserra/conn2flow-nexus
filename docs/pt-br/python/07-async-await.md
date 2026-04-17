# 07. Async/Await & Concorrência

## Por Que Async Importa?

### PHP Tradicional (Síncrono)
```php
// PHP bloqueia em cada chamada:
$user = $db->query("SELECT * FROM users WHERE id = 1");  // Espera...
$orders = $db->query("SELECT * FROM orders WHERE user_id = 1");  // Espera...
$payments = Http::get("https://api.stripe.com/charges");  // Espera...
// Total: soma dos tempos
```

### Python Async
```python
# Python async executa em paralelo:
user, orders, payments = await asyncio.gather(
    db.fetch("SELECT * FROM users WHERE id = $1", 1),
    db.fetch("SELECT * FROM orders WHERE user_id = $1", 1),
    httpx.get("https://api.stripe.com/charges"),
)
# Total: tempo da chamada mais lenta (não a soma!)
```

### Analogia simples:
- **Síncrono**: Faz um pedido no restaurante, espera chegar, faz outro pedido, espera...
- **Assíncrono**: Faz todos os pedidos de uma vez, a cozinha prepara em paralelo, você recebe tudo quase junto.

---

## `async def` — Funções Assíncronas (Coroutines)

```python
# Função normal (síncrona)
def get_user(user_id: int) -> dict:
    return db.query(f"SELECT * FROM users WHERE id = {user_id}")

# Função assíncrona (coroutine)
async def get_user(user_id: int) -> dict:
    return await db.fetch("SELECT * FROM users WHERE id = $1", user_id)
```

### Regras:
1. `async def` define uma coroutine
2. Dentro de `async def`, use `await` para esperar operações I/O
3. Só pode usar `await` dentro de `async def`
4. Chamar uma coroutine **sem await** retorna um objeto coroutine (não executa!)

```python
# ❌ Erro comum:
result = get_user(1)  # Retorna <coroutine object> — NÃO executa!

# ✅ Correto:
result = await get_user(1)  # Executa e retorna o resultado
```

---

## `await` — Cedendo Controle

`await` faz duas coisas:
1. **Espera** o resultado da coroutine
2. **Cede controle** para o event loop executar outras tarefas enquanto espera

```python
async def process():
    print("1. Iniciando")
    data = await fetch_from_api()  # Cede controle enquanto espera
    print("2. Dados recebidos")
    await save_to_db(data)         # Cede controle novamente
    print("3. Salvo no banco")
```

Enquanto `await fetch_from_api()` espera a resposta HTTP, o event loop pode executar outras coroutines.

---

## Event Loop — O Motor Async

```python
import asyncio

async def main():
    print("Hello")
    await asyncio.sleep(1)
    print("World")

# Iniciar o event loop
asyncio.run(main())
```

No **FastAPI**, o event loop já está rodando — você não precisa de `asyncio.run()`. Basta definir endpoints como `async def`:

```python
@router.get("/health")
async def health_check():
    # FastAPI já roda isso dentro do event loop
    redis_ok = await check_redis()
    return {"status": "healthy", "redis": redis_ok}
```

---

## `asyncio.gather()` — Execução Paralela

```python
async def process_all():
    # Executa em paralelo (concurrent)
    user, orders, settings = await asyncio.gather(
        fetch_user(1),
        fetch_orders(1),
        load_settings(),
    )
    return {"user": user, "orders": orders, "settings": settings}
```

### `gather` vs execução sequencial:
```python
# Sequencial — 3 segundos total
a = await slow_task_1()   # 1s
b = await slow_task_2()   # 1s
c = await slow_task_3()   # 1s

# Paralelo — 1 segundo total
a, b, c = await asyncio.gather(
    slow_task_1(),  # 1s ─┐
    slow_task_2(),  # 1s ─┤ Executam em paralelo
    slow_task_3(),  # 1s ─┘
)
```

### No nosso código:
```python
# src/api/endpoints/health.py
async def health_check():
    redis_ok = False
    kafka_ok = False

    try:
        r = get_redis()
        redis_ok = await r.ping()
    except Exception:
        pass

    # Sequencial neste caso — depende do resultado anterior
    # Se precisasse de paralelo, usaria gather()
```

---

## `async for` — Iteração Assíncrona

```python
# Kafka consumer — lê mensagens assincronamente
async for msg in consumer:
    data = orjson.loads(msg.value)
    await handle_message(data)
```

### No nosso código:
```python
# src/core/kafka_consumer.py
async def run(self) -> None:
    await self._start()
    try:
        async for msg in self._consumer:
            data = orjson.loads(msg.value)
            await self.handle_message(data)
    finally:
        await self._stop()
```

`async for` é como `for`, mas cada iteração pode envolver I/O assíncrono.

---

## `async with` — Context Managers Assíncronos

```python
# Conexão HTTP assíncrona
async with httpx.AsyncClient() as client:
    response = await client.post(url, json=data)
```

### No nosso código:
```python
# src/workers/delivery_worker.py
async with httpx.AsyncClient(timeout=30.0) as client:
    response = await client.post(
        webhook_url,
        json=result_event.model_dump(mode="json"),
        headers={"Content-Type": "application/json"},
    )
```

`async with` garante que recursos assíncronos sejam liberados corretamente (conexões HTTP, sessões de banco, etc.).

---

## Tasks — Execução em Background

```python
import asyncio

async def background_job():
    while True:
        await process_queue()
        await asyncio.sleep(5)

async def main():
    # Cria task em background
    task = asyncio.create_task(background_job())

    # Faz outras coisas...
    await handle_requests()

    # Cancela a task quando não precisa mais
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("Task cancelada")
```

---

## Timeouts

```python
import asyncio

# Timeout de 5 segundos
try:
    result = await asyncio.wait_for(slow_operation(), timeout=5.0)
except asyncio.TimeoutError:
    print("Operação expirou!")

# Python 3.11+ — TaskGroup com timeout
async with asyncio.timeout(5.0):
    result = await slow_operation()
```

---

## Armadilhas Comuns

### 1. Chamar async sem await
```python
# ❌ Retorna coroutine object, não executa!
result = fetch_data()

# ✅
result = await fetch_data()
```

### 2. Bloquear o event loop
```python
# ❌ Bloqueia o event loop inteiro!
import time
async def bad():
    time.sleep(5)  # Bloqueia TUDO por 5 segundos

# ✅ Cede controle
async def good():
    await asyncio.sleep(5)  # Permite outras tasks executarem
```

### 3. Misturar sync e async
```python
# ❌ Não pode usar await em função sync
def sync_function():
    data = await async_function()  # SyntaxError!

# ✅ Só await dentro de async def
async def async_function():
    data = await fetch_data()
```

### 4. Executar código CPU-intensive em async
```python
# ❌ Bloqueia o event loop
async def bad():
    result = heavy_computation()  # CPU-bound, bloqueia

# ✅ Use run_in_executor para CPU-bound
async def good():
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, heavy_computation)
```

---

## PHP Comparação Final

| PHP | Python async |
|-----|-------------|
| Execução sequencial natural | `async def` + `await` |
| Guzzle promises (async HTTP) | `httpx.AsyncClient` |
| ReactPHP / Swoole / Fibers | `asyncio` (nativo desde 3.4) |
| `Promise::all()` | `asyncio.gather()` |
| PHP não precisa — Apache/FPM gerencia processos | Python precisa — single-thread, event loop gerencia I/O |

---

## Anterior: [← Módulos & Pacotes](06-modulos-pacotes.md) | Próximo: [Context Managers →](08-context-managers.md)
