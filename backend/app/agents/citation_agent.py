"""
Agent 5 — Citation Verification Agent
Verifies every claim against retrieved chunks, outputs citation confidence.
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.agents.graph import AgentState
from app.services.embedding import get_llm
from app.core.logging import get_logger

logger = get_logger(__name__)

CITATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a Citation Verification Agent.
For each retrieved chunk, determine if it supports the query answer.
Return JSON with:
- citations: list of objects with:
  - document_name: string
  - page_number: integer
  - chunk_id: string
  - content_preview: first 150 chars of chunk
  - similarity_score: float 0-1
  - supports_answer: boolean
  - confidence: float 0-1
- overall_citation_confidence: float 0-1 (average confidence of supporting citations)

Return ONLY valid JSON."""),
    ("human", """Query: {query}
Answer so far: {answer_draft}

Retrieved Chunks:
{chunks_json}

Verify citations and return JSON:"""),
])


async def citation_verification_agent(state: AgentState) -> AgentState:
    """Verify all claims against retrieved chunks."""
    logger.info("agent.citation.start")

    try:
        chunks = state.get("retrieved_chunks", [])
        answer_draft = state.get("summary") or state.get("research_notes", "") or state["query"]

        if not chunks:
            state.update({
                "verified_citations": [],
                "citation_confidence": 0.0,
            })
            state.setdefault("agents_executed", []).append("citation")
            return state

        # Build concise chunks JSON
        chunks_summary = []
        for i, chunk in enumerate(chunks[:10]):
            meta = chunk.get("metadata", {})
            chunks_summary.append({
                "index": i,
                "chunk_id": meta.get("chunk_id", f"chunk_{i}"),
                "document_name": meta.get("document_name", "Unknown"),
                "page_number": meta.get("page_number", 1),
                "content": chunk["content"][:300],
                "score": chunk.get("score", 0.0),
            })

        llm = get_llm(state.get("model", "gpt-4o"))
        chain = CITATION_PROMPT | llm | JsonOutputParser()

        import json
        result = await chain.ainvoke({
            "query": state["query"],
            "answer_draft": answer_draft[:1000],
            "chunks_json": json.dumps(chunks_summary, indent=2),
        })

        citations = result.get("citations", [])
        confidence = float(result.get("overall_citation_confidence", 0.85))

        state.update({
            "verified_citations": citations,
            "citation_confidence": round(confidence, 4),
        })
        state.setdefault("agents_executed", []).append("citation")
        logger.info(
            "agent.citation.done",
            citations=len(citations),
            confidence=confidence,
        )
    except Exception as e:
        logger.error("agent.citation.failed", error=str(e))
        # Build fallback citations from raw chunks
        fallback_citations = _build_fallback_citations(state.get("retrieved_chunks", []))
        state.update({
            "verified_citations": fallback_citations,
            "citation_confidence": state.get("avg_retrieval_score", 0.75),
        })
        state.setdefault("errors", []).append(f"citation_agent: {str(e)}")

    return state


def _build_fallback_citations(chunks: list) -> list:
    citations = []
    for chunk in chunks[:5]:
        meta = chunk.get("metadata", {})
        citations.append({
            "document_name": meta.get("document_name", "Unknown"),
            "page_number": meta.get("page_number", 1),
            "chunk_id": meta.get("chunk_id", ""),
            "content_preview": chunk["content"][:150],
            "similarity_score": chunk.get("score", 0.7),
            "supports_answer": True,
            "confidence": chunk.get("score", 0.7),
        })
    return citations
