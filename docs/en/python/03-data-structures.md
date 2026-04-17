# 03. Data Structures Deep Dive

## The Big Shift: PHP Arrays vs Python Collections

In PHP, `array` is a Swiss Army knife — it's a list, a dictionary, a queue, a stack, and everything in between. Python separates these into **distinct types**, each optimized for its use case.

| PHP | Python | Ordered? | Mutable? | Duplicates? | Use Case |
|-----|--------|----------|----------|-------------|----------|
| `array` (indexed) | `list` | ✅ | ✅ | ✅ | General-purpose sequence |
| `array` (assoc) | `dict` | ✅ (3.7+) | ✅ | Keys: ❌ | Key-value mapping |
| (no equiv) | `tuple` | ✅ | ❌ | ✅ | Immutable sequence |
| (no equiv) | `set` | ❌ | ✅ | ❌ | Unique values, membership testing |
| (no equiv) | `frozenset` | ❌ | ❌ | ❌ | Immutable set (hashable) |

---

## Lists — PHP Indexed Arrays

### Creation
```python
# PHP: $items = [1, 2, 3];
items = [1, 2, 3]

# Mixed types (valid but discouraged)
mixed = [1, "hello", True, 3.14, None]

# Empty list
empty = []
# or
empty = list()
```

### Accessing Elements
```python
items = ["a", "b", "c", "d", "e"]

items[0]    # "a" (first)
items[-1]   # "e" (last — PHP doesn't have negative indexing!)
items[-2]   # "d" (second to last)
```

**Python Exclusive: Negative Indexing**
```python
# PHP: $items[count($items) - 1]  // Last element
# Python:
items[-1]   # Much cleaner!
```

### Slicing — Extracting Sub-lists
```python
items = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

items[2:5]    # [2, 3, 4]    — from index 2 to 4 (5 excluded)
items[:3]     # [0, 1, 2]    — first 3 elements
items[7:]     # [7, 8, 9]    — from index 7 to end
items[-3:]    # [7, 8, 9]    — last 3 elements
items[::2]    # [0, 2, 4, 6, 8] — every 2nd element
items[::-1]   # [9, 8, 7, ..., 0] — reversed!

# Slicing creates a COPY (important for mutability)
copy = items[:]  # Shallow copy of entire list
```

PHP equivalent would require `array_slice()`:
```php
$items = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
array_slice($items, 2, 3);  // [2, 3, 4]
array_reverse($items);       // reversed
```

### Modifying Lists
```python
items = [1, 2, 3]

# Add elements
items.append(4)           # [1, 2, 3, 4]  — PHP: $items[] = 4;
items.insert(0, 0)        # [0, 1, 2, 3, 4] — insert at index
items.extend([5, 6])      # [0, 1, 2, 3, 4, 5, 6] — PHP: array_merge()

# Remove elements
items.pop()               # 6 — removes and returns last
items.pop(0)              # 0 — removes and returns at index
items.remove(3)           # removes first occurrence of value 3
del items[1]              # removes at index 1

# PHP: unset($items[1]);  vs  Python: del items[1]
# But! Python re-indexes the list. PHP leaves a gap.
```

### List Operations
```python
items = [3, 1, 4, 1, 5, 9, 2, 6]

len(items)           # 8 — PHP: count($items)
items.sort()         # In-place sort — [1, 1, 2, 3, 4, 5, 6, 9]
sorted(items)        # Returns new sorted list (original unchanged)
items.reverse()      # In-place reverse
reversed(items)      # Returns iterator (lazy)

min(items)           # 1 — PHP: min($items)
max(items)           # 9 — PHP: max($items)
sum(items)           # 31 — PHP: array_sum($items)

3 in items           # True — PHP: in_array(3, $items)
3 not in items       # False

items.count(1)       # 2 — count occurrences of value 1
items.index(5)       # 4 — index of first occurrence (raises ValueError if not found)
```

### List Comprehensions — The Python Superpower

This is one of Python's most powerful features — no PHP equivalent:

```python
# PHP:
# $squares = [];
# for ($i = 0; $i < 10; $i++) {
#     $squares[] = $i ** 2;
# }

# Python — one line:
squares = [i ** 2 for i in range(10)]
# [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

# With condition (filter)
evens = [i for i in range(20) if i % 2 == 0]
# [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]

# Transform + filter
names = ["Alice", "Bob", "Charlie", "Dave"]
long_upper = [name.upper() for name in names if len(name) > 3]
# ["ALICE", "CHARLIE", "DAVE"]

# Nested comprehension
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
flat = [num for row in matrix for num in row]
# [1, 2, 3, 4, 5, 6, 7, 8, 9]
```

### From our codebase — Generator Expression:
```python
# src/graphs/base_graph.py
has_user = any(m.get("role") == "user" for m in messages)
```
Note: `(expr for x in iterable)` with parentheses is a **generator expression** — it doesn't create a list in memory. When passed directly to a function like `any()`, you can omit the outer parentheses.

---

## Dictionaries — PHP Associative Arrays

### Creation
```python
# PHP: $config = ["host" => "localhost", "port" => 8000];
config = {"host": "localhost", "port": 8000}

# Also valid:
config = dict(host="localhost", port=8000)

# Empty dict
empty = {}
```

### Accessing Values
```python
config = {"host": "localhost", "port": 8000, "debug": True}

# Direct access (raises KeyError if missing)
config["host"]      # "localhost"
config["missing"]   # ❌ KeyError!

# Safe access with .get() (returns None or default)
config.get("host")           # "localhost"
config.get("missing")        # None
config.get("missing", "N/A") # "N/A"
```

In PHP: `$config['missing'] ?? 'N/A'` is equivalent to `config.get("missing", "N/A")`.

### From our codebase (`src/workers/task_processor.py`):
```python
task_id = payload.get("task_id", "unknown")
model = payload.get("model", self.settings.default_model)
messages = payload.get("messages", [])
temperature = payload.get("temperature", 0.7)
max_tokens = payload.get("max_tokens")  # None if missing
```

### Modifying Dicts
```python
config = {"host": "localhost", "port": 8000}

# Add or update
config["debug"] = True        # Add new key
config["port"] = 9000         # Update existing

# Merge dicts (Python 3.9+)
defaults = {"host": "0.0.0.0", "port": 8000, "debug": False}
overrides = {"port": 9000, "debug": True}
merged = defaults | overrides  # {"host": "0.0.0.0", "port": 9000, "debug": True}

# In-place merge
defaults |= overrides  # Same as defaults.update(overrides)

# Remove
del config["debug"]           # Removes key (KeyError if missing)
config.pop("debug", None)     # Removes and returns (None if missing — safe)

# PHP: unset($config['debug']);
```

### Dict Spread/Unpack (like PHP `...` spread)
```python
# Merging dicts with ** operator
base = {"host": "localhost", "port": 8000}
extra = {"debug": True, "version": "1.0"}
combined = {**base, **extra}
# {"host": "localhost", "port": 8000, "debug": True, "version": "1.0"}

# From our codebase — very common pattern:
value = orjson.dumps({"status": status, **(data or {})})
# Unpacks data dict into the new dict, with "status" key added
```

### Iterating Dicts
```python
config = {"host": "localhost", "port": 8000, "debug": True}

# Keys only
for key in config:          # or config.keys()
    print(key)

# Values only
for value in config.values():
    print(value)

# Both (most common)
for key, value in config.items():
    print(f"{key}: {value}")

# PHP equivalent:
# foreach ($config as $key => $value) { ... }
```

### Dict Comprehension
```python
# PHP: No equivalent
# Create dict from iteration
squares = {i: i**2 for i in range(5)}
# {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}

# Filter dict
config = {"host": "localhost", "port": 8000, "debug": True, "secret": "abc"}
public = {k: v for k, v in config.items() if k != "secret"}

# Transform keys/values
upper_keys = {k.upper(): v for k, v in config.items()}
```

### From our codebase — dict patterns:

```python
# src/core/llm_router.py — Building result dict
result = {
    "content": choice.message.content or "",
    "model_used": response.model or model,
    "usage": {
        "prompt_tokens": getattr(usage, "prompt_tokens", 0),
        "completion_tokens": getattr(usage, "completion_tokens", 0),
        "total_tokens": getattr(usage, "total_tokens", 0),
    },
    "finish_reason": choice.finish_reason or "stop",
}
```

```python
# src/core/llm_router.py — Iterating key-value map
key_map = {
    "OPENAI_API_KEY": settings.openai_api_key,
    "ANTHROPIC_API_KEY": settings.anthropic_api_key,
}
for env_var, value in key_map.items():
    if value:
        os.environ[env_var] = value
```

---

## Tuples — Immutable Lists

```python
# Creation
point = (1, 2)
rgb = (255, 128, 0)
single = (42,)  # Note the comma! Without it, (42) is just 42

# Accessing (same as list)
point[0]   # 1
point[-1]  # 2

# Immutable — cannot modify
point[0] = 5  # ❌ TypeError!

# Unpacking (destructuring)
x, y = point  # x=1, y=2
r, g, b = rgb  # r=255, g=128, b=0

# Common use: return multiple values
def get_dimensions():
    return (1920, 1080)  # Parentheses optional

width, height = get_dimensions()
```

### When to use tuple vs list?
- **Tuple:** Fixed-size, immutable data (coordinates, RGB, config pairs)
- **List:** Variable-size, mutable data (items to process, results to accumulate)
- Tuples are **hashable** (can be dict keys or set members) — lists are not

---

## Sets — Unique Values

```python
# Creation
tags = {"python", "fastapi", "kafka"}
# or from list (removes duplicates)
unique = set([1, 2, 2, 3, 3, 3])  # {1, 2, 3}

# Membership testing (O(1) — very fast!)
"python" in tags  # True
"php" in tags     # False
# vs list: "python" in ["python", "fastapi", "kafka"]  # O(n) — slow for large lists

# Operations
a = {1, 2, 3, 4}
b = {3, 4, 5, 6}

a | b       # {1, 2, 3, 4, 5, 6} — union
a & b       # {3, 4} — intersection
a - b       # {1, 2} — difference
a ^ b       # {1, 2, 5, 6} — symmetric difference

# Modifying
tags.add("redis")
tags.remove("kafka")      # KeyError if missing
tags.discard("missing")   # No error if missing
```

---

## Unpacking & Star Expressions

```python
# Basic unpacking
a, b, c = [1, 2, 3]

# Star expression — collect remaining
first, *rest = [1, 2, 3, 4, 5]
# first=1, rest=[2, 3, 4, 5]

*init, last = [1, 2, 3, 4, 5]
# init=[1, 2, 3, 4], last=5

first, *middle, last = [1, 2, 3, 4, 5]
# first=1, middle=[2, 3, 4], last=5

# Ignore values with _
_, second, _ = (1, 2, 3)  # Only care about second
```

---

## `enumerate()`, `zip()`, `map()`, `filter()`

```python
# enumerate — index + value
items = ["a", "b", "c"]
for i, item in enumerate(items):
    print(f"{i}: {item}")
# 0: a
# 1: b
# 2: c

# Start from 1
for i, item in enumerate(items, start=1):
    print(f"{i}: {item}")

# zip — pair up iterables
names = ["Alice", "Bob", "Charlie"]
scores = [95, 87, 92]
for name, score in zip(names, scores):
    print(f"{name}: {score}")

# Create dict from two lists
mapping = dict(zip(names, scores))
# {"Alice": 95, "Bob": 87, "Charlie": 92}

# map — apply function to all elements
numbers = [1, 2, 3, 4]
doubled = list(map(lambda x: x * 2, numbers))  # [2, 4, 6, 8]
# But prefer list comprehension: [x * 2 for x in numbers]

# filter — keep elements matching condition
evens = list(filter(lambda x: x % 2 == 0, numbers))  # [2, 4]
# Prefer: [x for x in numbers if x % 2 == 0]
```

---

## `collections` Module — Specialized Containers

```python
from collections import defaultdict, Counter, OrderedDict, deque

# defaultdict — auto-initializes missing keys
word_count = defaultdict(int)  # Default value: 0
for word in ["hello", "world", "hello"]:
    word_count[word] += 1
# {"hello": 2, "world": 1}

# Counter — count elements
counter = Counter(["a", "b", "a", "c", "a", "b"])
counter.most_common(2)  # [("a", 3), ("b", 2)]

# deque — double-ended queue (efficient append/pop from both ends)
queue = deque([1, 2, 3])
queue.append(4)       # [1, 2, 3, 4]
queue.appendleft(0)   # [0, 1, 2, 3, 4]
queue.popleft()       # 0 — O(1) vs list.pop(0) which is O(n)
```

---

## Codebase Patterns Summary

| Pattern | PHP | Python (from our code) |
|---------|-----|------------------------|
| Default value | `$x ?? 'default'` | `x.get("key", "default")` |
| Array/dict spread | `array_merge($a, $b)` | `{**a, **b}` |
| Check membership | `in_array($v, $arr)` | `v in items` |
| List of dicts | `$arr = [['k' => 'v']]` | `arr = [{"k": "v"}]` |
| Any truthy | `array_filter($arr)` | `any(arr)` |
| Key exists | `isset($arr['k'])` or `array_key_exists` | `"k" in d` |

---

## Previous: [← Type Hints](02-type-hints.md) | Next: [Functions & Decorators →](04-functions-decorators.md)
