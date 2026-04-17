# 05. OOP em Python

## PHP vs Python — Visão Geral

| Conceito | PHP | Python |
|----------|-----|--------|
| Definição | `class Foo { }` | `class Foo:` |
| Construtor | `__construct()` | `__init__()` |
| Referência a instância | `$this` | `self` (explícito no parâmetro!) |
| Visibilidade | `public/private/protected` | Convenção: `_private`, `__mangled` |
| Herança | `extends` | `class Child(Parent):` |
| Interface | `interface` | `ABC` + `@abstractmethod` |
| Trait | `trait` | Herança múltipla ou `Protocol` |
| Tipo final | `final class` | `@final` decorator (Python 3.8+) |

---

## Classes — O Básico

### PHP
```php
class User {
    public function __construct(
        private string $name,
        private int $age,
        private ?string $email = null,
    ) {}

    public function greet(): string {
        return "Hello, {$this->name}!";
    }
}
$user = new User("Alice", 30);
```

### Python
```python
class User:
    def __init__(self, name: str, age: int, email: str | None = None) -> None:
        self.name = name
        self.age = age
        self.email = email

    def greet(self) -> str:
        return f"Hello, {self.name}!"

user = User("Alice", 30)  # Sem "new"!
```

### Diferenças críticas:
1. **`self` é explícito** — todo método de instância recebe `self` como primeiro parâmetro
2. **Sem `new`** — `User()` em vez de `new User()`
3. **Sem visibilidade** — tudo é público. Convenção: `_private` (um underscore)
4. **`__init__` não é construtor** — é inicializador (o verdadeiro construtor é `__new__`)

---

## `self` — A Grande Diferença

```python
class Counter:
    def __init__(self) -> None:
        self.count = 0     # Atributo de instância

    def increment(self) -> None:
        self.count += 1    # Acessa via self

    def get_count(self) -> int:
        return self.count
```

**PHP:** `$this` é implícito — está sempre disponível.
**Python:** `self` é explícito — deve ser o primeiro parâmetro de todo método de instância.

```python
# ❌ Erro comum de quem vem do PHP:
class Foo:
    def bar():           # Falta self!
        return self.x    # NameError: name 'self' is not defined

# ✅ Correto:
class Foo:
    def bar(self):
        return self.x
```

---

## Properties — Getters/Setters Pythonico

### PHP
```php
class Temperature {
    private float $celsius;

    public function getCelsius(): float { return $this->celsius; }
    public function setCelsius(float $value): void {
        if ($value < -273.15) throw new InvalidArgumentException();
        $this->celsius = $value;
    }
}
```

### Python
```python
class Temperature:
    def __init__(self, celsius: float) -> None:
        self.celsius = celsius  # Usa o setter!

    @property
    def celsius(self) -> float:
        return self._celsius

    @celsius.setter
    def celsius(self, value: float) -> None:
        if value < -273.15:
            raise ValueError("Temperatura abaixo do zero absoluto")
        self._celsius = value

    @property
    def fahrenheit(self) -> float:
        """Property computada (somente leitura)."""
        return self._celsius * 9/5 + 32

t = Temperature(100)
print(t.celsius)      # 100 — chama o getter
print(t.fahrenheit)   # 212 — computado
t.celsius = -300      # ❌ ValueError
```

`@property` permite acessar métodos como se fossem atributos: `t.celsius` em vez de `t.get_celsius()`.

---

## Dunder Methods — Métodos Mágicos

### PHP
```php
public function __toString(): string { ... }
public function __get(string $name): mixed { ... }
```

### Python — Métodos com `__nome__` (double underscores = "dunder")
```python
class Vector:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def __repr__(self) -> str:
        """Representação para debug (var_dump equivalente)."""
        return f"Vector(x={self.x}, y={self.y})"

    def __str__(self) -> str:
        """Representação para print (echo equivalente)."""
        return f"({self.x}, {self.y})"

    def __eq__(self, other: object) -> bool:
        """Comparação de igualdade."""
        if not isinstance(other, Vector):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __add__(self, other: "Vector") -> "Vector":
        """Sobrecarga do operador +."""
        return Vector(self.x + other.x, self.y + other.y)

    def __len__(self) -> int:
        return 2

    def __bool__(self) -> bool:
        return self.x != 0 or self.y != 0

v1 = Vector(1, 2)
v2 = Vector(3, 4)
print(v1)          # (1, 2)
print(repr(v1))    # Vector(x=1, y=2)
print(v1 + v2)     # (4, 6)
print(v1 == v2)    # False
```

### Dunders mais comuns:

| Dunder | Uso | PHP equivalente |
|--------|-----|-----------------|
| `__init__` | Inicialização | `__construct` |
| `__str__` | `str(obj)`, `print(obj)` | `__toString` |
| `__repr__` | Debug, `repr(obj)` | `var_dump` |
| `__eq__` | `obj == other` | N/A (== compara valor) |
| `__hash__` | `hash(obj)`, usar como key em dict | `spl_object_hash` |
| `__len__` | `len(obj)` | `Countable::count` |
| `__bool__` | `bool(obj)`, `if obj:` | N/A |
| `__getattr__` | Acesso a atributo inexistente | `__get` |
| `__setattr__` | Atribuição de atributo | `__set` |
| `__contains__` | `item in obj` | N/A |
| `__iter__` | `for x in obj:` | `Iterator` |
| `__enter__`/`__exit__` | `with obj:` | N/A |

---

## Herança

### PHP
```php
class Animal {
    public function speak(): string { return "..."; }
}
class Dog extends Animal {
    public function speak(): string { return "Woof!"; }
}
```

### Python
```python
class Animal:
    def speak(self) -> str:
        return "..."

class Dog(Animal):
    def speak(self) -> str:
        return "Woof!"

# Chamar método do pai
class Cat(Animal):
    def speak(self) -> str:
        base = super().speak()  # Chama Animal.speak()
        return f"{base} Meow!"
```

### Herança Múltipla (Python permite!)
```python
class Serializable:
    def to_json(self) -> str:
        return json.dumps(self.__dict__)

class Loggable:
    def log(self) -> None:
        print(f"[LOG] {self}")

class User(Serializable, Loggable):
    def __init__(self, name: str) -> None:
        self.name = name
```

**MRO (Method Resolution Order):** Python usa C3 linearization para resolver conflitos.

---

## ABC — Classes Abstratas

### PHP
```php
abstract class Shape {
    abstract public function area(): float;
}
```

### Python
```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self) -> float:
        """Subclasses DEVEM implementar."""
        ...

class Circle(Shape):
    def __init__(self, radius: float) -> None:
        self.radius = radius

    def area(self) -> float:
        return 3.14159 * self.radius ** 2

# ❌ Não pode instanciar abstrata
Shape()   # TypeError: Can't instantiate abstract class
```

### No nosso código:
```python
# src/core/kafka_consumer.py
class BaseKafkaConsumer(ABC):
    @abstractmethod
    async def handle_message(self, data: dict) -> None:
        ...

# src/workers/task_processor.py
class TaskProcessor(BaseKafkaConsumer):
    async def handle_message(self, data: dict) -> None:
        # Implementação concreta
        event = TaskEvent(**data)
        ...
```

---

## Protocol — Duck Typing Tipado

```python
from typing import Protocol

class Sendable(Protocol):
    def send(self, data: bytes) -> None: ...

class EmailSender:
    def send(self, data: bytes) -> None:
        # Implementa send() — é um Sendable sem herdar!
        ...

def notify(sender: Sendable) -> None:
    sender.send(b"Hello")

notify(EmailSender())  # ✅ OK — EmailSender tem .send()
```

**Protocol** é como interface, mas sem herança explícita. Se o objeto tem os métodos certos, ele é válido. Isso é **duck typing** com suporte do type checker.

---

## Dataclasses — DTO/Value Object Rápido

### PHP 8.1
```php
class Point {
    public function __construct(
        public readonly float $x,
        public readonly float $y,
    ) {}
}
```

### Python
```python
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float

p = Point(1.0, 2.0)
print(p)          # Point(x=1.0, y=2.0)  — __repr__ automático!
p == Point(1.0, 2.0)  # True — __eq__ automático!
```

### Opções:
```python
@dataclass(frozen=True)      # Imutável (como readonly)
@dataclass(order=True)       # Habilita <, >, <=, >=
@dataclass(slots=True)       # Mais rápido e menos memória

@dataclass
class Config:
    host: str = "localhost"
    port: int = 8000
    tags: list[str] = field(default_factory=list)  # Mutable default!
```

### No nosso projeto, usamos **Pydantic BaseModel** em vez de dataclass:
- BaseModel valida tipos em runtime
- BaseModel serializa para JSON
- BaseModel gera schema OpenAPI
- Dataclass é mais leve, mas sem validação

---

## `@classmethod` e `@staticmethod`

```python
class User:
    _count = 0  # Atributo de classe

    def __init__(self, name: str) -> None:
        self.name = name
        User._count += 1

    @classmethod
    def get_count(cls) -> int:
        """Recebe a classe (cls), não a instância."""
        return cls._count

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Factory method — cria instância a partir de dict."""
        return cls(name=data["name"])

    @staticmethod
    def validate_name(name: str) -> bool:
        """Sem acesso a cls ou self — é apenas uma função no namespace."""
        return len(name) > 0

User.get_count()          # 0
u = User.from_dict({"name": "Alice"})
User.get_count()          # 1
User.validate_name("Bob") # True
```

---

## Anterior: [← Funções & Decorators](04-funcoes-decorators.md) | Próximo: [Módulos & Pacotes →](06-modulos-pacotes.md)
