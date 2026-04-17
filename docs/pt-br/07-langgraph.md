# 7. LangGraph — Orquestração com Grafos de Estado

## O Que É LangGraph?

**LangGraph** é uma biblioteca do ecossistema **LangChain** para construir aplicações LLM como **grafos de estado** (State Graphs). Em vez de escrever lógica sequencial, você define:

1. **State** — os dados que fluem pelo grafo
2. **Nodes** — funções que transformam o estado
3. **Edges** — conexões entre nodes (podem ser condicionais)

### Por que usar LangGraph em vez de código sequencial?

| Código Sequencial | LangGraph |
|-------------------|-----------|
| `if/else` aninhados | Routing condicional visual |
| Difícil de estender | Adicionar um node = 2 linhas |
| Estado implícito | Estado explícito e tipado |
| Sem retry nativo | Checkpoint + retry nativo |
| Difícil de debugar | Cada node tem input/output claro |

---

## Conceitos Fundamentais

### StateGraph

Um `StateGraph` é um **grafo direcionado** onde:
- Cada **node** é uma função que recebe e modifica o **state**
- **Edges** conectam nodes em uma sequência
- **Conditional edges** escolhem o próximo node baseado no state

```
START → validate_input → [condição] → invoke_llm → format_output → END
                              │
                              └─ (se erro) → format_output → END
```

### State (Estado)

O state é compartilhado entre todos os nodes. É como um "documento" que cada node pode ler e modificar:

```python
class TaskGraphState(TypedDict):
    task_id: str
    model: str
    messages: list[dict[str, str]]
    temperature: float
    max_tokens: int | None
    llm_response: dict[str, Any] | None   # Preenchido pelo invoke_llm
    error: str | None                      # Preenchido se houver erro
    status: str                            # queued → processing → completed/failed
```

**Conceito: `TypedDict`**
- `TypedDict` é uma forma de tipar dicionários Python
- Diferente de `dataclass`, permanece como um `dict` normal em runtime
- LangGraph usa TypedDict para definir o schema do state
- O IDE consegue autocompletar e validar os campos

---

## Implementação: `src/graphs/base_graph.py`

### Node 1: Validação de Input

```python
async def validate_input(state: TaskGraphState) -> dict[str, Any]:
    messages = state.get("messages", [])

    if not messages:
        return {"error": "No messages provided", "status": "failed"}

    has_user = any(m.get("role") == "user" for m in messages)
    if not has_user:
        return {"error": "At least one user message is required", "status": "failed"}

    return {"status": "processing"}
```

**Conceito: Retorno Parcial**
- Cada node retorna apenas os campos que **quer modificar** no state
- `{"status": "processing"}` → atualiza apenas `status`, deixando os demais intactos
- LangGraph faz o **merge** automaticamente: `state = {**state, **node_output}`

**Conceito: `any()` com Generator Expression**
```python
has_user = any(m.get("role") == "user" for m in messages)
```
- `any()` retorna `True` se **pelo menos um** elemento for truthy
- A generator expression `(... for m in messages)` é avaliada **lazily** — para no primeiro `True`
- Mais eficiente que criar uma lista inteira para depois verificar

### Node 2: Chamada ao LLM

```python
async def invoke_llm(state: TaskGraphState) -> dict[str, Any]:
    if state.get("error"):
        return {}  # Pula se já falhou

    try:
        result = await call_llm(
            model=state["model"],
            messages=state["messages"],
            temperature=state.get("temperature", 0.7),
            max_tokens=state.get("max_tokens"),
        )
        return {"llm_response": result, "status": "completed"}
    except Exception as exc:
        return {
            "error": f"LLM error: {type(exc).__name__}: {exc}",
            "status": "failed",
        }
```

**Conceito: `type(exc).__name__`**
- Obtém o nome da classe da exceção (ex: `"RateLimitError"`, `"TimeoutError"`)
- Útil para logs — saber **que tipo** de erro aconteceu
- `f"LLM error: {type(exc).__name__}: {exc}"` → `"LLM error: RateLimitError: Rate limit exceeded"`

### Node 3: Formatação de Output

```python
async def format_output(state: TaskGraphState) -> dict[str, Any]:
    if state.get("error"):
        logger.warning("[graph] Task failed — task=%s error=%s", state["task_id"], state["error"])
    else:
        logger.info("[graph] Task completed — task=%s", state["task_id"])
    return {}  # Noop por enquanto — pronto para pós-processamento
```

- Atualmente é um **noop** (no operation) — não modifica o state
- Existe como **ponto de extensão**: aqui podemos adicionar:
  - Formatação de resposta
  - Sanitização de conteúdo
  - Extração de dados estruturados
  - Tradução automática

### Routing Condicional

```python
def should_call_llm(state: TaskGraphState) -> str:
    if state.get("error"):
        return "format_output"   # Pula o LLM, vai direto pro output
    return "invoke_llm"          # Segue para o LLM
```

**Conceito: Conditional Edge**
```python
graph.add_conditional_edges("validate_input", should_call_llm)
```
- Após `validate_input`, LangGraph chama `should_call_llm(state)`
- O **retorno** é o **nome do próximo node**
- Isso cria um "desvio" no grafo:
  - Se input válido → `invoke_llm` → `format_output` → END
  - Se input inválido → `format_output` → END (pula o LLM)

### Montagem do Grafo

```python
def build_task_graph() -> StateGraph:
    graph = StateGraph(TaskGraphState)

    # Registra os nodes
    graph.add_node("validate_input", validate_input)
    graph.add_node("invoke_llm", invoke_llm)
    graph.add_node("format_output", format_output)

    # Define o fluxo
    graph.add_edge(START, "validate_input")                    # Início → validação
    graph.add_conditional_edges("validate_input", should_call_llm)  # Condição
    graph.add_edge("invoke_llm", "format_output")              # LLM → output
    graph.add_edge("format_output", END)                       # Output → fim

    return graph

# Compila uma vez e reutiliza
task_graph = build_task_graph().compile()
```

**Conceito: `compile()`**
- `compile()` valida o grafo (sem edges soltas, sem ciclos infinitos)
- Retorna um objeto executável otimizado
- Chamamos **uma vez** na importação do módulo (nível de módulo)

### Execução

```python
async def run_task_graph(task_id, model, messages, temperature, max_tokens):
    initial_state: TaskGraphState = {
        "task_id": task_id,
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "llm_response": None,
        "error": None,
        "status": "queued",
    }
    result = await task_graph.ainvoke(initial_state)
    return result
```

**Conceito: `ainvoke` vs `invoke`**
- `ainvoke()` = invocação **assíncrona** — usa `await`
- `invoke()` = invocação síncrona
- Como nossos nodes são `async def`, usamos `ainvoke()`

---

## Visualização do Grafo

```
    ┌──────────┐
    │  START    │
    └────┬─────┘
         │
    ┌────▼──────────┐
    │ validate_input │
    └────┬──────────┘
         │
    ┌────▼──────────────┐
    │ should_call_llm?  │
    └──┬────────────┬───┘
       │            │
  (válido)    (com erro)
       │            │
  ┌────▼────┐  ┌────▼───────────┐
  │invoke_llm│  │ format_output  │
  └────┬────┘  └────┬───────────┘
       │            │
  ┌────▼───────────┐│
  │ format_output  ││
  └────┬───────────┘│
       │            │
    ┌──▼────────────▼┐
    │      END        │
    └─────────────────┘
```

---

## Anterior: [← LiteLLM](06-litellm.md) | Próximo: [Workers →](08-workers.md)
