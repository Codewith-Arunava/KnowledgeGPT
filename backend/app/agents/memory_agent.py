"""
Agent 8 — Memory Agent
Maintains conversation history and session context for follow-up queries.
"""
from app.agents.graph import AgentState
from app.core.logging import get_logger

logger = get_logger(__name__)

MAX_HISTORY_MESSAGES = 20  # Keep last 20 messages in context


async def memory_agent(state: AgentState) -> AgentState:
    """Update conversation history with the new Q&A pair."""
    logger.info("agent.memory.start")

    try:
        history = list(state.get("conversation_history", []))

        # Add the new user message and assistant response
        history.append({"role": "user", "content": state["query"]})
        history.append({
            "role": "assistant",
            "content": state.get("final_answer", ""),
        })

        # Trim to max history length
        if len(history) > MAX_HISTORY_MESSAGES:
            history = history[-MAX_HISTORY_MESSAGES:]

        # Build session context for follow-up queries
        session_context = {
            "last_query": state["query"],
            "last_answer_preview": (state.get("final_answer") or "")[:500],
            "last_documents": [
                c.get("document_name", "")
                for c in (state.get("citations") or [])[:3]
            ],
            "last_retrieval_score": state.get("avg_retrieval_score"),
            "conversation_turns": len(history) // 2,
        }

        state.update({
            "updated_history": history,
            "session_context": session_context,
        })
        state.setdefault("agents_executed", []).append("memory")
        logger.info(
            "agent.memory.done",
            history_length=len(history),
        )
    except Exception as e:
        logger.error("agent.memory.failed", error=str(e))
        state.setdefault("errors", []).append(f"memory_agent: {str(e)}")

    return state
