import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.research_cache import ResearchCache
from app.db.models.market_cache import MarketCache
from app.services.news_service import NewsService

logger = logging.getLogger(__name__)


class MarketResearcher:
    def __init__(self, db: AsyncSession, research_cache: ResearchCache):
        self.db = db
        self.news_service = NewsService(db=db)
        self.research_cache = research_cache

    async def research_with_cache(self, market: MarketCache) -> dict:
        current_price = float(market.yes_price) if market.yes_price else 0.5
        mid = market.condition_id
        now = datetime.now(timezone.utc)

        if not self.research_cache.should_research(mid, current_price, now):
            entry = self.research_cache.get(mid)
            if entry and entry.research_result:
                logger.debug(f"Research cache hit for {mid}")
                return entry.research_result

        result = await self.research(market)
        self.research_cache.record_research(mid, result, current_price)
        return result

    async def research(self, market: MarketCache) -> dict:
        try:
            news_items = await self.news_service.search(
                query=market.question,
                category=market.category or "general",
                market_id=market.condition_id,
            )

            return {
                "market_id": market.condition_id,
                "market_question": market.question,
                "category": market.category,
                "current_yes_price": float(market.yes_price) if market.yes_price else 0.5,
                "current_no_price": float(market.no_price) if market.no_price else 0.5,
                "news_items": news_items,
                "sources_count": len(news_items),
            }
        except Exception as e:
            logger.warning(f"Research failed for {market.condition_id}: {e}")
            return {
                "market_id": market.condition_id,
                "market_question": market.question,
                "category": market.category,
                "current_yes_price": float(market.yes_price) if market.yes_price else 0.5,
                "current_no_price": float(market.no_price) if market.no_price else 0.5,
                "news_items": [],
                "sources_count": 0,
            }
