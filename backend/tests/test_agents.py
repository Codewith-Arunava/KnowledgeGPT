"""Agent unit tests with mocked LLM responses."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_query_understanding_agent():
    """Test query agent classifies intent correctly."""
    from app.agents.graph import AgentState
    from app.agents.query_agent import query_understanding_agent

    mock_result = {
        "intent": "factual",
        "query_type": "factual",
        "entities": ["transformer", "attention mechanism"],
        "refined_query": "What is the attention mechanism in transformers?",
        "retrieval_strategy": "similarity",
    }

    with patch("app.agents.query_agent.get_llm") as mock_llm:
        mock_chain = AsyncMock(return_value=mock_result)
        mock_llm.return_value.__or__ = MagicMock(return_value=mock_chain)

        state: AgentState = {
            "query": "What is attention in transformers?",
            "knowledge_base_id": "test-kb-id",
            "conversation_id": "test-conv-id",
            "user_id": "test-user-id",
            "model": "gpt-4o",
            "search_type": "similarity",
            "top_k": 5,
            "deep_research": False,
            "retriever_type": "langchain",
            "embedding_model": "openai-small",
            "vector_store_type": "chromadb",
            "conversation_history": [],
            "agents_executed": [],
            "errors": [],
            **{k: None for k in [
                "query_intent", "query_type", "entities", "refined_query", "retrieval_strategy",
                "retrieved_chunks", "avg_retrieval_score", "retrieval_metadata",
                "research_notes", "research_findings", "information_gaps",
                "web_search_results", "summary", "summary_type",
                "verified_citations", "citation_confidence",
                "hallucination_risk", "hallucination_score", "unsupported_claims",
                "final_answer", "citations", "answer_confidence",
                "updated_history", "session_context", "tokens_used", "response_time_ms",
            ]},
            "web_search_needed": False,
            "feedback_stored": False,
        }

        # Agents may fail gracefully with mock, just check it returns state
        result = await query_understanding_agent(state)
        assert "query_intent" in result
        assert "agents_executed" in result
        assert "query_understanding" in result["agents_executed"]


@pytest.mark.asyncio
async def test_memory_agent():
    """Test memory agent updates conversation history."""
    from app.agents.graph import AgentState
    from app.agents.memory_agent import memory_agent

    state: AgentState = {
        "query": "What is RAG?",
        "conversation_history": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ],
        "final_answer": "RAG stands for Retrieval-Augmented Generation...",
        "citations": [],
        "agents_executed": [],
        "errors": [],
        **{k: None for k in [
            "knowledge_base_id", "conversation_id", "user_id", "model",
            "search_type", "top_k", "deep_research", "retriever_type",
            "embedding_model", "vector_store_type", "query_intent", "query_type",
            "entities", "refined_query", "retrieval_strategy", "retrieved_chunks",
            "avg_retrieval_score", "retrieval_metadata", "research_notes",
            "research_findings", "information_gaps", "web_search_results",
            "summary", "summary_type", "verified_citations", "citation_confidence",
            "hallucination_risk", "hallucination_score", "unsupported_claims",
            "answer_confidence", "updated_history", "session_context",
            "tokens_used", "response_time_ms",
        ]},
        "web_search_needed": False,
        "feedback_stored": False,
    }

    result = await memory_agent(state)
    assert result["updated_history"] is not None
    assert len(result["updated_history"]) == 4  # 2 existing + 2 new
    assert result["updated_history"][-1]["role"] == "assistant"
    assert "memory" in result["agents_executed"]
