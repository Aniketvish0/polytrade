import logging
import time
from collections import OrderedDict
from datetime import datetime, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models.news_item import NewsItem

logger = logging.getLogger(__name__)

_NEWS_CACHE: OrderedDict[str, tuple[float, list[dict]]] = OrderedDict()
_CACHE_TTL = 300  # 5 minutes
_CACHE_MAX = 100


def _cache_get(key: str) -> list[dict] | None:
    if key in _NEWS_CACHE:
        ts, items = _NEWS_CACHE[key]
        if time.monotonic() - ts < _CACHE_TTL:
            _NEWS_CACHE.move_to_end(key)
            return items
        del _NEWS_CACHE[key]
    return None


def _cache_set(key: str, items: list[dict]):
    _NEWS_CACHE[key] = (time.monotonic(), items)
    while len(_NEWS_CACHE) > _CACHE_MAX:
        _NEWS_CACHE.popitem(last=False)


class NewsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(self, query: str, category: str, market_id: str) -> list[dict]:
        cache_key = f"{market_id}:{category}"
        cached = _cache_get(cache_key)
        if cached is not None:
            logger.debug(f"News cache hit for {cache_key}")
            return cached
        import asyncio

        results = await asyncio.gather(
            self._search_tavily(query),
            self._search_newsapi(query),
            return_exceptions=True,
        )

        all_items = []
        for result in results:
            if isinstance(result, list):
                all_items.extend(result)

        seen_urls = set()
        unique = []
        for item in all_items:
            url = item.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique.append(item)
            elif not url:
                unique.append(item)

        scored = await self._score_items(unique, query, category)

        for item in scored:
            news = NewsItem(
                source=item.get("source", "unknown"),
                title=item.get("title", ""),
                url=item.get("url"),
                summary=item.get("summary"),
                market_ids=[market_id],
                categories=[category],
                relevance_score=item.get("relevance_score"),
                credibility_score=item.get("credibility_score"),
                sentiment_score=item.get("sentiment_score"),
            )
            self.db.add(news)

        _cache_set(cache_key, scored)
        return scored

    async def _search_tavily(self, query: str) -> list[dict]:
        if not settings.TAVILY_API_KEY:
            return []
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": settings.TAVILY_API_KEY,
                        "query": query,
                        "search_depth": "advanced",
                        "max_results": 5,
                    },
                )
                response.raise_for_status()
                data = response.json()

            return [
                {
                    "source": "tavily",
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "summary": r.get("content", "")[:500],
                }
                for r in data.get("results", [])
            ]
        except Exception as e:
            logger.warning(f"Tavily search failed: {e}")
            return []

    async def _search_newsapi(self, query: str) -> list[dict]:
        if not settings.NEWSAPI_KEY:
            return []
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(
                    "https://newsapi.org/v2/everything",
                    params={
                        "q": query,
                        "sortBy": "relevancy",
                        "pageSize": 5,
                        "apiKey": settings.NEWSAPI_KEY,
                    },
                )
                response.raise_for_status()
                data = response.json()

            return [
                {
                    "source": article.get("source", {}).get("name", "newsapi"),
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "summary": article.get("description", "")[:500],
                }
                for article in data.get("articles", [])
            ]
        except Exception as e:
            logger.warning(f"NewsAPI search failed: {e}")
            return []

    async def _score_items(self, items: list[dict], query: str, category: str) -> list[dict]:
        if not items:
            return []

        try:
            from app.llm.base import LLMMessage
            from app.llm.prompts.market_analysis import NEWS_SCORING_SYSTEM
            from app.llm.registry import LLMRegistry
            from app.llm.tools import SCORE_NEWS_TOOL

            articles_text = "\n".join(
                f"{i}. [{item.get('source')}] {item.get('title')}: {item.get('summary', '')[:200]}"
                for i, item in enumerate(items)
            )

            llm = LLMRegistry.get()
            response = await llm.complete(
                messages=[
                    LLMMessage(
                        role="user",
                        content=f"Market question: {query}\nCategory: {category}\n\nArticles:\n{articles_text}",
                    )
                ],
                tools=[SCORE_NEWS_TOOL],
                system_prompt=NEWS_SCORING_SYSTEM,
                temperature=0.1,
            )

            if response.tool_calls:
                scores = response.tool_calls[0].arguments.get("scores", [])
                for score in scores:
                    idx = score.get("index", 0)
                    if 0 <= idx < len(items):
                        items[idx]["relevance_score"] = score.get("relevance_score", 0.5)
                        items[idx]["credibility_score"] = score.get("credibility_score", 0.5)
                        items[idx]["sentiment_score"] = score.get("sentiment_score", 0)

        except Exception as e:
            logger.warning(f"News scoring failed: {e}")
            for item in items:
                item.setdefault("relevance_score", 0.5)
                item.setdefault("credibility_score", 0.5)
                item.setdefault("sentiment_score", 0)

        return sorted(items, key=lambda x: x.get("relevance_score", 0), reverse=True)
