import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.market_cache import MarketCache
from app.services.news_service import NewsService

logger = logging.getLogger(__name__)


class MarketResearcher:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.news_service = NewsService(db=db)

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
