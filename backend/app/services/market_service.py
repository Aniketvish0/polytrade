import json as _json
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select

from app.config import settings
from app.db.engine import async_session
from app.db.models.market_cache import MarketCache

logger = logging.getLogger(__name__)

CATEGORY_KEYWORDS = {
    "politics": ["election", "president", "congress", "senate", "vote", "democrat", "republican", "political", "trump", "biden"],
    "economics": ["fed", "inflation", "gdp", "interest rate", "unemployment", "recession", "cpi", "treasury", "economic"],
    "crypto": ["bitcoin", "ethereum", "crypto", "btc", "eth", "blockchain", "token"],
    "sports": ["nba", "nfl", "mlb", "soccer", "football", "basketball", "world cup", "championship", "playoff"],
    "entertainment": ["oscar", "grammy", "movie", "film", "celebrity", "tv show", "award"],
    "science_tech": ["ai", "climate", "spacex", "nasa", "tech", "science", "research", "fda"],
}


def categorize_market(question: str) -> str:
    q_lower = question.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in q_lower for kw in keywords):
            return category
    return "general"


class MarketService:
    async def fetch_and_cache_markets(self):
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{settings.POLYMARKET_GAMMA_URL}/markets",
                    params={"limit": 100, "active": True, "closed": False},
                )
                response.raise_for_status()
                markets = response.json()

            async with async_session() as db:
                for market_data in markets:
                    condition_id = (
                        market_data.get("conditionId")
                        or market_data.get("condition_id")
                        or market_data.get("id", "")
                    )
                    if not condition_id:
                        continue

                    question = market_data.get("question", "")
                    category = categorize_market(question)

                    yes_price, no_price = self._parse_prices(market_data)
                    token_ids = self._parse_token_ids(market_data)
                    end_date = self._parse_end_date(market_data)

                    existing = await db.execute(
                        select(MarketCache).where(MarketCache.condition_id == condition_id)
                    )
                    cached = existing.scalar_one_or_none()

                    if cached:
                        cached.question = question
                        cached.category = category
                        cached.yes_price = yes_price
                        cached.no_price = no_price
                        cached.yes_token_id = token_ids[0]
                        cached.no_token_id = token_ids[1]
                        cached.volume = market_data.get("volume")
                        cached.liquidity = market_data.get("liquidity")
                        cached.slug = market_data.get("slug")
                        cached.description = market_data.get("description")
                        if end_date:
                            cached.end_date = end_date
                        cached.is_active = market_data.get("active", True)
                        cached.resolved = market_data.get("closed", False)
                        cached.raw_data = market_data
                        cached.last_fetched_at = datetime.now(timezone.utc)
                    else:
                        new_market = MarketCache(
                            condition_id=condition_id,
                            question=question,
                            description=market_data.get("description"),
                            category=category,
                            slug=market_data.get("slug"),
                            yes_token_id=token_ids[0],
                            no_token_id=token_ids[1],
                            yes_price=yes_price,
                            no_price=no_price,
                            volume=market_data.get("volume"),
                            liquidity=market_data.get("liquidity"),
                            end_date=end_date,
                            is_active=market_data.get("active", True),
                            resolved=market_data.get("closed", False),
                            raw_data=market_data,
                        )
                        db.add(new_market)

                await db.commit()
                logger.info(f"Cached {len(markets)} markets from Polymarket")

        except Exception as e:
            logger.error(f"Failed to fetch markets: {e}", exc_info=True)

    @staticmethod
    def _parse_prices(data: dict) -> tuple[float | None, float | None]:
        raw = data.get("outcomePrices")
        if not raw:
            return None, None
        if isinstance(raw, str):
            raw = _json.loads(raw)
        if isinstance(raw, list) and len(raw) >= 2:
            return float(raw[0]), float(raw[1])
        return None, None

    @staticmethod
    def _parse_token_ids(data: dict) -> tuple[str | None, str | None]:
        raw = data.get("clobTokenIds")
        if not raw:
            return None, None
        if isinstance(raw, str):
            raw = _json.loads(raw)
        if isinstance(raw, list) and len(raw) >= 2:
            return raw[0], raw[1]
        return None, None

    @staticmethod
    def _parse_end_date(data: dict) -> datetime | None:
        for key in ("endDate", "end_date_iso"):
            val = data.get(key)
            if val:
                try:
                    return datetime.fromisoformat(val.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    continue
        return None
