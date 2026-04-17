# 7. LangGraph — State Graph Orchestration

## What Is LangGraph?

**LangGraph** is a library from the **LangChain** ecosystem for building LLM applications as **state graphs** (State Graphs). Instead of writing sequential logic, you define:

1. **State** — the data flowing through the graph
2. **Nodes** — functions that transform the state
3. **Edges** — connections between nodes (can be conditional)

### Why Use LangGraph Instead of Sequential Code?

| Sequential Code | LangGraph |
|----------------|-----------|
| Nested `if/else` | Visual conditional routing |
| Hard to extend | Adding a node = 2 lines |
| Implicit state | Explicit, typed state |
| No native retry | Native checkpoint + retry |
| Hard to debug | Each node has clear input/output |

---

## Fundamental Concepts

### StateGraph

A `StateGraph` is a **directed graph** where:
- Each **node** is a function that receives and modifies the **state**
- **Edges** connect nodes in a sequence
- **Conditional edges** choose the next node based on the state

```
START → validate_input → [condition] → invoke_llm → format_output → END
                              │
                              └─ (if error) → format_output → END
```

### State

The state is shared between all nodes. It's like a "document" that each node can read and modify:

```python
class TaskGraphState(TypedDict):
    task_id: str
    model: str
    messages: list[dict[str, str]]
    temperature: float
    max_tokens: int | None
    llm_response: dict[str, Any] | None   # Filled by invoke_llm
    error: str | None                      # Filled if there's an error
    status: str                            # queued → processing → completed/failed
```

**Concept: `TypedDict`**
- `TypedDict` is a way to type Python dictionaries
- Unlike `dataclass`, it remains a normal `dict` at runtime
- LangGraph uses TypedDict to define the state schema
- The IDE can autocomplete and validate fields

---

## Implementation: `src/graphs/base_graph.py`

### Node 1: Input Validation

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

**Concept: Partial Return**
- Each node returns only the fields it **wants to modify** in the state
- `{"status": "processing"}` → updates only `status`, leaving the rest intact
- LangGraph performs the **merge** automatically: `state = {**state, **node_output}`

**Concept: `any()` with Generator Expression**
```python
has_user = any(m.get("role") == "user" for m in messages)
```
- `any()` returns `True` if **at least one** element is truthy
- The generator expression `(... for m in messages)` is evaluated **lazily** — stops at the first `True`
- More efficient than creating an entire list just to check it

### Node 2: LLM Call

```python
async def invoke_llm(state: TaskGraphState) -> dict[str, Any]:
    if state.get("error"):
        return {}  # Skip if validation already failed

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

**Concept: `type(exc).__name__`**
- Gets the class name of the exception (e.g., `"RateLimitError"`, `"TimeoutError"`)
- Useful for logs — knowing **what type** of error occurred
- `f"LLM error: {type(exc).__name__}: {exc}"` → `"LLM error: RateLimitError: Rate limit exceeded"`

### Node 3: Output Formatting

```python
async def format_output(state: TaskGraphState) -> dict[str, Any]:
    if state.get("error"):
        logger.warning("[graph] Task failed — task=%s error=%s", state["task_id"], state["error"])
    else:
        logger.info("[graph] Task completed — task=%s", state["task_id"])
    return {}  # Noop for now — ready for post-processing
```

- Currently a **noop** (no operation) — doesn't modify the state
- Exists as an **extension point**: here we could add:
  - Response formatting
  - Content sanitization
  - Structured data extraction
  - Automatic translation

### Conditional Routing

```python
def should_call_llm(state: TaskGraphState) -> str:
    if state.get("error"):
        return "format_output"   # Skip LLM, go straight to output
    return "invoke_llm"          # Proceed to LLM
```

**Concept: Conditional Edge**
```python
graph.add_conditional_edges("validate_input", should_call_llm)
```
- After `validate_input`, LangGraph calls `should_call_llm(state)`
- The **return value** is the **name of the next node**
- This creates a "branch" in the graph:
  - If input is valid → `invoke_llm` → `format_output` → END
  - If input is invalid → `format_output` → END (skips LLM)

### Graph Assembly

```python
def build_task_graph() -> StateGraph:
    graph = StateGraph(TaskGraphState)

    # Register nodes
    graph.add_node("validate_input", validate_input)
    graph.add_node("invoke_llm", invoke_llm)
    graph.add_node("format_output", format_output)

    # Define the flow
    graph.add_edge(START, "validate_input")                    # Start → validation
    graph.add_conditional_edges("validate_input", should_call_llm)  # Condition
    graph.add_edge("invoke_llm", "format_output")              # LLM → output
    graph.add_edge("format_output", END)                       # Output → end

    return graph

# Compile once and reuse
task_graph = build_task_graph().compile()
```

**Concept: `compile()`**
- `compile()` validates the graph (no dangling edges, no infinite cycles)
- Returns an optimized executable object
- Called **once** at module import time (module level)

### Execution

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

**Concept: `ainvoke` vs `invoke`**
- `ainvoke()` = **asynchronous** invocation — uses `await`
- `invoke()` = synchronous invocation
- Since our nodes are `async def`, we use `ainvoke()`

---

## Graph Visualization

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
   (valid)     (has error)
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

## Previous: [← LiteLLM](06-litellm.md) | Next: [Workers →](08-workers.md)
