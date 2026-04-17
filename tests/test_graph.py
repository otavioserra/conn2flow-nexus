"""
Tests for the LangGraph (task processing graph).
"""

import pytest
from unittest.mock import AsyncMock, patch


class TestTaskGraph:

    @pytest.mark.asyncio
    @patch("src.graphs.base_graph.call_llm", new_callable=AsyncMock)
    async def test_successful_graph_execution(self, mock_llm):
        from src.graphs.base_graph import run_task_graph

        mock_llm.return_value = {
            "content": "LLM Response",
            "model_used": "gpt-4o-mini",
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            "finish_reason": "stop",
        }

        result = await run_task_graph(
            task_id="test-1",
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
        )

        assert result["status"] == "completed"
        assert result["llm_response"]["content"] == "LLM Response"
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_empty_messages_fails(self):
        from src.graphs.base_graph import run_task_graph

        result = await run_task_graph(
            task_id="test-2",
            model="gpt-4o-mini",
            messages=[],
        )

        assert result["status"] == "failed"
        assert result["error"] is not None
        assert "No messages" in result["error"]

    @pytest.mark.asyncio
    async def test_no_user_message_fails(self):
        from src.graphs.base_graph import run_task_graph

        result = await run_task_graph(
            task_id="test-3",
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You are helpful"}],
        )

        assert result["status"] == "failed"
        assert "user message" in result["error"]

    @pytest.mark.asyncio
    @patch("src.graphs.base_graph.call_llm", new_callable=AsyncMock)
    async def test_llm_error_caught(self, mock_llm):
        from src.graphs.base_graph import run_task_graph

        mock_llm.side_effect = RuntimeError("API exploded")

        result = await run_task_graph(
            task_id="test-4",
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Explode"}],
        )

        assert result["status"] == "failed"
        assert "LLM error" in result["error"]
        assert "API exploded" in result["error"]
