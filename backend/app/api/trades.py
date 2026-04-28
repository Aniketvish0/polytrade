import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.models.trade import Trade
from app.db.models.user import User
from app.dependencies import get_current_user
from app.schemas.trade import TradeResponse

router = APIRouter()


@router.get("", response_model=list[TradeResponse])
async def list_trades(
    limit: int = Query(50, le=200),
    offset: int = 0,
    category: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Trade).where(Trade.user_id == user.id)
    if category:
        query = query.where(Trade.market_category == category)
    query = query.order_by(desc(Trade.executed_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(
    trade_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Trade).where(Trade.id == trade_id, Trade.user_id == user.id)
    )
    trade = result.scalar_one_or_none()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade
