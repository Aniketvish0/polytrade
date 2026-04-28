from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.models.market_cache import MarketCache
from app.db.models.user import User
from app.dependencies import get_current_user
from app.schemas.market import MarketResponse

router = APIRouter()


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
