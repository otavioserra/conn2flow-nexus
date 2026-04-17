"""
Conn2Flow Nexus AI - LangGraph Task Processing Graph
Stateful graph for task orchestration with nodes:
  validate_input → call_llm → format_output
"""

from __future__ import annotations

import logging
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from src.core.llm_router import call_llm

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# State schema
# ---------------------------------------------------------------------------

class TaskGraphState(TypedDict):
    """Shared state between graph nodes."""
    task_id: str
    model: str
    messages: list[dict[str, str]]
    temperature: float
    max_tokens: int | None
    # Populated by call_llm node
    llm_response: dict[str, Any] | None
    error: str | None
    status: str


# ---------------------------------------------------------------------------
# Graph Nodes
# ---------------------------------------------------------------------------

async def validate_input(state: TaskGraphState) -> dict[str, Any]:
    """Validates and normalizes input before calling the LLM."""
    messages = state.get("messages", [])

    if not messages:
        return {"error": "No messages provided", "status": "failed"}

    # Ensure there is at least one user message
    has_user = any(m.get("role") == "user" for m in messages)
    if not has_user:
        return {"error": "At least one user message is required", "status": "failed"}

    logger.debug("[graph] Input validated — task=%s model=%s", state["task_id"], state["model"])
    return {"status": "processing"}


async def invoke_llm(state: TaskGraphState) -> dict[str, Any]:
    """Calls the LLM via LiteLLM router."""
    if state.get("error"):
        return {}  # Skip if validation already failed

    try:
        result = await call_llm(
            model=state["model"],
            messages=state["messages"],
            temperature=state.get("temperature", 0.7),
            max_tokens=state.get("max_tokens"),
        )
        logger.info("[graph] LLM completed — task=%s model=%s", state["task_id"], result["model_used"])
        return {"llm_response": result, "status": "completed"}

    except Exception as exc:
        logger.exception("[graph] LLM failed — task=%s", state["task_id"])
        return {
            "error": f"LLM error: {type(exc).__name__}: {exc}",
            "status": "failed",
        }


async def format_output(state: TaskGraphState) -> dict[str, Any]:
    """Formats the final result (noop for now, ready for post-processing)."""
    if state.get("error"):
        logger.warning("[graph] Task failed — task=%s error=%s", state["task_id"], state["error"])
    else:
        logger.info("[graph] Task completed — task=%s", state["task_id"])
    return {}


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def should_call_llm(state: TaskGraphState) -> str:
    """Decides whether to proceed to LLM or skip to output (if already failed)."""
    if state.get("error"):
        return "format_output"
    return "invoke_llm"


# ---------------------------------------------------------------------------
# Build Graph
# ---------------------------------------------------------------------------

def build_task_graph() -> StateGraph:
    """Builds and compiles the task processing graph.

    Flow: START → validate_input → (invoke_llm | format_output) → END
    """
    graph = StateGraph(TaskGraphState)

    # Nodes
    graph.add_node("validate_input", validate_input)
    graph.add_node("invoke_llm", invoke_llm)
    graph.add_node("format_output", format_output)

    # Edges
    graph.add_edge(START, "validate_input")
    graph.add_conditional_edges("validate_input", should_call_llm)
    graph.add_edge("invoke_llm", "format_output")
    graph.add_edge("format_output", END)

    return graph


# Compiled and ready to use
task_graph = build_task_graph().compile()


async def run_task_graph(
    task_id: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int | None = None,
) -> TaskGraphState:
    """Executes the processing graph for a task.

    Returns:
        Final state with llm_response or error.
    """
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
