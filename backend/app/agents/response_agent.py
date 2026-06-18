"""
Agent 7 — Response Generation Agent
Generates the final formatted answer with Markdown, citations, and confidence.
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.agents.graph import AgentState
from app.services.embedding import get_llm
from app.core.logging import get_logger

logger = get_logger(__name__)

RESPONSE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a Response Generation Agent creating the final answer for the user.

Guidelines:
- Use Markdown formatting (headers, bullets, **bold**, code blocks, tables)
- Be precise and cite sources inline using [Doc Name, p.X] notation
- If hallucination risk is high, add a warning note
- For code: use proper code blocks with language identifier
- End with numbered citation list if there are sources
- Be comprehensive but concise

Hallucination Risk: {hallucination_risk}
Query Type: {query_type}"""),
    ("human", """Original Query: {query}
Research Notes: {research_notes}
Summary: {summary}
Verified Citations: {citations_json}

Retrieved Context:
{context}

Generate the final answer:"""),
])


async def response_generation_agent(state: AgentState) -> AgentState:
    """Generate the final formatted answer with inline citations."""
    logger.info("agent.response.start")

    try:
        chunks = state.get("retrieved_chunks", [])
        context = "\n\n".join([
            f"**[{c['metadata'].get('document_name','?')} | p.{c['metadata'].get('page_number','?')}]**\n{c['content'][:500]}"
            for c in chunks[:5]
        ])

        citations_data = state.get("verified_citations", [])
        import json
        citations_json = json.dumps(
            [{k: v for k, v in c.items() if k != "content_preview"} for c in citations_data[:8]],
            indent=2,
        )

        llm = get_llm(state.get("model", "gpt-4o"))
        chain = RESPONSE_PROMPT | llm | StrOutputParser()

        final_answer = await chain.ainvoke({
            "query": state["query"],
            "research_notes": (state.get("research_notes") or "")[:2000],
            "summary": (state.get("summary") or "")[:2000],
            "citations_json": citations_json[:2000],
            "context": context[:5000],
            "hallucination_risk": state.get("hallucination_risk", "low"),
            "query_type": state.get("query_type", "factual"),
        })

        # Compute answer confidence (inverse of hallucination + avg retrieval)
        h_score = state.get("hallucination_score", 0.1)
        r_score = state.get("avg_retrieval_score", 0.8)
        c_score = state.get("citation_confidence", 0.85)
        answer_confidence = round((1 - h_score) * 0.4 + r_score * 0.3 + c_score * 0.3, 4)

        # Build final citations list
        final_citations = [
            {
                "document_name": c.get("document_name", "Unknown"),
                "page_number": c.get("page_number", 1),
                "chunk_id": c.get("chunk_id", ""),
                "content_preview": c.get("content_preview", ""),
                "similarity_score": c.get("similarity_score", 0.0),
            }
            for c in citations_data
            if c.get("supports_answer", True)
        ]

        state.update({
            "final_answer": final_answer,
            "citations": final_citations,
            "answer_confidence": answer_confidence,
        })
        state.setdefault("agents_executed", []).append("response")
        logger.info(
            "agent.response.done",
            answer_length=len(final_answer),
            confidence=answer_confidence,
        )
    except Exception as e:
        logger.error("agent.response.failed", error=str(e))
        state.update({
            "final_answer": state.get("summary") or "I could not generate a response. Please try again.",
            "citations": [],
            "answer_confidence": 0.5,
        })
        state.setdefault("errors", []).append(f"response_agent: {str(e)}")

    return state
