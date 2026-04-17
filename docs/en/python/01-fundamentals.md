# 01. Python Fundamentals for PHP Developers

## The Philosophy Shift

In PHP, you're used to a **permissive** language — loose types, implicit conversions, `$` for variables, semicolons everywhere. Python is **opinionated**: indentation matters, explicit is better than implicit, and readability is king.

Python's guiding principles are captured in `import this` (The Zen of Python):
```
Beautiful is better than ugly.
Explicit is better than implicit.
Simple is better than complex.
Readability counts.
```

---

## Variables & Assignment

### PHP
```php
$name = "Conn2Flow";
$version = 1;
$price = 9.99;
$isActive = true;
$items = null;
```

### Python
```python
name = "Conn2Flow"
version = 1
price = 9.99
is_active = True
items = None
```

### Key Differences:

| Concept | PHP | Python |
|---------|-----|--------|
| Variable prefix | `$name` | `name` (no prefix) |
| Statement terminator | `;` required | None (newline) |
| Boolean | `true` / `false` | `True` / `False` (capital) |
| Null | `null` | `None` (capital) |
| Naming convention | `$camelCase` or `$snake_case` | `snake_case` (PEP 8) |
| Constants | `const NAME = "x"` or `define()` | `NAME = "x"` (convention, ALL_CAPS) |

**Important:** Python has **no constants**. `NAME = "x"` is just a convention — nothing prevents reassignment. In practice, ALL_CAPS variables are treated as constants by convention.

### Multiple Assignment
```python
# Parallel assignment
x, y, z = 1, 2, 3

# Same value
a = b = c = 0

# Swap (no temp variable needed!)
x, y = y, x  # Mind = blown for PHP devs
```

In PHP, swapping requires a temp:
```php
$temp = $x;
$x = $y;
$y = $temp;
```

---

## Strings

### PHP
```php
$name = "World";
echo "Hello, $name!";           // Interpolation
echo "Hello, {$name}!";         // Explicit interpolation
echo 'Hello, ' . $name . '!';  // Concatenation
echo "Line 1\nLine 2";
```

### Python — f-strings (Python 3.6+)
```python
name = "World"
print(f"Hello, {name}!")          # f-string (recommended)
print("Hello, " + name + "!")    # Concatenation (avoid)
print("Hello, {}!".format(name)) # .format() (older style)
print("Line 1\nLine 2")
```

### f-strings are powerful — expressions inside `{}`
```python
price = 49.99
quantity = 3
print(f"Total: ${price * quantity:.2f}")  # Total: $149.97

items = ["a", "b", "c"]
print(f"Count: {len(items)}")  # Count: 3

# Conditional inside f-string
status = "active"
print(f"Status: {'✓' if status == 'active' else '✗'}")
```

### From our codebase (`src/main.py`):
```python
logger.info("Starting Conn2Flow Nexus AI v%s (%s)", settings.app_version, settings.app_env)
```
Note: logging uses `%s` style (not f-strings) for performance — the string is only formatted if the log level is enabled.

### Multiline Strings (Triple Quotes)
```python
# PHP heredoc equivalent
query = """
    SELECT *
    FROM users
    WHERE active = 1
    ORDER BY name
"""

# Docstrings (documentation)
def my_function():
    """This is the function's documentation.

    It can span multiple lines.
    Accessible via my_function.__doc__
    """
    pass
```

### String Methods (no separate functions like PHP)
```python
# PHP: strtoupper($s), strtolower($s), trim($s)
s = "  Hello World  "
s.upper()      # "  HELLO WORLD  "
s.lower()      # "  hello world  "
s.strip()      # "Hello World"
s.lstrip()     # "Hello World  "
s.rstrip()     # "  Hello World"

# PHP: str_replace("World", "Python", $s)
s.replace("World", "Python")  # "  Hello Python  "

# PHP: strpos($s, "World")
s.find("World")   # 8 (returns -1 if not found)
s.index("World")  # 8 (raises ValueError if not found)

# PHP: explode(",", $s)
"a,b,c".split(",")  # ["a", "b", "c"]

# PHP: implode(",", $arr)
",".join(["a", "b", "c"])  # "a,b,c"

# PHP: substr($s, 2, 5)
s[2:7]  # "Hello" (slicing — more on this in data structures)

# PHP: str_starts_with($s, "  He"), str_ends_with($s, "  ")
s.startswith("  He")  # True
s.endswith("  ")      # True
```

---

## Numbers

```python
# Integers (unlimited precision — no overflow!)
big = 999_999_999_999_999  # Underscores for readability (Python 3.6+)

# Floats
pi = 3.14159

# Division
10 / 3    # 3.3333... (always float)
10 // 3   # 3 (integer/floor division — like PHP intdiv())
10 % 3    # 1 (modulo — same as PHP)

# Power
2 ** 10   # 1024 (PHP: pow(2, 10) or 2 ** 10 in PHP 5.6+)

# Type conversion
int("42")     # 42
float("3.14") # 3.14
str(42)       # "42"
```

### PHP vs Python Division Gotcha
```php
// PHP
10 / 3;     // 3.3333... (float)
intdiv(10, 3); // 3
```
```python
# Python
10 / 3     # 3.3333... (always float, even 10 / 2 = 5.0)
10 // 3    # 3 (floor division)
```

**Watch out:** In Python, `/` ALWAYS returns float. Use `//` for integer division.

---

## Booleans & Truthiness

### PHP Falsy Values
```php
// These are ALL falsy in PHP:
false, 0, 0.0, "", "0", null, [], // empty array
```

### Python Falsy Values
```python
# These are ALL falsy in Python:
False, 0, 0.0, "", None, [], {}, set(), (), 0j
# Note: "0" is TRUTHY in Python! (non-empty string)
```

**Critical difference:** In PHP, `"0"` is falsy. In Python, `"0"` is **truthy** because it's a non-empty string. This WILL bite you.

### Boolean Operations
```python
# PHP: && || !
# Python: and, or, not (English words, not symbols)

x = True
y = False

x and y   # False
x or y    # True
not x     # False

# Short-circuit evaluation (same as PHP)
name = user_name or "Anonymous"  # If user_name is falsy, use "Anonymous"
```

### From our codebase (`src/config/settings.py`):
```python
has_any = any([
    self.openai_api_key,
    self.anthropic_api_key,
    self.gemini_api_key,
    self.groq_api_key,
])
if not has_any and self.is_production:
    raise ValueError("At least one LLM API key must be set in production")
```

`any()` returns `True` if **any** element is truthy. `all()` returns `True` if **all** elements are truthy.

---

## Comparison Operators

```python
# Same as PHP
x == y   # Equal (value)
x != y   # Not equal
x > y    # Greater than
x < y    # Less than
x >= y   # Greater or equal
x <= y   # Less or equal

# Python-specific: identity comparison
x is y       # Same object (PHP: === but for identity, not type+value)
x is not y   # Not same object

# Chained comparisons (Python exclusive!)
1 < x < 10       # True if x is between 1 and 10
0 <= score <= 100 # Beautiful, right?
```

### `==` vs `is`
```python
a = [1, 2, 3]
b = [1, 2, 3]
c = a

a == b  # True (same value)
a is b  # False (different objects in memory)
a is c  # True (same object)

# ALWAYS use `is` for None checks:
if x is None:    # ✅ Correct
if x == None:    # ❌ Works but bad practice (can be overridden by __eq__)
```

---

## Control Flow

### if / elif / else
```python
# PHP
# if ($score >= 90) { $grade = "A"; }
# elseif ($score >= 80) { $grade = "B"; }
# else { $grade = "C"; }

# Python — no braces, no parentheses required, colon + indentation
score = 85
if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
else:
    grade = "C"
```

Note: `elif` not `elseif` or `else if`.

### Ternary Operator
```php
// PHP
$status = $active ? "on" : "off";
```
```python
# Python (reads like English)
status = "on" if active else "off"
```

### Match Statement (Python 3.10+ — like PHP 8.0 match)
```python
# PHP 8.0+
# match($status) {
#     'active' => 'Running',
#     'paused' => 'On hold',
#     default => 'Unknown',
# };

# Python 3.10+
match status:
    case "active":
        result = "Running"
    case "paused":
        result = "On hold"
    case _:  # default
        result = "Unknown"

# Pattern matching is MORE powerful than PHP match:
match point:
    case (0, 0):
        print("Origin")
    case (x, 0):
        print(f"On X axis at {x}")
    case (0, y):
        print(f"On Y axis at {y}")
    case (x, y):
        print(f"At ({x}, {y})")
```

---

## Loops

### for Loop
```python
# PHP: foreach ($items as $item) { ... }
# Python:
for item in items:
    print(item)

# PHP: foreach ($items as $key => $value) { ... }
# Python (with enumerate):
for index, item in enumerate(items):
    print(f"{index}: {item}")

# PHP: for ($i = 0; $i < 10; $i++) { ... }
# Python:
for i in range(10):       # 0 to 9
    print(i)

for i in range(1, 11):    # 1 to 10
    print(i)

for i in range(0, 20, 2): # 0, 2, 4, ..., 18 (step 2)
    print(i)
```

### while Loop
```python
# Same concept as PHP, just different syntax
count = 0
while count < 10:
    print(count)
    count += 1
# Note: Python has NO $count++ or count++. Use count += 1
```

### Loop Control
```python
for i in range(10):
    if i == 3:
        continue  # Skip this iteration
    if i == 7:
        break     # Exit loop
    print(i)
# Output: 0, 1, 2, 4, 5, 6

# Python-exclusive: for/else
for item in items:
    if item == target:
        print("Found!")
        break
else:
    # This runs if the loop completed WITHOUT break
    print("Not found!")
```

The `for/else` pattern replaces the common PHP pattern:
```php
$found = false;
foreach ($items as $item) {
    if ($item === $target) {
        $found = true;
        break;
    }
}
if (!$found) {
    echo "Not found!";
}
```

---

## From Our Codebase — Real Examples

### Iteration with message validation (`src/graphs/base_graph.py`):
```python
has_user = any(m.get("role") == "user" for m in messages)
```
This is a **generator expression** inside `any()`. It iterates over `messages` and checks if any message has `role == "user"`. In PHP:
```php
$hasUser = false;
foreach ($messages as $m) {
    if ($m['role'] === 'user') {
        $hasUser = true;
        break;
    }
}
```

### Dictionary key access with default (`src/workers/task_processor.py`):
```python
model = payload.get("model", self.settings.default_model)
```
In PHP: `$model = $payload['model'] ?? $this->settings->default_model;`

### Logging with old-style formatting (`src/core/kafka_producer.py`):
```python
logger.debug(
    "Event sent — topic=%s partition=%d offset=%d key=%s",
    metadata.topic,
    metadata.partition,
    metadata.offset,
    key,
)
```
Logging uses `%s`/`%d` (lazy formatting) instead of f-strings for performance.

---

## Print & Debugging

```python
# Basic print
print("Hello")
print("a", "b", "c")          # a b c (space-separated by default)
print("a", "b", sep=", ")     # a, b
print("no newline", end="")   # No trailing newline

# Debug print (Python 3.8+)
x = 42
print(f"{x=}")  # x=42 (prints variable name and value!)

# Type checking
type(42)           # <class 'int'>
isinstance(42, int)  # True
isinstance("hi", (str, bytes))  # True (check multiple types)
```

---

## Indentation Matters

This is the **biggest** adjustment for PHP developers. Python uses indentation (4 spaces by convention) instead of braces:

```python
# ✅ Correct
if True:
    print("yes")
    if True:
        print("nested")

# ❌ IndentationError
if True:
print("yes")  # Not indented!

# ❌ IndentationError (mixed indentation)
if True:
    print("yes")
      print("oops")  # Wrong indentation level
```

**Rule:** Use 4 spaces per level. Never mix tabs and spaces. Configure your editor to insert spaces when you press Tab.

---

## None — The Python null

```python
x = None

# Check for None (always use `is`)
if x is None:
    print("x is None")

# None is a singleton — there's only one None object
a = None
b = None
a is b  # True (same object)

# Common pattern: default mutable arguments
def add_item(item, items=None):  # ✅ Correct
    if items is None:
        items = []
    items.append(item)
    return items

# ❌ DANGER — never use mutable default arguments:
def add_item_bad(item, items=[]):  # Bug! Same list shared across calls
    items.append(item)
    return items
```

**Critical Python Gotcha:** Default mutable arguments (like `[]` or `{}`) are created once and shared across all calls. Always use `None` as default and create the mutable inside the function. This is why you see `default_factory` in Pydantic:

```python
# From src/api/schemas/requests.py
metadata: dict[str, Any] = Field(default_factory=dict)
#                                 ^^^^^^^^^^^^^^^ Creates a new dict for each instance
```

---

## `pass` — The Do-Nothing Statement

```python
# Placeholder for empty blocks (Python requires a body)
class MyError(Exception):
    pass  # Empty class body

def not_implemented_yet():
    pass  # Will implement later

if condition:
    pass  # Do nothing
else:
    do_something()

# Also common: ellipsis (...) as placeholder
def abstract_method():
    ...  # Same as pass, but more semantically "not implemented"
```

From our codebase (`src/core/kafka_consumer.py`):
```python
@abstractmethod
async def process_message(self, payload: dict[str, Any]) -> None:
    """Processes an individual message. Must be implemented by subclasses."""
    ...  # Ellipsis as placeholder for abstract method
```

---

## Next: [Type Hints & The Type System →](02-type-hints.md)
