import logging
import math
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.research_cache import ResearchCache
from app.db.models.market_cache import MarketCache
from app.db.models.position import Position
from app.db.models.strategy import Strategy

logger = logging.getLogger(__name__)

PRICE_FLOOR = 0.10
PRICE_CEILING = 0.90
FETCH_LIMIT = 50
RETURN_LIMIT = 20

WEIGHT_EDGE = 0.30
WEIGHT_LIQUIDITY = 0.25
WEIGHT_VOLUME = 0.20
WEIGHT_CATEGORY = 0.15
WEIGHT_FRESHNESS = 0.10

LOG_LIQUIDITY_CAP = math.log1p(100_000)
LOG_VOLUME_CAP = math.log1p(1_000_000)


class MarketScanner:
    def __init__(self, db: AsyncSession, user_id: uuid.UUID, research_cache: ResearchCache):
        self.db = db
        self.user_id = user_id
        self.research_cache = research_cache

    async def scan(self) -> list[MarketCache]:
        strategy = await self._get_active_strategy()
        now = datetime.now(timezone.utc)

        query = select(MarketCache).where(
            MarketCache.is_active == True,
            MarketCache.resolved == False,
            MarketCache.yes_price >= PRICE_FLOOR,
            MarketCache.yes_price <= PRICE_CEILING,
        )

        category_weights: dict[str, float] = {}

        if strategy and strategy.rules:
            filters = strategy.rules.get("market_filters", {})

            categories = strategy.rules.get("categories") or filters.get("categories")
            if categories:
                query = query.where(MarketCache.category.in_(categories))

            odds_range = filters.get("odds_range") or strategy.rules.get("preferred_odds_range")
            if isinstance(odds_range, dict):
                lo = max(PRICE_FLOOR, odds_range.get("min", PRICE_FLOOR))
                hi = min(PRICE_CEILING, odds_range.get("max", PRICE_CEILING))
                query = query.where(MarketCache.yes_price >= lo, MarketCache.yes_price <= hi)
            elif isinstance(odds_range, list) and len(odds_range) == 2:
                lo = max(PRICE_FLOOR, odds_range[0])
                hi = min(PRICE_CEILING, odds_range[1])
                query = query.where(MarketCache.yes_price >= lo, MarketCache.yes_price <= hi)

            min_volume = filters.get("min_volume")
            if min_volume:
                query = query.where(MarketCache.volume >= min_volume)

            category_weights = strategy.rules.get("category_weights", {})

        query = query.limit(FETCH_LIMIT)
        result = await self.db.execute(query)
        markets = list(result.scalars().all())

        held_ids = await self._get_held_market_ids()

        scored: list[tuple[float, MarketCache]] = []
        skipped_held = 0
        skipped_cooldown = 0
        for m in markets:
            mid = m.condition_id
            if mid in held_ids:
                skipped_held += 1
                continue
            if self.research_cache.is_on_trade_cooldown(mid, now):
                skipped_cooldown += 1
                continue

            yes_price = float(m.yes_price) if m.yes_price else 0.5
            edge_potential = abs(yes_price - 0.5) / 0.4
            edge_potential = min(1.0, edge_potential)

            liq = float(m.liquidity or 0)
            liquidity_score = min(1.0, math.log1p(liq) / LOG_LIQUIDITY_CAP) if liq > 0 else 0.0

            vol = float(m.volume or 0)
            volume_score = min(1.0, math.log1p(vol) / LOG_VOLUME_CAP) if vol > 0 else 0.0

            cat = m.category or ""
            cat_weight = category_weights.get(cat, 0.5)

            freshness = self.research_cache.get_freshness_score(mid, now)

            score = (
                WEIGHT_EDGE * edge_potential
                + WEIGHT_LIQUIDITY * liquidity_score
                + WEIGHT_VOLUME * volume_score
                + WEIGHT_CATEGORY * cat_weight
                + WEIGHT_FRESHNESS * freshness
            )
            scored.append((score, m))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = [m for _, m in scored[:RETURN_LIMIT]]

        for m in top:
            self.research_cache.record_scan(m.condition_id)

        logger.info(
            f"Scanner: {len(markets)} fetched, {skipped_held} held, "
            f"{skipped_cooldown} on cooldown, {len(scored)} scored, returning {len(top)}"
        )
        return top

    async def _get_held_market_ids(self) -> set[str]:
        result = await self.db.execute(
            select(Position.market_id).where(
                Position.user_id == self.user_id,
                Position.status == "open",
            )
        )
        return set(result.scalars().all())

    async def _get_active_strategy(self) -> Strategy | None:
        result = await self.db.execute(
            select(Strategy).where(
                Strategy.user_id == self.user_id, Strategy.is_active == True
            ).order_by(Strategy.priority.desc())
        )
        return result.scalars().first()
