"""
LangGraph Multi-Agent Workflow — Main State Graph
Orchestrates all 9 agents in a directed workflow.
"""
from __future__ import annotations
from typing import TypedDict, List, Optional, Any, Dict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from app.core.logging import get_logger

logger = get_logger(__name__)


class AgentState(TypedDict):
    """Shared state flowing through all agents."""
    # Input
    query: str
    knowledge_base_id: str
    conversation_id: str
    user_id: str
    model: str
    search_type: str
    top_k: int
    deep_research: bool
    retriever_type: str
    embedding_model: str
    vector_store_type: str

    # Conversation history
    conversation_history: List[Dict[str, str]]

    # Agent 1 — Query Understanding
    query_intent: Optional[str]
    query_type: Optional[str]
    entities: Optional[List[str]]
    refined_query: Optional[str]
    retrieval_strategy: Optional[str]

    # Agent 2 — Retrieval
    retrieved_chunks: Optional[List[Dict[str, Any]]]
    avg_retrieval_score: Optional[float]
    retrieval_metadata: Optional[Dict[str, Any]]

    # Agent 3 — Research
    research_notes: Optional[str]
    research_findings: Optional[List[str]]
    information_gaps: Optional[List[str]]
    web_search_needed: bool
    web_search_results: Optional[List[Dict[str, Any]]]

    # Agent 4 — Summarization
    summary: Optional[str]
    summary_type: Optional[str]

    # Agent 5 — Citation Verification
    verified_citations: Optional[List[Dict[str, Any]]]
    citation_confidence: Optional[float]

    # Agent 6 — Hallucination Detection
    hallucination_risk: Optional[str]  # low | medium | high
    hallucination_score: Optional[float]
    unsupported_claims: Optional[List[str]]

    # Agent 7 — Response Generation
    final_answer: Optional[str]
    citations: Optional[List[Dict[str, Any]]]
    answer_confidence: Optional[float]

    # Agent 8 — Memory
    updated_history: Optional[List[Dict[str, str]]]
    session_context: Optional[Dict[str, Any]]

    # Agent 9 — Feedback
    feedback_stored: bool

    # Metadata
    agents_executed: List[str]
    tokens_used: Optional[int]
    response_time_ms: Optional[float]
    errors: List[str]


def build_agent_graph() -> StateGraph:
    """Build and return the compiled LangGraph agent workflow."""
    from app.agents.query_agent import query_understanding_agent
    from app.agents.retrieval_agent import retrieval_agent
    from app.agents.research_agent import research_agent
    from app.agents.summarization_agent import summarization_agent
    from app.agents.citation_agent import citation_verification_agent
    from app.agents.hallucination_agent import hallucination_detection_agent
    from app.agents.response_agent import response_generation_agent
    from app.agents.memory_agent import memory_agent

    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("query_agent", query_understanding_agent)
    graph.add_node("retrieval_agent", retrieval_agent)
    graph.add_node("research_agent", research_agent)
    graph.add_node("summarization_agent", summarization_agent)
    graph.add_node("citation_agent", citation_verification_agent)
    graph.add_node("hallucination_agent", hallucination_detection_agent)
    graph.add_node("response_agent", response_generation_agent)
    graph.add_node("memory_agent", memory_agent)

    # Define edges — linear flow with conditional branching
    graph.add_edge(START, "query_agent")
    graph.add_edge("query_agent", "retrieval_agent")
    graph.add_edge("retrieval_agent", "research_agent")

    # Conditional: if deep_research requested → summarization → citation → hallucination → response
    # Otherwise → citation → hallucination → response directly
    graph.add_conditional_edges(
        "research_agent",
        _route_after_research,
        {
            "summarization": "summarization_agent",
            "citation": "citation_agent",
        },
    )

    graph.add_edge("summarization_agent", "citation_agent")
    graph.add_edge("citation_agent", "hallucination_agent")
    graph.add_edge("hallucination_agent", "response_agent")
    graph.add_edge("response_agent", "memory_agent")
    graph.add_edge("memory_agent", END)

    return graph.compile()


def _route_after_research(state: AgentState) -> str:
    """Route to summarization if deep_research, otherwise directly to citation."""
    if state.get("deep_research", False):
        return "summarization"
    # Also summarize for summary-type queries
    if state.get("query_type") in ("summary", "research"):
        return "summarization"
    return "citation"


# Compiled graph singleton
compiled_graph = build_agent_graph()


async def run_agent_pipeline(initial_state: AgentState) -> AgentState:
    """Run the full agent pipeline and return the final state."""
    import time
    start = time.time()
    try:
        result = await compiled_graph.ainvoke(initial_state)
        result["response_time_ms"] = (time.time() - start) * 1000
        logger.info(
            "agent_pipeline.complete",
            agents=result.get("agents_executed", []),
            time_ms=result["response_time_ms"],
        )
        return result
    except Exception as e:
        logger.error("agent_pipeline.failed", error=str(e))
        raise
