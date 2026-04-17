# 01. Fundamentos Python para Desenvolvedores PHP

## Primeiras Diferenças — Visão Geral

| Conceito | PHP | Python |
|----------|-----|--------|
| Delimitador | `<?php ... ?>` | Nenhum — o arquivo inteiro é código |
| Fim de instrução | `;` obrigatório | Sem `;` — a quebra de linha encerra |
| Blocos | `{ }` | **Indentação** (4 espaços) |
| Variáveis | `$nome` | `nome` (sem `$`) |
| Constantes | `define()`, `const` | `MAIÚSCULAS` por convenção (sem keyword) |
| Comentários | `//`, `/* */` | `#`, `"""docstring"""` |
| Print/Debug | `echo`, `var_dump` | `print()`, `repr()`, `f"{var=}"` |
| Tipagem | Fraca (coerção implícita) | Forte (sem coerção implícita) |

---

## Variáveis & Atribuição

### PHP
```php
$name = "Conn2Flow";
$version = 1;
$price = 19.99;
$active = true;
$data = null;

// Múltipla atribuição
list($a, $b, $c) = [1, 2, 3];
```

### Python
```python
name = "Conn2Flow"
version = 1
price = 19.99
active = True       # Maiúsculo!
data = None         # Maiúsculo!

# Múltipla atribuição (unpacking)
a, b, c = 1, 2, 3

# Swap sem variável temporária
a, b = b, a
```

### Diferenças-chave:
- Sem `$` — variáveis são nomes simples
- `True`, `False`, `None` — são capitalizados (palavras reservadas)
- Sem declaração de tipo na variável (opcionalmente via type hints)
- Unpacking é nativo — sem precisar de `list()`

---

## Tipos Primitivos

| PHP | Python | Exemplo |
|-----|--------|---------|
| `string` | `str` | `"hello"`, `'hello'` |
| `int` | `int` | `42`, `1_000_000` |
| `float` | `float` | `3.14` |
| `bool` | `bool` | `True`, `False` |
| `null` | `None` | `None` |
| `array` (indexado) | `list` | `[1, 2, 3]` |
| `array` (associativo) | `dict` | `{"key": "value"}` |
| N/A | `tuple` | `(1, 2, 3)` — imutável |
| N/A | `set` | `{1, 2, 3}` — sem duplicatas |

### Verificando tipos:
```python
type(42)          # <class 'int'>
type("hello")     # <class 'str'>
isinstance(42, int)  # True
isinstance(42, (int, float))  # True — verifica múltiplos tipos
```

---

## Strings & F-Strings

### PHP
```php
$name = "World";
echo "Hello, $name!";           // Interpolação com aspas duplas
echo "Total: " . ($a + $b);     // Concatenação
echo sprintf("Price: %.2f", $price);
```

### Python
```python
name = "World"
print(f"Hello, {name}!")           # f-string (recomendado!)
print(f"Total: {a + b}")          # Expressões dentro de {}
print(f"Price: {price:.2f}")      # Formatação inline
print(f"{name!r}")                # repr() — útil para debug
print(f"{name=}")                 # Debug: name='World'
```

### Strings multilinha:
```python
query = """
    SELECT *
    FROM users
    WHERE active = 1
"""

# Raw string (sem escapar \)
path = r"C:\Users\folder\new"
```

### Métodos comuns de string:
```python
s = "Hello World"
s.upper()          # "HELLO WORLD"
s.lower()          # "hello world"
s.strip()          # Remove espaços (trim() no PHP)
s.split(" ")       # ["Hello", "World"]
s.replace("o", "0")  # "Hell0 W0rld"
s.startswith("He")   # True
s.endswith("ld")     # True
"llo" in s           # True (str_contains no PHP 8)
len(s)               # 11 (strlen no PHP)
```

---

## Estruturas Condicionais

### PHP
```php
if ($status === "active") {
    echo "Active";
} elseif ($status === "pending") {
    echo "Pending";
} else {
    echo "Unknown";
}
```

### Python
```python
if status == "active":
    print("Active")
elif status == "pending":
    print("Pending")
else:
    print("Unknown")
```

### Diferenças:
- `elif` (não `elseif`)
- `:` ao final da condição
- Sem `{ }` — **indentação define o bloco**
- `==` para comparação (Python não tem `===`)

### Operador ternário:
```python
# PHP: $result = $active ? "yes" : "no";
result = "yes" if active else "no"
```

### Match (Python 3.10+) — equivalente ao `match` do PHP 8.0:
```python
match status:
    case "queued":
        print("In queue")
    case "processing":
        print("Working...")
    case "completed" | "done":
        print("Finished")
    case _:
        print("Unknown")
```

---

## Loops

### `for` — Iteração (o mais usado)
```python
# PHP: foreach ($items as $item) { ... }
for item in items:
    print(item)

# PHP: foreach ($items as $key => $value) { ... }
for key, value in items.items():
    print(f"{key}: {value}")

# PHP: for ($i = 0; $i < 10; $i++) { ... }
for i in range(10):
    print(i)  # 0, 1, 2, ..., 9

# range com início e passo
for i in range(2, 10, 2):
    print(i)  # 2, 4, 6, 8

# enumerate — índice + valor
for index, item in enumerate(items):
    print(f"{index}: {item}")
```

### `while`
```python
count = 0
while count < 10:
    print(count)
    count += 1    # Sem ++ em Python!
```

### Loop Control
```python
for item in items:
    if item.skip:
        continue      # Pular para próxima iteração
    if item.stop:
        break         # Sair do loop
else:
    # Executa se o loop completou sem break!
    print("Loop completed without break")
```

O `else` no `for`/`while` é um recurso exclusivo do Python — executa quando o loop termina normalmente (sem `break`).

---

## Truthiness — O Que É Falsy?

### PHP (== false)
```php
false, 0, 0.0, "", "0", [], null
// Atenção: "0" é falsy em PHP!
```

### Python (bool(x) == False)
```python
False, 0, 0.0, "", [], {}, set(), (), None, 0j
# "0" é TRUTHY em Python! (string não-vazia)
```

### Diferença crítica:
```python
# PHP: "0" é falsy
# Python: "0" é TRUTHY (string com conteúdo)

if "0":
    print("This runs in Python!")  # ✅ Sim, executa

if 0:
    print("This does NOT run")     # ❌ Não executa
```

### Verificação idiomática de None:
```python
# ❌ Não faça
if x == None:

# ✅ Faça
if x is None:
if x is not None:
```

`is` verifica **identidade** (mesmo objeto), `==` verifica **igualdade** (mesmo valor).

---

## Operadores

### Aritméticos
```python
5 + 3      # 8
5 - 3      # 2
5 * 3      # 15
5 / 3      # 1.666... (SEMPRE float!)
5 // 3     # 1 (divisão inteira)
5 % 3      # 2 (módulo)
5 ** 3     # 125 (potência — PHP: pow() ou **)
```

### Lógicos
```python
# PHP: && || !
# Python: and, or, not (palavras, não símbolos)
if active and not deleted:
    ...

if status == "a" or status == "b":
    ...

# Short-circuit — mesmo que PHP
result = value or "default"  # Se value é falsy, usa "default"
```

### Comparação
```python
a == b      # Igualdade (como PHP ==, mas SEM coerção implícita)
a != b      # Diferente
a is b      # Identidade (mesmo objeto — como PHP ===, mas para objetos)
a is not b  # Não é mesmo objeto
a in b      # Pertence (item na lista, key no dict, substring)

# Comparação encadeada (exclusivo do Python!)
if 0 < age < 150:
    print("Valid age")
# Equivale a: if age > 0 and age < 150
```

---

## Compreensões de Lista — Substituição do `array_map`/`array_filter`

### PHP
```php
$numbers = [1, 2, 3, 4, 5];
$doubled = array_map(fn($n) => $n * 2, $numbers);
$evens = array_filter($numbers, fn($n) => $n % 2 === 0);
```

### Python
```python
numbers = [1, 2, 3, 4, 5]
doubled = [n * 2 for n in numbers]          # [2, 4, 6, 8, 10]
evens = [n for n in numbers if n % 2 == 0]  # [2, 4]

# Com transformação + filtro
big_doubled = [n * 2 for n in numbers if n > 3]  # [8, 10]

# Dict comprehension
squares = {n: n**2 for n in range(5)}  # {0:0, 1:1, 2:4, 3:9, 4:16}

# Set comprehension
unique_lengths = {len(word) for word in words}
```

---

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
    return f"{greeting}, {name}!"
```

### Diferenças:
- `def` em vez de `function`
- `:` ao final da assinatura
- Type hints são **opcionais** (mas recomendados)
- `->` para tipo de retorno (em vez de `:` antes do corpo)

---

## Dicas Rápidas para Devs PHP

| PHP | Python | Dica |
|-----|--------|------|
| `echo` | `print()` | Parênteses obrigatórios |
| `var_dump($x)` | `print(repr(x))` ou `print(f"{x=}")` | f-string debug |
| `strlen($s)` | `len(s)` | Função global |
| `count($arr)` | `len(arr)` | Mesma função! |
| `isset($x)` | `x is not None` | Verificação de None |
| `empty($x)` | `not x` | Truthiness check |
| `array_push($a, $v)` | `a.append(v)` | Método do objeto |
| `in_array($v, $a)` | `v in a` | Operador `in` |
| `implode(",", $a)` | `",".join(a)` | Método da string! |
| `explode(",", $s)` | `s.split(",")` | Método da string |
| `die("msg")` | `sys.exit("msg")` | Raro em apps web |

---

## Anterior: [← Índice do Curso](README.md) | Próximo: [Type Hints →](02-type-hints.md)
