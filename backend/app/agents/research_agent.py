"""
Agent 3 — Research Agent
Analyzes retrieved chunks, detects information gaps, triggers web search if needed.
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.agents.graph import AgentState
from app.services.embedding import get_llm
from app.services.web_search import web_search
from app.core.logging import get_logger

logger = get_logger(__name__)

RESEARCH_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a Research Agent analyzing retrieved document chunks.
Your job is to:
1. Identify key findings relevant to the query
2. Detect missing information or gaps
3. Determine if web search is needed

Return JSON with:
- research_notes: detailed analysis of the retrieved information
- findings: list of key findings (strings)
- information_gaps: list of what's missing (strings)
- web_search_needed: boolean - true only if critical info is completely missing

Return ONLY valid JSON."""),
    ("human", """Query: {query}
Query Type: {query_type}

Retrieved Context:
{context}

Analyze and return JSON:"""),
])


async def research_agent(state: AgentState) -> AgentState:
    """Analyze retrieved chunks and detect information gaps."""
    logger.info("agent.research.start")

    try:
        chunks = state.get("retrieved_chunks", [])
        if not chunks:
            state.update({
                "research_notes": "No relevant documents found in knowledge base.",
                "research_findings": [],
                "information_gaps": ["No documents retrieved"],
                "web_search_needed": True,
                "web_search_results": [],
            })
            state.setdefault("agents_executed", []).append("research")
            return state

        context = _build_context(chunks)
        llm = get_llm(state.get("model", "gpt-4o"))
        chain = RESEARCH_PROMPT | llm | JsonOutputParser()

        result = await chain.ainvoke({
            "query": state.get("refined_query") or state["query"],
            "query_type": state.get("query_type", "factual"),
            "context": context[:6000],  # Token limit safety
        })

        web_needed = result.get("web_search_needed", False)
        web_results = []

        # Trigger web search if needed and available
        if web_needed:
            logger.info("agent.research.triggering_web_search")
            web_results = await web_search.search(state["query"], max_results=5)

        state.update({
            "research_notes": result.get("research_notes", ""),
            "research_findings": result.get("findings", []),
            "information_gaps": result.get("information_gaps", []),
            "web_search_needed": web_needed,
            "web_search_results": web_results,
        })
        state.setdefault("agents_executed", []).append("research")
        logger.info(
            "agent.research.done",
            findings=len(result.get("findings", [])),
            web_search=web_needed,
        )
    except Exception as e:
        logger.error("agent.research.failed", error=str(e))
        state.update({
            "research_notes": "",
            "research_findings": [],
            "information_gaps": [],
            "web_search_needed": False,
            "web_search_results": [],
        })
        state.setdefault("errors", []).append(f"research_agent: {str(e)}")

    return state


def _build_context(chunks: list, max_chars: int = 8000) -> str:
    parts = []
    total = 0
    for i, chunk in enumerate(chunks):
        meta = chunk.get("metadata", {})
        text = f"[Chunk {i+1}] Source: {meta.get('document_name', 'Unknown')} | Page: {meta.get('page_number', '?')}\n{chunk['content']}\n"
        if total + len(text) > max_chars:
            break
        parts.append(text)
        total += len(text)
    return "\n".join(parts)
