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

        category_weights: dict[str, float] = {}

        if strategy and strategy.rules:
            filters = strategy.rules.get("market_filters", {})

            categories = strategy.rules.get("categories") or filters.get("categories")
            if categories:
                query = query.where(MarketCache.category.in_(categories))

            odds_range = filters.get("odds_range") or strategy.rules.get("preferred_odds_range")
            if isinstance(odds_range, dict):
                odds_range = [odds_range.get("min", 0.08), odds_range.get("max", 0.92)]
            elif isinstance(odds_range, list) and len(odds_range) == 2:
                pass
            else:
                odds_range = [0.08, 0.92]

            query = query.where(
                MarketCache.yes_price >= odds_range[0],
                MarketCache.yes_price <= odds_range[1],
            )

            min_volume = filters.get("min_volume")
            if min_volume:
                query = query.where(MarketCache.volume >= min_volume)

            category_weights = strategy.rules.get("category_weights", {})

        query = query.order_by(MarketCache.volume.desc()).limit(20)
        result = await self.db.execute(query)
        markets = list(result.scalars().all())

        if category_weights:
            markets.sort(
                key=lambda m: category_weights.get(m.category or "", 0.5),
                reverse=True,
            )

        return markets[:10]

    async def _get_active_strategy(self) -> Strategy | None:
        result = await self.db.execute(
            select(Strategy).where(
                Strategy.user_id == self.user_id, Strategy.is_active == True
            ).order_by(Strategy.priority.desc())
        )
        return result.scalars().first()
