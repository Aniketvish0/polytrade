from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.models.policy import Policy
from app.db.models.portfolio import Portfolio
from app.db.models.position import Position
from app.db.models.trade import Trade
from app.db.models.user import User
from app.dependencies import get_current_user
from app.schemas.portfolio import PortfolioResponse, PositionResponse

router = APIRouter()


@router.get("", response_model=PortfolioResponse)
async def get_portfolio(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Portfolio).where(Portfolio.user_id == user.id))
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    open_pos = await db.execute(
        select(func.count()).select_from(Position).where(
            Position.user_id == user.id, Position.status == "open"
        )
    )
    open_count = open_pos.scalar() or 0

    today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)
    today_trades_q = await db.execute(
        select(func.count(), func.coalesce(func.sum(Trade.total_amount), 0)).select_from(Trade).where(
            Trade.user_id == user.id, Trade.executed_at >= today_start
        )
    )
    today_row = today_trades_q.one()
    today_trades_count = today_row[0] or 0
    daily_spend = today_row[1] or Decimal("0")

    policy_result = await db.execute(
        select(Policy).where(Policy.user_id == user.id, Policy.is_active == True)
    )
    active_policy = policy_result.scalar_one_or_none()
    daily_limit = Decimal("200")
    if active_policy and active_policy.global_rules:
        daily_limit = Decimal(str(active_policy.global_rules.get("max_daily_spend", 200)))

    win_rate = 0.0
    if portfolio.total_trades > 0:
        win_rate = portfolio.winning_trades / portfolio.total_trades

    return PortfolioResponse(
        id=portfolio.id,
        balance=portfolio.balance,
        total_deposited=portfolio.total_deposited,
        total_pnl=portfolio.total_pnl,
        total_trades=portfolio.total_trades,
        winning_trades=portfolio.winning_trades,
        losing_trades=portfolio.losing_trades,
        win_rate=win_rate,
        open_positions=open_count,
        today_pnl=Decimal("0"),
        today_trades=today_trades_count,
        daily_spend_used=daily_spend,
        daily_spend_limit=daily_limit,
    )


@router.get("/positions", response_model=list[PositionResponse])
async def list_positions(
    status: str = "open",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Position).where(Position.user_id == user.id, Position.status == status)
    )
    return result.scalars().all()
