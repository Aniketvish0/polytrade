import math
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.models.market_cache import MarketCache
from app.db.models.position import Position
from app.db.models.user import User
from app.dependencies import get_current_user
from app.schemas.market import EnhancedMarketResponse, MarketResponse

router = APIRouter()

LOG_LIQUIDITY_CAP = math.log1p(100_000)
LOG_VOLUME_CAP = math.log1p(1_000_000)


@router.get("", response_model=list[MarketResponse])
async def list_markets(
    category: str | None = None,
    search: str | None = None,
    active_only: bool = True,
    limit: int = Query(50, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(MarketCache)
    if active_only:
        query = query.where(MarketCache.is_active == True, MarketCache.resolved == False)
    if category:
        query = query.where(MarketCache.category == category)
    if search:
        query = query.where(MarketCache.question.ilike(f"%{search}%"))
    query = query.order_by(desc(MarketCache.volume)).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/enhanced", response_model=list[EnhancedMarketResponse])
async def list_enhanced_markets(
    category: str | None = None,
    sort_by: str = Query("score", pattern="^(score|volume|edge|liquidity)$"),
    limit: int = Query(50, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.agent.research_cache import get_cache

    query = select(MarketCache).where(
        MarketCache.is_active == True,
        MarketCache.resolved == False,
    )
    if category:
        query = query.where(MarketCache.category == category)
    query = query.order_by(desc(MarketCache.volume)).limit(200)
    result = await db.execute(query)
    markets = result.scalars().all()

    pos_result = await db.execute(
        select(Position.market_id, Position.side).where(
            Position.user_id == user.id,
            Position.status == "open",
        )
    )
    positions = {row.market_id: row.side for row in pos_result}

    cache = get_cache(str(user.id))
    now = datetime.now(timezone.utc)

    enhanced = []
    for m in markets:
        yes_price = float(m.yes_price) if m.yes_price else 0.5
        no_price = float(m.no_price) if m.no_price else 0.5

        edge_potential = min(1.0, abs(yes_price - 0.5) / 0.4)
        liq = float(m.liquidity or 0)
        liquidity_score = min(1.0, math.log1p(liq) / LOG_LIQUIDITY_CAP) if liq > 0 else 0.0
        vol = float(m.volume or 0)
        volume_score = min(1.0, math.log1p(vol) / LOG_VOLUME_CAP) if vol > 0 else 0.0

        composite = 0.35 * edge_potential + 0.35 * liquidity_score + 0.30 * volume_score

        entry = cache.get(m.condition_id)
        research_status = None
        last_researched = None
        if entry and entry.last_researched_at:
            elapsed = (now - entry.last_researched_at).total_seconds()
            research_status = "researched" if elapsed < 300 else "stale"
            last_researched = entry.last_researched_at

        spread = abs(yes_price + no_price - 1.0)

        hours_to_resolution = None
        if m.end_date:
            delta = (m.end_date - now).total_seconds() / 3600
            hours_to_resolution = max(0, delta)

        mid = m.condition_id
        enhanced.append(EnhancedMarketResponse(
            id=m.id,
            condition_id=mid,
            question=m.question,
            description=m.description,
            category=m.category,
            slug=m.slug,
            yes_price=m.yes_price,
            no_price=m.no_price,
            volume=m.volume,
            liquidity=m.liquidity,
            end_date=m.end_date,
            is_active=m.is_active,
            resolved=m.resolved,
            last_fetched_at=m.last_fetched_at,
            edge_potential=round(edge_potential, 3),
            liquidity_score=round(liquidity_score, 3),
            composite_score=round(composite, 3),
            research_status=research_status,
            last_researched_at=last_researched,
            user_has_position=mid in positions,
            position_side=positions.get(mid),
            spread=round(spread, 4),
            hours_to_resolution=round(hours_to_resolution, 1) if hours_to_resolution is not None else None,
        ))

    sort_keys = {
        "score": lambda x: x.composite_score or 0,
        "volume": lambda x: float(x.volume or 0),
        "edge": lambda x: x.edge_potential or 0,
        "liquidity": lambda x: x.liquidity_score or 0,
    }
    enhanced.sort(key=sort_keys.get(sort_by, sort_keys["score"]), reverse=True)

    return enhanced[:limit]
