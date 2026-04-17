# 04. Funções, Closures & Decorators

## Funções Básicas

### PHP
```php
function greet(string $name, string $greeting = "Hello"): string {
    return "$greeting, $name!";
}
```

### Python
```python
def greet(name: str, greeting: str = "Hello") -> str:
    """Retorna uma saudação formatada."""
    return f"{greeting}, {name}!"
```

### Diferenças-chave:
- `def` em vez de `function`
- `:` ao final da assinatura
- Type hints opcionais (mas recomendados)
- `->` para tipo de retorno
- **Docstring** (primeira string do corpo) em vez de `/** */`

---

## Argumentos — `*args` e `**kwargs`

### PHP
```php
function log(string $level, string ...$messages): void {
    foreach ($messages as $msg) {
        echo "[$level] $msg\n";
    }
}
log("INFO", "Starting", "Loading config");
```

### Python
```python
# *args — argumentos posicionais variáveis (como tupla)
def log(level: str, *messages: str) -> None:
    for msg in messages:
        print(f"[{level}] {msg}")

log("INFO", "Starting", "Loading config")
# messages = ("Starting", "Loading config")

# **kwargs — argumentos nomeados variáveis (como dict)
def create_user(**kwargs: Any) -> dict:
    return {"created_at": datetime.now(), **kwargs}

create_user(name="Alice", age=30)
# kwargs = {"name": "Alice", "age": 30}

# Combinados
def flexible(required: str, *args: int, **kwargs: str) -> None:
    print(required)  # Argumento obrigatório
    print(args)      # Tupla de extras posicionais
    print(kwargs)    # Dict de extras nomeados
```

### No nosso código:
```python
# src/core/llm_router.py
async def call_llm(model: str, messages: list, **kwargs) -> dict:
    # kwargs captura: temperature, max_tokens, etc.
    response = await acompletion(model=candidate, messages=messages, **kwargs)
```

`**kwargs` permite passar parâmetros opcionais sem listá-los todos explicitamente.

---

## Argumentos Apenas por Nome (keyword-only)

```python
def connect(host: str, *, port: int = 5432, ssl: bool = True) -> None:
    ...

connect("localhost", port=8000)       # ✅ OK
connect("localhost", 8000)             # ❌ TypeError! port é keyword-only
```

O `*` na assinatura força todos os argumentos seguintes a serem nomeados. Isso previne erros de ordem.

---

## Lambda — Funções Anônimas

### PHP
```php
$double = fn($n) => $n * 2;
$double(5);  // 10
```

### Python
```python
double = lambda n: n * 2
double(5)  # 10

# Uso comum: como argumento
sorted(users, key=lambda u: u["age"])
```

### Limitações do lambda:
- **Apenas uma expressão** (sem `if`, `for`, `=`)
- Se precisar de múltiplas linhas, use `def`

---

## Closures

### PHP
```php
function multiplier(int $factor): Closure {
    return fn(int $n): int => $n * $factor;
}
$triple = multiplier(3);
$triple(5);  // 15
```

### Python
```python
def multiplier(factor: int):
    def multiply(n: int) -> int:
        return n * factor  # factor é capturado do escopo externo
    return multiply

triple = multiplier(3)
triple(5)  # 15
```

Python captura variáveis do escopo externo automaticamente (sem `use`).

### `nonlocal` — Modificar Variável do Escopo Externo
```python
def counter():
    count = 0
    def increment():
        nonlocal count  # Sem isso, Python criaria uma variável local!
        count += 1
        return count
    return increment

c = counter()
c()  # 1
c()  # 2
c()  # 3
```

---

## Decorators — O Superpoder do Python

### Conceito
Um decorator é uma **função que envolve outra função**, adicionando comportamento antes/depois sem modificar o código original.

### PHP (sem decorators nativos)
```php
// PHP não tem decorators — usa middleware, traits, ou chamadas manuais
function withLogging(Closure $fn): Closure {
    return function(...$args) use ($fn) {
        echo "Calling function\n";
        $result = $fn(...$args);
        echo "Function returned\n";
        return $result;
    };
}
$logged = withLogging(fn() => "hello");
```

### Python — Sintaxe `@`
```python
import functools

def log_calls(func):
    @functools.wraps(func)  # Preserva nome e docstring originais
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"{func.__name__} returned {result}")
        return result
    return wrapper

@log_calls
def add(a: int, b: int) -> int:
    return a + b

add(2, 3)
# Output:
# Calling add
# add returned 5
```

`@log_calls` é açúcar sintático para: `add = log_calls(add)`

### Decorator com Argumentos
```python
def retry(times: int = 3, delay: float = 1.0):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(times):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == times - 1:
                        raise
                    await asyncio.sleep(delay)
        return wrapper
    return decorator

@retry(times=5, delay=0.5)
async def call_api():
    ...
```

### Decorator para Async
```python
def log_execution_time(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info(f"{func.__name__} levou {elapsed:.3f}s")
        return result
    return wrapper

@log_execution_time
async def process_task(task_id: str):
    ...
```

### Decorators no Nosso Código

#### `@lru_cache` — Cache de Resultado
```python
# src/config/settings.py
from functools import lru_cache

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

#### `@router.post()` — Registra Rota
```python
# src/api/endpoints/tasks.py
@router.post("/submit", response_model=TaskAcceptedResponse, status_code=202)
async def submit_task(payload: TaskRequest, ...):
    ...
```

#### `@abstractmethod` — Método Abstrato
```python
# src/core/kafka_consumer.py
from abc import ABC, abstractmethod

class BaseKafkaConsumer(ABC):
    @abstractmethod
    async def handle_message(self, data: dict) -> None:
        ...
```

#### `@field_validator` e `@model_validator` — Validação Pydantic
```python
# src/config/settings.py
@model_validator(mode="after")
def _warn_missing_keys(self) -> "Settings":
    ...
```

---

## `functools` — Utilitários para Funções

```python
import functools

# @functools.wraps — preserva metadata da função original
def my_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

# @lru_cache — memoização
@functools.lru_cache(maxsize=128)
def fibonacci(n: int) -> int:
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# functools.partial — aplicação parcial
from functools import partial
int_from_binary = partial(int, base=2)
int_from_binary("1010")  # 10
```

---

## Funções como Objetos de Primeira Classe

```python
# Funções são valores — podem ser atribuídas, passadas, retornadas
def shout(text: str) -> str:
    return text.upper()

def whisper(text: str) -> str:
    return text.lower()

def greet(func, name: str) -> str:
    return func(f"Hello, {name}!")

greet(shout, "World")    # "HELLO, WORLD!"
greet(whisper, "World")  # "hello, world!"

# Armazenar em dict (Strategy Pattern)
strategies = {
    "loud": shout,
    "quiet": whisper,
}
strategies["loud"]("Hello")  # "HELLO"
```

---

## Anterior: [← Estruturas de Dados](03-estruturas-dados.md) | Próximo: [OOP em Python →](05-oop.md)
