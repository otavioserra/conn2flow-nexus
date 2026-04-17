# 02. Type Hints & Sistema de Tipos

## PHP vs Python — Tipagem

| PHP | Python |
|-----|--------|
| Tipagem fraca (coerção implícita) | Tipagem forte (sem coerção) |
| `declare(strict_types=1);` | Sempre strict por padrão |
| `function f(string $s): int` | `def f(s: str) -> int:` |
| Tipos reforçados em runtime | Tipos **NÃO** reforçados em runtime! |

### A grande diferença:
```python
# Python NÃO recusa em runtime:
def greet(name: str) -> str:
    return f"Hello, {name}!"

greet(42)  # ✅ Roda sem erro! Python ignora o hint em runtime.
```

Type hints são para:
1. **IDEs** — autocompletar, navegação
2. **Type checkers** — mypy, pyright (análise estática)
3. **Documentação** — código auto-documentado
4. **Frameworks** — Pydantic e FastAPI USAM os hints em runtime

---

## Sintaxe Básica

### PHP
```php
function add(int $a, int $b): int {
    return $a + $b;
}
```

### Python
```python
def add(a: int, b: int) -> int:
    return a + b
```

### Variáveis
```python
name: str = "Conn2Flow"
version: int = 1
price: float = 19.99
active: bool = True
data: None = None
```

Na prática, **não precisa anotar variáveis locais** — o type checker infere:
```python
name = "Conn2Flow"    # Inferido como str
version = 1           # Inferido como int
```

Anotações de variável são úteis quando o tipo não é óbvio:
```python
items: list[str] = []          # Sem anotação: list[Unknown]
cache: dict[str, int] = {}     # dict vazio — tipo não é inferido
```

---

## Tipos Básicos

```python
# Primitivos
x: int = 42
y: float = 3.14
z: str = "hello"
w: bool = True
n: None = None

# Coleções (genéricos com [])
names: list[str] = ["Alice", "Bob"]
ages: dict[str, int] = {"Alice": 30, "Bob": 25}
coords: tuple[float, float] = (1.0, 2.0)
unique: set[int] = {1, 2, 3}

# Coleções aninhadas
matrix: list[list[int]] = [[1, 2], [3, 4]]
config: dict[str, list[str]] = {"models": ["gpt-4o", "claude"]}
```

---

## `str | None` — Union Types (Python 3.10+)

### PHP
```php
function find(?string $name): ?User {
    // ?string = string|null
}
```

### Python (moderno — 3.10+)
```python
def find(name: str | None) -> User | None:
    ...
```

### Python (compatibilidade — 3.9 e anterior)
```python
from typing import Optional, Union

def find(name: Optional[str]) -> Optional[User]:
    ...
# Optional[X] é EXATAMENTE Union[X, None]
```

### No nosso código:
```python
# src/api/schemas/requests.py
max_tokens: int | None = Field(default=None, gt=0, le=128000)
webhook_url: str | None = Field(default=None)
```

---

## `typing` — Módulo de Tipos Avançados

```python
from typing import Any, Union, Optional, Literal, TypeAlias

# Any — qualquer tipo (escape hatch)
metadata: dict[str, Any] = {"key": "value", "count": 42}

# Union — múltiplos tipos (pré-3.10)
value: Union[str, int] = "hello"

# Optional — None ou o tipo (pré-3.10)
name: Optional[str] = None  # == Union[str, None] == str | None

# Literal — valores específicos
status: Literal["queued", "processing", "completed", "failed"]

# TypeAlias — alias para tipos complexos
MessageList: TypeAlias = list[dict[str, str]]
def process(messages: MessageList) -> None: ...
```

### No nosso código:
```python
# src/models/events.py
metadata: dict[str, Any] = Field(default_factory=dict)
# Any porque metadata pode conter qualquer tipo de valor
```

---

## Tipos Callable

```python
from typing import Callable, Awaitable

# Função que recebe str e retorna int
parser: Callable[[str], int] = int

# Função async
handler: Callable[[dict], Awaitable[None]]

# Callback sem argumentos
on_complete: Callable[[], None]
```

### No contexto de FastAPI:
```python
# Depends() aceita um Callable que retorna o tipo esperado
settings: Settings = Depends(get_settings)
# get_settings é Callable[[], Settings]
```

---

## Generics — Tipos Parametrizados

```python
from typing import TypeVar, Generic

T = TypeVar("T")

class Repository(Generic[T]):
    def __init__(self) -> None:
        self._items: list[T] = []

    def add(self, item: T) -> None:
        self._items.append(item)

    def get_all(self) -> list[T]:
        return self._items

# Uso:
user_repo = Repository[User]()
user_repo.add(User(name="Alice"))  # Aceita User
```

### PHP 8.x (sem generics nativos):
```php
/** @template T */
class Repository {
    /** @var T[] */
    private array $items = [];

    /** @param T $item */
    public function add($item): void { ... }
}
```

Python generics são **nativos na linguagem** — PHP depende de PHPDoc annotations.

---

## `TypedDict` — Dicts com Chaves Tipadas

```python
from typing import TypedDict

class Message(TypedDict):
    role: str
    content: str

# Tipo-safe — IDE sabe as chaves disponíveis
msg: Message = {"role": "user", "content": "Hello"}
msg["role"]     # ✅ IDE autocompletea
msg["invalid"]  # ❌ Type checker reclama
```

### Quando usar:
- **Dict simples com chaves conhecidas** → `TypedDict`
- **Validação + serialização** → `pydantic.BaseModel` (preferido no Nexus)

---

## `from __future__ import annotations`

```python
from __future__ import annotations

class Node:
    def __init__(self, children: list[Node]) -> None:
        # Sem o import, isso daria erro:
        # Node ainda não está definido quando Python lê a anotação
        self.children = children
```

Este import faz todas as anotações serem **avaliadas como strings** (lazy), resolvendo referências circulares e forward references.

---

## Dicas Práticas

### 1. Anote parâmetros e retorno de funções:
```python
# ✅ Bom
def process_task(task_id: str, model: str) -> dict[str, Any]:
    ...

# ❌ Evite
def process_task(task_id, model):
    ...
```

### 2. Use `| None` em vez de `Optional`:
```python
# ✅ Moderno (3.10+)
def find(name: str | None = None) -> User | None:
    ...

# 🔄 Funciona, mas verboso
def find(name: Optional[str] = None) -> Optional[User]:
    ...
```

### 3. `Any` é um escape hatch — use com moderação:
```python
# ✅ Quando o tipo é realmente desconhecido
metadata: dict[str, Any]

# ❌ Preguiça — deveria ser tipado
def process(data: Any) -> Any:  # O que é data? O que retorna?
    ...
```

### 4. Pydantic valida em runtime:
```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

User(name="Alice", age="trinta")  # ❌ ValidationError!
# Diferente de type hints puros — Pydantic REFORÇA os tipos
```

---

## Anterior: [← Fundamentos](01-fundamentos.md) | Próximo: [Estruturas de Dados →](03-estruturas-dados.md)
