# 03. Estruturas de Dados em Profundidade

## PHP Arrays vs Python — A Grande Diferença

PHP tem **uma estrutura para tudo**: `array`. Python tem **quatro** estruturas distintas:

| PHP | Python | Mutável | Ordenado | Duplicatas |
|-----|--------|---------|----------|------------|
| `array` (indexado) | `list` | ✅ | ✅ | ✅ |
| `array` (associativo) | `dict` | ✅ | ✅ (3.7+) | Chaves únicas |
| N/A | `tuple` | ❌ | ✅ | ✅ |
| N/A | `set` | ✅ | ❌ | ❌ |

---

## List — Array Indexado

```python
# Criação
names = ["Alice", "Bob", "Charlie"]
empty = []
typed: list[str] = []

# Acesso
names[0]     # "Alice"
names[-1]    # "Charlie" (último!)
names[-2]    # "Bob" (penúltimo)

# Fatiamento (slicing)
names[0:2]   # ["Alice", "Bob"] — do índice 0 até 2 (exclusivo)
names[1:]    # ["Bob", "Charlie"] — do índice 1 até o final
names[:2]    # ["Alice", "Bob"] — do início até 2
names[::2]   # ["Alice", "Charlie"] — pula de 2 em 2
names[::-1]  # ["Charlie", "Bob", "Alice"] — invertido!
```

### Métodos comuns:
```python
items = [3, 1, 4, 1, 5]

items.append(9)          # [3, 1, 4, 1, 5, 9] — adiciona ao final
items.insert(0, 0)       # [0, 3, 1, 4, 1, 5, 9] — insere na posição
items.extend([2, 6])     # [..., 2, 6] — concatena lista
items.remove(1)          # Remove primeira ocorrência de 1
items.pop()              # Remove e retorna o último
items.pop(0)             # Remove e retorna o item no índice 0
items.sort()             # Ordena in-place
items.reverse()          # Inverte in-place
items.index(4)           # Índice da primeira ocorrência de 4
items.count(1)           # Conta ocorrências de 1
len(items)               # Tamanho

# Sem modificar o original:
sorted_items = sorted(items)           # Nova lista ordenada
reversed_items = list(reversed(items)) # Nova lista invertida
```

### PHP comparado:
```php
$items = [3, 1, 4, 1, 5];
array_push($items, 9);        // Python: items.append(9)
array_pop($items);             // Python: items.pop()
sort($items);                  // Python: items.sort()
array_reverse($items);         // Python: items[::-1] ou list(reversed(items))
count($items);                 // Python: len(items)
in_array(4, $items);           // Python: 4 in items
array_search(4, $items);       // Python: items.index(4)
```

---

## Dict — Array Associativo

```python
# Criação
user = {"name": "Alice", "age": 30, "email": "alice@example.com"}
empty = {}
typed: dict[str, int] = {}

# Acesso
user["name"]              # "Alice"
user["missing"]           # ❌ KeyError!
user.get("missing")       # None (seguro)
user.get("missing", "N/A")  # "N/A" (com default)

# Modificação
user["name"] = "Bob"      # Atualiza
user["phone"] = "123"     # Adiciona nova chave
del user["email"]         # Remove

# Verificação
"name" in user            # True
"address" in user         # False
```

### Métodos comuns:
```python
d = {"a": 1, "b": 2, "c": 3}

d.keys()       # dict_keys(["a", "b", "c"])
d.values()     # dict_values([1, 2, 3])
d.items()      # dict_items([("a", 1), ("b", 2), ("c", 3)])
d.update({"d": 4, "a": 10})  # Merge/atualiza
d.pop("b")     # Remove e retorna valor de "b"
d.setdefault("e", 5)  # Retorna valor se existe, senão insere e retorna
```

### Iteração:
```python
# PHP: foreach ($user as $key => $value) { ... }
for key, value in user.items():
    print(f"{key}: {value}")

# Só chaves
for key in user:
    print(key)

# Só valores
for value in user.values():
    print(value)
```

### Merge de dicts:
```python
# Python 3.9+ — operador |
merged = dict_a | dict_b      # Novo dict (b sobrescreve a)
dict_a |= dict_b              # In-place merge

# Unpacking (3.5+)
merged = {**dict_a, **dict_b}

# PHP: array_merge($a, $b)
```

### No nosso código:
```python
# src/api/schemas/requests.py
messages: list[dict[str, str]] = Field(...)
# Lista de dicts: [{"role": "user", "content": "Hello"}]

# src/models/events.py
metadata: dict[str, Any] = Field(default_factory=dict)
```

---

## Tuple — Sequência Imutável

```python
# Criação
point = (1.0, 2.0)
single = (42,)           # Vírgula necessária para tupla de 1 elemento!
empty = ()

# Acesso (igual a list)
point[0]      # 1.0
point[-1]     # 2.0

# ❌ Imutável!
point[0] = 3.0  # TypeError: 'tuple' object does not support item assignment

# Unpacking
x, y = point   # x=1.0, y=2.0
```

### Quando usar tuple:
- Dados que **não devem mudar** (coordenadas, configs)
- **Retorno múltiplo** de funções: `return status, data`
- **Chaves de dict** (lists não podem ser chaves — são mutáveis)
- **Performance** — tuples são mais rápidas que lists

---

## Set — Conjunto Sem Duplicatas

```python
# Criação
tags = {"python", "fastapi", "async"}
empty = set()   # NÃO {} — isso cria dict vazio!

# Operações
tags.add("kafka")         # Adicionar
tags.discard("java")      # Remover (sem erro se não existe)
tags.remove("python")     # Remover (KeyError se não existe)
"fastapi" in tags         # True — O(1), muito rápido!

# Operações de conjunto
a = {1, 2, 3, 4}
b = {3, 4, 5, 6}

a | b    # União: {1, 2, 3, 4, 5, 6}
a & b    # Interseção: {3, 4}
a - b    # Diferença: {1, 2}
a ^ b    # Diferença simétrica: {1, 2, 5, 6}

# Eliminar duplicatas de uma lista
names = ["Alice", "Bob", "Alice", "Charlie", "Bob"]
unique = list(set(names))  # ["Alice", "Bob", "Charlie"] (ordem pode variar)
```

### PHP equivalente:
```php
$unique = array_unique($names);
$diff = array_diff($a, $b);
$intersect = array_intersect($a, $b);
```

---

## Comprehensions — O Superpoder do Python

### List Comprehension
```python
# PHP: array_map(fn($n) => $n * 2, $numbers)
doubled = [n * 2 for n in numbers]

# PHP: array_filter($numbers, fn($n) => $n % 2 === 0)
evens = [n for n in numbers if n % 2 == 0]

# Combinado: filtrar + transformar
big_doubled = [n * 2 for n in numbers if n > 3]

# Aninhado
flat = [x for row in matrix for x in row]
# Equivale a:
# flat = []
# for row in matrix:
#     for x in row:
#         flat.append(x)
```

### Dict Comprehension
```python
# Inverter chave/valor
inverted = {v: k for k, v in original.items()}

# Filtrar dict
active_users = {k: v for k, v in users.items() if v["active"]}

# De duas listas
keys = ["name", "age", "email"]
values = ["Alice", 30, "a@b.com"]
user = {k: v for k, v in zip(keys, values)}
# {"name": "Alice", "age": 30, "email": "a@b.com"}
```

### Set Comprehension
```python
unique_lengths = {len(word) for word in words}
```

### Generator Expression (lazy — econômico em memória)
```python
# List comprehension — cria toda a lista em memória
total = sum([n * 2 for n in range(1_000_000)])

# Generator — calcula um por vez (sem lista intermediária)
total = sum(n * 2 for n in range(1_000_000))
```

---

## Unpacking — Desestruturação

```python
# Tupla/Lista
a, b, c = [1, 2, 3]

# Ignorar valores
_, important, _ = get_data()

# Captura do restante (starred)
first, *rest = [1, 2, 3, 4, 5]
# first = 1, rest = [2, 3, 4, 5]

first, *middle, last = [1, 2, 3, 4, 5]
# first = 1, middle = [2, 3, 4], last = 5

# Dict unpacking em chamada de função
config = {"host": "localhost", "port": 8000}
connect(**config)  # connect(host="localhost", port=8000)

# Dict merge via unpacking
merged = {**defaults, **overrides}
```

### PHP comparado:
```php
[$a, $b, $c] = [1, 2, 3];
// PHP não tem *rest equivalente nativo
// PHP não tem ** para dicts em chamadas
```

---

## Funções Úteis para Coleções

```python
# zip — combina iteráveis
names = ["Alice", "Bob"]
ages = [30, 25]
for name, age in zip(names, ages):
    print(f"{name}: {age}")

# enumerate — índice + valor
for i, name in enumerate(names, start=1):
    print(f"{i}. {name}")

# map + filter (funcional)
doubled = list(map(lambda n: n * 2, numbers))
evens = list(filter(lambda n: n % 2 == 0, numbers))
# Mas comprehensions são preferidas!

# any / all
any([False, True, False])   # True (algum é True)
all([True, True, True])     # True (todos são True)
all([True, False, True])    # False

# min / max / sum
min([3, 1, 4])     # 1
max([3, 1, 4])     # 4
sum([3, 1, 4])     # 8

# sorted com key
users = [{"name": "Bob", "age": 25}, {"name": "Alice", "age": 30}]
sorted_by_name = sorted(users, key=lambda u: u["name"])
sorted_by_age = sorted(users, key=lambda u: u["age"], reverse=True)
```

---

## Anterior: [← Type Hints](02-type-hints.md) | Próximo: [Funções & Decorators →](04-funcoes-decorators.md)
