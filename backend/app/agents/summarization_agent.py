"""
Agent 4 — Summarization Agent
Generates Short, Detailed, Executive, and Academic summaries.
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.agents.graph import AgentState
from app.services.embedding import get_llm
from app.core.logging import get_logger

logger = get_logger(__name__)

SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a Summarization Agent. Generate a comprehensive summary of the provided content.

Summary Type: {summary_type}

Summary Guidelines:
- short: 2-3 sentences capturing the core answer
- detailed: Full paragraphs covering all key points with evidence
- executive: Business-focused, key decisions and outcomes
- academic: Structured with methodology, findings, and implications

Use markdown formatting. Be precise and cite specific information from the context."""),
    ("human", """Query: {query}
Research Notes: {research_notes}

Context:
{context}

Generate a {summary_type} summary:"""),
])


async def summarization_agent(state: AgentState) -> AgentState:
    """Generate appropriate summary based on query type."""
    logger.info("agent.summarization.start")

    try:
        # Determine summary type from query type
        query_type = state.get("query_type", "factual")
        summary_type_map = {
            "summary": "detailed",
            "research": "academic",
            "factual": "short",
            "comparison": "detailed",
            "explanation": "detailed",
            "document_lookup": "short",
        }
        summary_type = summary_type_map.get(query_type, "detailed")
        if state.get("deep_research"):
            summary_type = "academic"

        chunks = state.get("retrieved_chunks", [])
        context = _build_context_with_web(chunks, state.get("web_search_results", []))

        llm = get_llm(state.get("model", "gpt-4o"))
        chain = SUMMARY_PROMPT | llm | StrOutputParser()

        summary = await chain.ainvoke({
            "query": state.get("refined_query") or state["query"],
            "research_notes": state.get("research_notes", ""),
            "context": context[:8000],
            "summary_type": summary_type,
        })

        state.update({
            "summary": summary,
            "summary_type": summary_type,
        })
        state.setdefault("agents_executed", []).append("summarization")
        logger.info("agent.summarization.done", type=summary_type, length=len(summary))
    except Exception as e:
        logger.error("agent.summarization.failed", error=str(e))
        state.update({"summary": "", "summary_type": "short"})
        state.setdefault("errors", []).append(f"summarization_agent: {str(e)}")

    return state


def _build_context_with_web(chunks: list, web_results: list) -> str:
    parts = []
    for i, chunk in enumerate(chunks[:8]):
        meta = chunk.get("metadata", {})
        parts.append(
            f"[Doc {i+1}] {meta.get('document_name','?')} p.{meta.get('page_number','?')}: {chunk['content'][:500]}"
        )
    for i, result in enumerate(web_results[:3]):
        parts.append(f"[Web {i+1}] {result.get('title','')}: {result.get('content','')[:300]}")
    return "\n\n".join(parts)
