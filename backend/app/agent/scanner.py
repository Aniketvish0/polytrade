import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.market_cache import MarketCache
from app.db.models.strategy import Strategy


class MarketScanner:
    def __init__(self, db: AsyncSession, user_id: uuid.UUID):
        self.db = db
        self.user_id = user_id

    async def scan(self) -> list[MarketCache]:
        strategy = await self._get_active_strategy()
        query = select(MarketCache).where(
            MarketCache.is_active == True,
            MarketCache.resolved == False,
        )

        if strategy and strategy.rules:
            filters = strategy.rules.get("market_filters", {})

            categories = filters.get("categories")
            if categories:
                query = query.where(MarketCache.category.in_(categories))

            odds_range = filters.get("odds_range", [0.08, 0.92])
            if odds_range and len(odds_range) == 2:
                query = query.where(
                    MarketCache.yes_price >= odds_range[0],
                    MarketCache.yes_price <= odds_range[1],
                )

            min_volume = filters.get("min_volume")
            if min_volume:
                query = query.where(MarketCache.volume >= min_volume)

        query = query.order_by(MarketCache.volume.desc()).limit(10)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _get_active_strategy(self) -> Strategy | None:
        result = await self.db.execute(
            select(Strategy).where(
                Strategy.user_id == self.user_id, Strategy.is_active == True
            ).order_by(Strategy.priority.desc())
        )
        return result.scalar_one_or_none()
