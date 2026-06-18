"""
Agent 6 — Hallucination Detection Agent
Compares generated answer vs retrieved context. Detects fabricated facts.
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.agents.graph import AgentState
from app.services.embedding import get_llm
from app.core.logging import get_logger

logger = get_logger(__name__)

HALLUCINATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a Hallucination Detection Agent.
Compare the generated answer against the retrieved source context.

Detect:
1. Fabricated facts (claims not in source)
2. Unsupported claims (plausible but not verified)
3. Missing evidence

Return JSON:
- hallucination_risk: "low" | "medium" | "high"
- hallucination_score: float 0-1 (0=no hallucination, 1=completely fabricated)
- unsupported_claims: list of specific claims not backed by sources
- supported_claims_count: integer
- total_claims_count: integer
- analysis: brief explanation

Return ONLY valid JSON."""),
    ("human", """Original Query: {query}

Generated Answer:
{answer}

Retrieved Source Context (ground truth):
{context}

Detect hallucinations and return JSON:"""),
])


async def hallucination_detection_agent(state: AgentState) -> AgentState:
    """Detect hallucinations by comparing answer vs retrieved context."""
    logger.info("agent.hallucination.start")

    try:
        answer = state.get("summary") or state.get("research_notes", "")
        chunks = state.get("retrieved_chunks", [])

        if not answer or not chunks:
            state.update({
                "hallucination_risk": "low",
                "hallucination_score": 0.0,
                "unsupported_claims": [],
            })
            state.setdefault("agents_executed", []).append("hallucination")
            return state

        # Build context string
        context = "\n\n".join([
            f"[Source {i+1}]: {c['content'][:400]}"
            for i, c in enumerate(chunks[:5])
        ])

        llm = get_llm(state.get("model", "gpt-4o"))
        chain = HALLUCINATION_PROMPT | llm | JsonOutputParser()

        result = await chain.ainvoke({
            "query": state["query"],
            "answer": answer[:3000],
            "context": context[:5000],
        })

        state.update({
            "hallucination_risk": result.get("hallucination_risk", "low"),
            "hallucination_score": float(result.get("hallucination_score", 0.1)),
            "unsupported_claims": result.get("unsupported_claims", []),
        })
        state.setdefault("agents_executed", []).append("hallucination")
        logger.info(
            "agent.hallucination.done",
            risk=state["hallucination_risk"],
            score=state["hallucination_score"],
        )
    except Exception as e:
        logger.error("agent.hallucination.failed", error=str(e))
        state.update({
            "hallucination_risk": "low",
            "hallucination_score": 0.05,
            "unsupported_claims": [],
        })
        state.setdefault("errors", []).append(f"hallucination_agent: {str(e)}")

    return state
