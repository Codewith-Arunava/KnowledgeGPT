"""
Agent 2 — Retrieval Agent
Fetches top-K chunks from vector store, ranks by score.
"""
from typing import Any, List, Dict
from app.agents.graph import AgentState
from app.services.retriever import get_retriever
from app.core.logging import get_logger

logger = get_logger(__name__)


async def retrieval_agent(state: AgentState) -> AgentState:
    """Retrieve top-K chunks from the knowledge base vector store."""
    logger.info("agent.retrieval.start", kb=state["knowledge_base_id"])

    try:
        retriever = get_retriever(
            collection_name=f"kb_{state['knowledge_base_id'].replace('-', '_')}",
            retriever_type=state.get("retriever_type", "langchain"),
            embedding_model=state.get("embedding_model", "openai-small"),
            vector_store_type=state.get("vector_store_type", "chromadb"),
        )

        # Use refined query if available
        query = state.get("refined_query") or state["query"]
        search_type = state.get("retrieval_strategy") or state.get("search_type", "similarity")
        k = state.get("top_k", 5)

        chunks = retriever.retrieve(query=query, search_type=search_type, k=k)

        # Rank chunks by score (descending)
        chunks.sort(key=lambda x: x.get("score", 0), reverse=True)

        # Compute average retrieval score
        scores = [c.get("score", 0) for c in chunks if c.get("score")]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        state.update({
            "retrieved_chunks": chunks,
            "avg_retrieval_score": round(avg_score, 4),
            "retrieval_metadata": {
                "search_type": search_type,
                "k": k,
                "retriever_type": state.get("retriever_type", "langchain"),
                "chunks_found": len(chunks),
            },
        })
        state.setdefault("agents_executed", []).append("retrieval")
        logger.info(
            "agent.retrieval.done",
            chunks=len(chunks),
            avg_score=avg_score,
        )
    except Exception as e:
        logger.error("agent.retrieval.failed", error=str(e))
        state.update({
            "retrieved_chunks": [],
            "avg_retrieval_score": 0.0,
        })
        state.setdefault("errors", []).append(f"retrieval_agent: {str(e)}")

    return state
