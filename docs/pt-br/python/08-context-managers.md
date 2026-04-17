# 08. Context Managers & Gerenciamento de Recursos

## O Que É um Context Manager?

Um context manager garante que **recursos sejam adquiridos e liberados corretamente**, mesmo se ocorrer um erro.

### PHP
```php
try {
    $file = fopen("data.txt", "r");
    $content = fread($file, filesize("data.txt"));
} finally {
    fclose($file);  // Precisa lembrar de fechar!
}
```

### Python
```python
with open("data.txt", "r") as file:
    content = file.read()
# Arquivo fechado AUTOMATICAMENTE ao sair do bloco!
```

`with` garante que o cleanup acontece — mesmo que uma exceção seja lançada.

---

## Sintaxe `with`

```python
# Arquivo
with open("data.txt", "w") as f:
    f.write("Hello")
# f.close() é chamado automaticamente

# Múltiplos resources (Python 3.10+)
with (
    open("input.txt") as src,
    open("output.txt", "w") as dst,
):
    dst.write(src.read())

# Pré-3.10
with open("input.txt") as src, open("output.txt", "w") as dst:
    dst.write(src.read())
```

---

## Criando Context Managers — Classe

### Protocol `__enter__` / `__exit__`
```python
class DatabaseConnection:
    def __init__(self, url: str) -> None:
        self.url = url
        self.conn = None

    def __enter__(self):
        """Chamado ao entrar no bloco with."""
        self.conn = connect(self.url)
        return self.conn  # Valor atribuído ao 'as'

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Chamado ao sair do bloco with (sempre!)."""
        if self.conn:
            self.conn.close()
        return False  # Não suprimir exceções

# Uso:
with DatabaseConnection("postgres://localhost/db") as conn:
    conn.execute("SELECT 1")
# conn.close() chamado automaticamente
```

### Parâmetros do `__exit__`:
- `exc_type` — Classe da exceção (ou None se não houve erro)
- `exc_val` — Instância da exceção
- `exc_tb` — Traceback
- Retornar `True` suprime a exceção (raramente usado)

---

## Criando Context Managers — `@contextmanager`

### Mais simples que a classe:
```python
from contextlib import contextmanager

@contextmanager
def timer(label: str):
    """Mede tempo de execução."""
    start = time.perf_counter()
    yield  # Aqui o bloco with é executado
    elapsed = time.perf_counter() - start
    print(f"{label}: {elapsed:.3f}s")

# Uso:
with timer("Database query"):
    result = db.execute("SELECT * FROM users")
# Output: Database query: 0.045s
```

### Como funciona:
1. Código antes do `yield` → `__enter__`
2. `yield valor` → valor atribuído ao `as`
3. Código depois do `yield` → `__exit__`

```python
@contextmanager
def managed_resource(name: str):
    print(f"Acquiring {name}")
    resource = acquire(name)
    try:
        yield resource        # Entrega o recurso ao bloco with
    finally:
        print(f"Releasing {name}")
        resource.release()    # Cleanup garantido
```

---

## `@asynccontextmanager` — Context Manager Async

### No nosso código:
```python
# src/main.py
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP — inicializa serviços
    settings = get_settings()
    await start_redis()
    await start_producer()
    logger.info("All services initialized")

    yield  # App está rodando

    # SHUTDOWN — libera recursos
    await stop_producer()
    await stop_redis()
    logger.info("Shutdown complete")

app = FastAPI(lifespan=lifespan)
```

### `async with` — Para resources assíncronos:
```python
# src/workers/delivery_worker.py
async with httpx.AsyncClient(timeout=30.0) as client:
    response = await client.post(webhook_url, json=data)
# Conexão HTTP fechada automaticamente
```

---

## Padrões Comuns

### Transação de Banco de Dados
```python
@contextmanager
def transaction(db):
    try:
        yield db
        db.commit()     # Sucesso → commit
    except Exception:
        db.rollback()   # Erro → rollback
        raise           # Re-lança a exceção

with transaction(db) as conn:
    conn.execute("INSERT INTO users ...")
    conn.execute("INSERT INTO orders ...")
# Se qualquer operação falhar, ambas são revertidas
```

### Lock / Mutex
```python
import threading

lock = threading.Lock()

with lock:
    # Apenas uma thread por vez
    shared_resource.update(data)
# Lock liberado automaticamente
```

### Async Lock
```python
import asyncio

lock = asyncio.Lock()

async with lock:
    # Apenas uma coroutine por vez
    await shared_resource.update(data)
```

### Diretório Temporário
```python
import tempfile

with tempfile.TemporaryDirectory() as tmpdir:
    # tmpdir é um path para um diretório temporário
    path = os.path.join(tmpdir, "data.json")
    with open(path, "w") as f:
        f.write("{}")
# Diretório e todos os arquivos deletados automaticamente
```

---

## `contextlib` — Utilitários

```python
from contextlib import suppress, redirect_stdout

# suppress — ignora exceções específicas
with suppress(FileNotFoundError):
    os.remove("maybe_missing.txt")
# Se FileNotFoundError for lançada, é silenciosamente ignorada

# redirect_stdout — redireciona print
from io import StringIO
f = StringIO()
with redirect_stdout(f):
    print("Captured!")
output = f.getvalue()  # "Captured!\n"
```

---

## PHP vs Python — Resumo

| PHP | Python |
|-----|--------|
| `try/finally` para cleanup | `with` statement |
| Sem equivalente direto | `@contextmanager` |
| Destructors `__destruct()` | `__exit__()` (mais confiável) |
| `fclose($file)` manual | Automático com `with open()` |

---

## Anterior: [← Async/Await](07-async-await.md) | Próximo: [Tratamento de Erros →](09-tratamento-erros.md)
