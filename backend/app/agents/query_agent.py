"""
Agent 1 — Query Understanding Agent
Detects intent, classifies query type, extracts entities, refines query.
"""
from typing import Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.agents.graph import AgentState
from app.services.embedding import get_llm
from app.core.logging import get_logger

logger = get_logger(__name__)

QUERY_UNDERSTANDING_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a Query Understanding Agent for a RAG system.
Analyze the user query and return a JSON with exactly these fields:
- intent: one of [factual, summary, comparison, research, explanation, document_lookup]
- query_type: same as intent
- entities: list of key entities/topics extracted
- refined_query: an improved, more specific version of the original query for better retrieval
- retrieval_strategy: one of [similarity, mmr, hybrid]

Return ONLY valid JSON, no markdown, no explanation."""),
    ("human", """Query: {query}
Conversation history: {history}

Analyze and return JSON:"""),
])


async def query_understanding_agent(state: AgentState) -> AgentState:
    """Classify intent, extract entities, refine query for retrieval."""
    logger.info("agent.query_understanding.start", query=state["query"][:100])

    try:
        llm = get_llm(state.get("model", "gpt-4o"))
        chain = QUERY_UNDERSTANDING_PROMPT | llm | JsonOutputParser()

        history_str = _format_history(state.get("conversation_history", []))
        result = await chain.ainvoke({
            "query": state["query"],
            "history": history_str,
        })

        state.update({
            "query_intent": result.get("intent", "factual"),
            "query_type": result.get("query_type", "factual"),
            "entities": result.get("entities", []),
            "refined_query": result.get("refined_query", state["query"]),
            "retrieval_strategy": result.get("retrieval_strategy", "similarity"),
        })
        state.setdefault("agents_executed", []).append("query_understanding")
        logger.info(
            "agent.query_understanding.done",
            intent=state["query_intent"],
            type=state["query_type"],
        )
    except Exception as e:
        logger.error("agent.query_understanding.failed", error=str(e))
        state.update({
            "query_intent": "factual",
            "query_type": "factual",
            "entities": [],
            "refined_query": state["query"],
            "retrieval_strategy": state.get("search_type", "similarity"),
        })
        state.setdefault("errors", []).append(f"query_agent: {str(e)}")

    return state


def _format_history(history: list) -> str:
    if not history:
        return "No previous conversation."
    return "\n".join([f"{m['role'].upper()}: {m['content'][:200]}" for m in history[-6:]])
