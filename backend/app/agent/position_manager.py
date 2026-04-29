import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.market_cache import MarketCache
from app.db.models.position import Position
from app.trading.engine import SimulatedTradingEngine

logger = logging.getLogger(__name__)

TAKE_PROFIT_THRESHOLD = Decimal("0.92")
STOP_LOSS_PCT = Decimal("0.25")
EXPIRY_HOURS = 24


class PositionManager:
    def __init__(self, db: AsyncSession, user_id: uuid.UUID):
        self.db = db
        self.user_id = user_id
        self.engine = SimulatedTradingEngine(db)

    async def evaluate_positions(self) -> list[dict]:
        result = await self.db.execute(
            select(Position).where(
                Position.user_id == self.user_id,
                Position.status == "open",
            )
        )
        positions = result.scalars().all()
        exits = []

        for pos in positions:
            market_result = await self.db.execute(
                select(MarketCache).where(MarketCache.condition_id == pos.market_id)
            )
            market = market_result.scalar_one_or_none()
            if not market:
                continue

            current_price = market.yes_price if pos.side == "YES" else market.no_price
            if not current_price:
                continue

            pos.current_price = current_price
            pos.current_value = (pos.shares * current_price).quantize(Decimal("0.01"))
            pos.unrealized_pnl = ((current_price - pos.avg_price) * pos.shares).quantize(Decimal("0.01"))

            exit_reason = self._should_exit(pos, market, current_price)
            if exit_reason:
                try:
                    trade = await self.engine.execute_sell(
                        user_id=self.user_id,
                        position_id=pos.id,
                        shares=pos.shares,
                        current_price=current_price,
                    )
                    exits.append({
                        "trade": trade,
                        "position": pos,
                        "reason": exit_reason,
                    })
                    logger.info(f"Exited position {pos.id}: {exit_reason}")
                except Exception as e:
                    logger.warning(f"Failed to exit position {pos.id}: {e}")

        return exits

    def _should_exit(self, pos: Position, market: MarketCache, current_price: Decimal) -> str | None:
        if current_price >= TAKE_PROFIT_THRESHOLD:
            return f"take_profit: price {current_price:.2f} >= {TAKE_PROFIT_THRESHOLD}"

        loss_pct = (pos.avg_price - current_price) / pos.avg_price if pos.avg_price > 0 else Decimal("0")
        if loss_pct >= STOP_LOSS_PCT:
            return f"stop_loss: down {loss_pct:.0%} from entry {pos.avg_price:.2f}"

        if market.end_date:
            now = datetime.now(timezone.utc)
            hours_left = (market.end_date - now).total_seconds() / 3600
            if hours_left < EXPIRY_HOURS and pos.unrealized_pnl and pos.unrealized_pnl > 0:
                return f"time_decay: {hours_left:.0f}h to expiry, locking profit"

        return None
