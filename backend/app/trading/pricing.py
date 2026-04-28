from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.market_cache import MarketCache


class PricingService:
    SLIPPAGE_BPS = 50

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_live_odds(self, market_id: str) -> dict:
        result = await self.db.execute(
            select(MarketCache).where(MarketCache.condition_id == market_id)
        )
        market = result.scalar_one_or_none()
        if not market:
            return {"yes_price": 0.5, "no_price": 0.5}
        return {
            "yes_price": float(market.yes_price) if market.yes_price else 0.5,
            "no_price": float(market.no_price) if market.no_price else 0.5,
        }

    async def get_execution_price(
        self, market_id: str, side: str, action: str
    ) -> Decimal:
        odds = await self.get_live_odds(market_id)
        base_price = Decimal(str(odds["yes_price"] if side == "YES" else odds["no_price"]))

        if action == "buy":
            return base_price * (1 + Decimal(self.SLIPPAGE_BPS) / 10000)
        else:
            return base_price * (1 - Decimal(self.SLIPPAGE_BPS) / 10000)
