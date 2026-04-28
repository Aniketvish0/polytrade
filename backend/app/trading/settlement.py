from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.portfolio import Portfolio
from app.db.models.position import Position


async def settle_market(db: AsyncSession, market_id: str, outcome: bool):
    result = await db.execute(
        select(Position).where(
            Position.market_id == market_id, Position.status == "open"
        )
    )
    positions = result.scalars().all()

    for pos in positions:
        if pos.side == "YES":
            settlement_value = pos.shares if outcome else Decimal("0")
        else:
            settlement_value = pos.shares if not outcome else Decimal("0")

        realized_pnl = (settlement_value - pos.cost_basis).quantize(Decimal("0.01"))

        portfolio_result = await db.execute(
            select(Portfolio).where(Portfolio.user_id == pos.user_id)
        )
        portfolio = portfolio_result.scalar_one()
        portfolio.balance += settlement_value
        portfolio.total_pnl += realized_pnl
        if realized_pnl > 0:
            portfolio.winning_trades += 1
        else:
            portfolio.losing_trades += 1

        pos.status = "resolved"
        pos.resolved_outcome = outcome
        pos.realized_pnl = realized_pnl
        pos.current_value = settlement_value
