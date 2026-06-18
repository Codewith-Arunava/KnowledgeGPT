"""
Web Search Service — Tavily & Serper API integration for fallback RAG.
"""
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class WebSearchService:
    """Web search with Tavily (primary) or Serper (fallback)."""

    async def search(
        self, query: str, max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Search the web and return structured results."""
        if settings.has_tavily:
            return await self._tavily_search(query, max_results)
        elif settings.SERPER_API_KEY:
            return await self._serper_search(query, max_results)
        else:
            logger.warning("web_search.no_api_key_configured")
            return []

    async def _tavily_search(
        self, query: str, max_results: int = 5
    ) -> List[Dict[str, Any]]:
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=settings.TAVILY_API_KEY)
            response = client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                include_answer=True,
            )
            results = []
            for r in response.get("results", []):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),
                    "score": r.get("score", 0.0),
                    "source": "tavily",
                })
            logger.info("web_search.tavily.done", query=query, results=len(results))
            return results
        except Exception as e:
            logger.error("web_search.tavily.failed", error=str(e))
            return []

    async def _serper_search(
        self, query: str, max_results: int = 5
    ) -> List[Dict[str, Any]]:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://google.serper.dev/search",
                    headers={"X-API-KEY": settings.SERPER_API_KEY, "Content-Type": "application/json"},
                    json={"q": query, "num": max_results},
                    timeout=10,
                )
                data = response.json()
                results = []
                for r in data.get("organic", []):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("link", ""),
                        "content": r.get("snippet", ""),
                        "score": 0.7,
                        "source": "serper",
                    })
                logger.info("web_search.serper.done", query=query, results=len(results))
                return results
        except Exception as e:
            logger.error("web_search.serper.failed", error=str(e))
            return []


web_search = WebSearchService()
