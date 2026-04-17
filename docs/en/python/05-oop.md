# 05. OOP in Python

## Classes — The Basics

### PHP
```php
class User {
    public string $name;
    private int $age;

    public function __construct(string $name, int $age) {
        $this->name = $name;
        $this->age = $age;
    }

    public function greet(): string {
        return "Hello, I'm {$this->name}";
    }
}

$user = new User("Alice", 30);
echo $user->greet();
```

### Python
```python
class User:
    def __init__(self, name: str, age: int) -> None:
        self.name = name    # Public (no keyword needed)
        self._age = age     # "Private" by convention (single underscore)

    def greet(self) -> str:
        return f"Hello, I'm {self.name}"

user = User("Alice", 30)  # No `new` keyword!
print(user.greet())
```

### Key Differences:

| Concept | PHP | Python |
|---------|-----|--------|
| Constructor | `__construct()` | `__init__()` |
| Self reference | `$this` | `self` (explicit first parameter) |
| New instance | `new User(...)` | `User(...)` |
| Member access | `->` | `.` |
| Public | `public` keyword | Default (no keyword) |
| Private | `private` keyword | `_name` convention or `__name` mangling |
| Static method | `public static function` | `@staticmethod` |
| Class method | (no equivalent) | `@classmethod` |

---

## `self` — Always Explicit

In PHP, `$this` is implicit. In Python, `self` is the **first parameter** of every instance method:

```python
class Calculator:
    def __init__(self) -> None:
        self.result = 0

    def add(self, value: int) -> "Calculator":
        self.result += value
        return self  # Method chaining

    def reset(self) -> "Calculator":
        self.result = 0
        return self

calc = Calculator()
calc.add(5).add(3).reset()  # Method chaining works
```

**Why explicit `self`?** — Python's philosophy: "Explicit is better than implicit." You always see where instance attributes come from.

---

## Access Modifiers — Convention, Not Enforcement

```python
class MyClass:
    def __init__(self):
        self.public = "anyone"        # Public
        self._protected = "subclass"  # Protected by convention
        self.__private = "mangled"    # Name mangling → _MyClass__private

# Access:
obj = MyClass()
obj.public       # ✅ "anyone"
obj._protected   # ✅ Works! (convention only — Python trusts developers)
obj.__private    # ❌ AttributeError
obj._MyClass__private  # ✅ Works! (name mangling — not truly private)
```

**Philosophy:** Python follows "we're all consenting adults here" — `_prefix` means "don't touch this unless you know what you're doing." There's no enforcement like PHP's `private`.

---

## Properties — PHP Getters/Setters

### PHP
```php
class Temperature {
    private float $celsius;

    public function __construct(float $celsius) {
        $this->celsius = $celsius;
    }

    public function getCelsius(): float {
        return $this->celsius;
    }

    public function setCelsius(float $value): void {
        if ($value < -273.15) throw new InvalidArgumentException("Too cold");
        $this->celsius = $value;
    }

    public function getFahrenheit(): float {
        return $this->celsius * 9/5 + 32;
    }
}
```

### Python — `@property`
```python
class Temperature:
    def __init__(self, celsius: float) -> None:
        self._celsius = celsius

    @property
    def celsius(self) -> float:
        """Get temperature in Celsius."""
        return self._celsius

    @celsius.setter
    def celsius(self, value: float) -> None:
        """Set temperature with validation."""
        if value < -273.15:
            raise ValueError("Temperature below absolute zero")
        self._celsius = value

    @property
    def fahrenheit(self) -> float:
        """Computed property — Fahrenheit."""
        return self._celsius * 9/5 + 32

temp = Temperature(100)
print(temp.celsius)     # 100 (calls getter)
print(temp.fahrenheit)  # 212 (computed)
temp.celsius = 0        # Calls setter
temp.celsius = -300     # ❌ ValueError!
```

### From our codebase (`src/config/settings.py`):
```python
class Settings(BaseSettings):
    app_env: str = "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

# Usage:
settings = get_settings()
if settings.is_production:  # Looks like an attribute, but it's a method!
    ...
```

---

## Dunder (Magic) Methods

"Dunder" = **d**ouble **under**score. These are Python's equivalent of PHP's magic methods.

| Purpose | PHP | Python |
|---------|-----|--------|
| Constructor | `__construct()` | `__init__()` |
| String representation | `__toString()` | `__str__()` |
| Debug representation | (none) | `__repr__()` |
| Array/dict access | `ArrayAccess` | `__getitem__()`, `__setitem__()` |
| Length | `Countable::count()` | `__len__()` |
| Iteration | `Iterator` | `__iter__()`, `__next__()` |
| Callable | `__invoke()` | `__call__()` |
| Comparison | (operators) | `__eq__()`, `__lt__()`, etc. |
| Hash | (none) | `__hash__()` |
| Context manager | (none) | `__enter__()`, `__exit__()` |

```python
class Vector:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"Vector({self.x}, {self.y})"

    def __str__(self) -> str:
        """User-friendly string."""
        return f"({self.x}, {self.y})"

    def __add__(self, other: "Vector") -> "Vector":
        """v1 + v2"""
        return Vector(self.x + other.x, self.y + other.y)

    def __eq__(self, other: object) -> bool:
        """v1 == v2"""
        if not isinstance(other, Vector):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __len__(self) -> int:
        """len(v)"""
        return 2  # 2D vector

    def __bool__(self) -> bool:
        """bool(v) — truthy if not zero vector."""
        return self.x != 0 or self.y != 0

v1 = Vector(1, 2)
v2 = Vector(3, 4)
print(v1 + v2)      # (4, 6)
print(repr(v1))      # Vector(1, 2)
print(v1 == v2)      # False
print(len(v1))       # 2
print(bool(Vector(0, 0)))  # False
```

---

## Inheritance

### PHP
```php
class Animal {
    public function __construct(protected string $name) {}
    public function speak(): string { return "..."; }
}

class Dog extends Animal {
    public function speak(): string { return "Woof!"; }
}
```

### Python
```python
class Animal:
    def __init__(self, name: str) -> None:
        self.name = name

    def speak(self) -> str:
        return "..."

class Dog(Animal):
    def speak(self) -> str:
        return "Woof!"

    def fetch(self) -> str:
        return f"{self.name} fetches the ball"

# super() — Call parent method
class Puppy(Dog):
    def __init__(self, name: str, toy: str) -> None:
        super().__init__(name)  # PHP: parent::__construct($name)
        self.toy = toy
```

### Multiple Inheritance (Python allows it!)
```python
class Flyable:
    def fly(self) -> str:
        return "Flying!"

class Swimmable:
    def swim(self) -> str:
        return "Swimming!"

class Duck(Flyable, Swimmable):
    pass

duck = Duck()
duck.fly()   # "Flying!"
duck.swim()  # "Swimming!"
```

PHP uses traits for this: `use Flyable, Swimmable;`. Python uses multiple inheritance directly.

**Method Resolution Order (MRO):**
```python
Duck.__mro__
# (Duck, Flyable, Swimmable, object)
# Python uses C3 linearization to resolve method lookup order
```

---

## Abstract Base Classes (ABC)

### PHP
```php
abstract class Shape {
    abstract public function area(): float;
    public function describe(): string { return "I'm a shape"; }
}
```

### Python
```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self) -> float:
        """Must be implemented by subclasses."""
        ...

    def describe(self) -> str:
        """Concrete method — can be inherited as-is."""
        return "I'm a shape"

# Cannot instantiate directly:
# shape = Shape()  # ❌ TypeError: Can't instantiate abstract class

class Circle(Shape):
    def __init__(self, radius: float) -> None:
        self.radius = radius

    def area(self) -> float:
        return 3.14159 * self.radius ** 2

circle = Circle(5)
circle.area()      # 78.54
circle.describe()  # "I'm a shape"
```

### From our codebase (`src/core/kafka_consumer.py`):
```python
class BaseKafkaConsumer(ABC):
    """Base class for workers that consume from a Kafka topic."""

    def __init__(self, topic: str, settings: Settings | None = None) -> None:
        self.topic = topic
        self.settings = settings or get_settings()
        self._consumer: AIOKafkaConsumer | None = None
        self._running = False

    async def run(self) -> None:
        """Main loop — concrete method."""
        await self.start()
        try:
            async for msg in self._consumer:
                await self.process_message(msg.value)
        finally:
            await self.stop()

    @abstractmethod
    async def process_message(self, payload: dict[str, Any]) -> None:
        """Must be implemented by subclasses."""
        ...

    async def handle_error(self, payload: dict[str, Any]) -> None:
        """Optional override — hook for error handling."""
        logger.warning("[%s] Message sent to error handling", self.__class__.__name__)
```

And the implementation (`src/workers/task_processor.py`):
```python
class TaskProcessorWorker(BaseKafkaConsumer):
    """Concrete implementation — processes AI tasks."""

    async def process_message(self, payload: dict[str, Any]) -> None:
        # Implements the abstract method
        task_id = payload.get("task_id", "unknown")
        ...
```

---

## Class Methods & Static Methods

```python
class User:
    _count = 0  # Class variable (shared across all instances)

    def __init__(self, name: str) -> None:
        self.name = name     # Instance variable
        User._count += 1

    def greet(self) -> str:
        """Instance method — has access to self."""
        return f"Hello, I'm {self.name}"

    @classmethod
    def get_count(cls) -> int:
        """Class method — has access to cls (the class), not self."""
        return cls._count

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Factory method — alternative constructor."""
        return cls(name=data["name"])

    @staticmethod
    def validate_name(name: str) -> bool:
        """Static method — no access to self or cls."""
        return len(name) >= 2

# Usage:
user = User("Alice")
User.get_count()          # 1
user2 = User.from_dict({"name": "Bob"})
User.get_count()          # 2
User.validate_name("A")   # False
```

**PHP comparison:**
- `@classmethod` → `public static function` that can access `static::` (late static binding)
- `@staticmethod` → `public static function` that's a plain utility function
- `@classmethod` + factory → PHP named constructors: `User::fromArray($data)`

---

## Dataclasses — Less Boilerplate

```python
from dataclasses import dataclass, field

@dataclass
class Point:
    x: float
    y: float
    z: float = 0.0

# Auto-generates: __init__, __repr__, __eq__
p = Point(1.0, 2.0)
print(p)           # Point(x=1.0, y=2.0, z=0.0)
p == Point(1.0, 2.0)  # True

@dataclass(frozen=True)  # Immutable
class Color:
    r: int
    g: int
    b: int

@dataclass
class Config:
    name: str
    tags: list[str] = field(default_factory=list)  # Mutable default
```

**Note:** In our project, we use **Pydantic BaseModel** instead of dataclasses because Pydantic adds validation. Dataclasses are for simple data holders without validation.

---

## Protocols — Structural Typing (Duck Typing Formalized)

```python
from typing import Protocol

class Serializable(Protocol):
    def to_json(self) -> str:
        ...

class User:
    def to_json(self) -> str:
        return '{"name": "Alice"}'

class Config:
    def to_json(self) -> str:
        return '{"debug": true}'

def save(obj: Serializable) -> None:
    """Accepts any object with a to_json() method."""
    print(obj.to_json())

save(User())   # ✅ User has to_json()
save(Config()) # ✅ Config has to_json()
# No explicit inheritance needed! (unlike PHP interfaces)
```

**PHP comparison:** PHP interfaces require `implements`. Python Protocols are **structural** — if it has the right methods, it satisfies the protocol. "If it walks like a duck and quacks like a duck..."

---

## `__slots__` — Memory Optimization

```python
class Point:
    __slots__ = ("x", "y")  # Only these attributes allowed

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

p = Point(1, 2)
p.z = 3  # ❌ AttributeError! (not in __slots__)
```

Benefits:
- ~30% less memory per instance
- Faster attribute access
- Prevents accidental attribute creation

---

## Previous: [← Functions & Decorators](04-functions-decorators.md) | Next: [Modules & Packages →](06-modules-packages.md)
