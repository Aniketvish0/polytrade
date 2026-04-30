import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.position import Position

logger = logging.getLogger(__name__)


def kelly_size(
    estimated_prob: float,
    market_price: float,
    portfolio_balance: float,
    kelly_fraction: float = 0.25,
    max_portfolio_pct: float = 0.15,
) -> float:
    if market_price <= 0.01 or market_price >= 0.99:
        return 0.0
    if estimated_prob <= 0.01 or estimated_prob >= 0.99:
        return 0.0
    if portfolio_balance <= 0:
        return 0.0

    b = (1 - market_price) / market_price
    p = estimated_prob
    q = 1 - p

    f_star = (b * p - q) / b
    if f_star <= 0:
        return 0.0

    bet = kelly_fraction * f_star * portfolio_balance
    max_bet = max_portfolio_pct * portfolio_balance
    return min(bet, max_bet)


def shares_from_kelly(
    estimated_prob: float,
    market_price: float,
    portfolio_balance: float,
    kelly_fraction: float = 0.25,
    max_portfolio_pct: float = 0.15,
    min_shares: int = 1,
) -> int:
    bet = kelly_size(estimated_prob, market_price, portfolio_balance, kelly_fraction, max_portfolio_pct)
    if bet <= 0 or market_price <= 0:
        return 0
    shares = int(bet / market_price)
    return max(min_shares, shares) if shares > 0 else 0


async def check_category_exposure(
    db: AsyncSession,
    user_id: uuid.UUID,
    category: str,
    proposed_amount: float,
    portfolio_balance: float,
    max_category_pct: float = 0.80,
) -> bool:
    result = await db.execute(
        select(func.coalesce(func.sum(Position.cost_basis), 0)).where(
            Position.user_id == user_id,
            Position.market_category == category,
            Position.status == "open",
        )
    )
    current_exposure = float(result.scalar() or 0)
    max_allowed = max_category_pct * portfolio_balance
    return (current_exposure + proposed_amount) <= max_allowed
