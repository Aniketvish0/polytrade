import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.market_cache import MarketCache
from app.db.models.portfolio import Portfolio
from app.db.models.position import Position
from app.db.models.trade import Trade


class SimulatedTradingEngine:
    SLIPPAGE_BPS = 50

    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute_buy(
        self,
        user_id: uuid.UUID,
        market: MarketCache,
        side: str,
        shares: Decimal,
        price: Decimal,
        decision: dict,
        enforcement_result: str,
        policy_id: uuid.UUID | None = None,
        armoriq_plan_hash: str | None = None,
        armoriq_intent_token_id: str | None = None,
    ) -> Trade:
        execution_price = price * (1 + Decimal(self.SLIPPAGE_BPS) / 10000)
        total_cost = (shares * execution_price).quantize(Decimal("0.01"))

        portfolio = await self._get_portfolio(user_id)
        if portfolio.balance < total_cost:
            shares = (portfolio.balance / execution_price).quantize(Decimal("0.0001"))
            total_cost = (shares * execution_price).quantize(Decimal("0.01"))

        portfolio.balance -= total_cost
        portfolio.total_trades += 1

        token_id = market.yes_token_id if side == "YES" else market.no_token_id

        existing_pos = await self.db.execute(
            select(Position).where(
                Position.user_id == user_id,
                Position.market_id == market.condition_id,
                Position.side == side,
                Position.status == "open",
            )
        )
        position = existing_pos.scalar_one_or_none()

        if position:
            total_shares = position.shares + shares
            position.avg_price = (
                (position.avg_price * position.shares + execution_price * shares) / total_shares
            ).quantize(Decimal("0.000001"))
            position.shares = total_shares
            position.cost_basis += total_cost
        else:
            position = Position(
                user_id=user_id,
                portfolio_id=portfolio.id,
                market_id=market.condition_id,
                market_slug=market.slug,
                market_question=market.question,
                market_category=market.category,
                token_id=token_id or "",
                side=side,
                shares=shares,
                avg_price=execution_price,
                cost_basis=total_cost,
                current_price=price,
                current_value=shares * price,
                unrealized_pnl=Decimal("0"),
                opened_at=datetime.now(timezone.utc),
            )
            self.db.add(position)

        await self.db.flush()

        trade = Trade(
            user_id=user_id,
            position_id=position.id,
            market_id=market.condition_id,
            market_question=market.question,
            market_category=market.category,
            action="buy",
            side=side,
            shares=shares,
            price=execution_price,
            total_amount=total_cost,
            confidence_score=Decimal(str(decision.get("confidence", 0))),
            edge=Decimal(str(decision.get("edge", 0))),
            sources_count=decision.get("sources_count"),
            reasoning=decision.get("reasoning"),
            enforcement_result=enforcement_result,
            policy_id=policy_id,
            armoriq_plan_hash=armoriq_plan_hash,
            armoriq_intent_token_id=armoriq_intent_token_id,
        )
        self.db.add(trade)
        await self.db.flush()

        return trade

    async def execute_sell(
        self,
        user_id: uuid.UUID,
        position_id: uuid.UUID,
        shares: Decimal,
        current_price: Decimal,
    ) -> Trade:
        result = await self.db.execute(
            select(Position).where(Position.id == position_id, Position.user_id == user_id)
        )
        position = result.scalar_one()

        execution_price = current_price * (1 - Decimal(self.SLIPPAGE_BPS) / 10000)
        proceeds = (shares * execution_price).quantize(Decimal("0.01"))
        realized_pnl = ((execution_price - position.avg_price) * shares).quantize(Decimal("0.01"))

        portfolio = await self._get_portfolio(user_id)
        portfolio.balance += proceeds
        portfolio.total_trades += 1
        portfolio.total_pnl += realized_pnl
        if realized_pnl > 0:
            portfolio.winning_trades += 1
        else:
            portfolio.losing_trades += 1

        position.shares -= shares
        if position.shares <= 0:
            position.status = "closed"
            position.closed_at = datetime.now(timezone.utc)
            position.realized_pnl = realized_pnl

        trade = Trade(
            user_id=user_id,
            position_id=position_id,
            market_id=position.market_id,
            market_question=position.market_question,
            market_category=position.market_category,
            action="sell",
            side=position.side,
            shares=shares,
            price=execution_price,
            total_amount=proceeds,
            enforcement_result="auto_approved",
        )
        self.db.add(trade)
        await self.db.flush()

        return trade

    async def refresh_positions(self, user_id: uuid.UUID):
        result = await self.db.execute(
            select(Position).where(Position.user_id == user_id, Position.status == "open")
        )
        positions = result.scalars().all()

        for pos in positions:
            market_result = await self.db.execute(
                select(MarketCache).where(MarketCache.condition_id == pos.market_id)
            )
            market = market_result.scalar_one_or_none()
            if market:
                current = market.yes_price if pos.side == "YES" else market.no_price
                if current:
                    pos.current_price = current
                    pos.current_value = (pos.shares * current).quantize(Decimal("0.01"))
                    pos.unrealized_pnl = (
                        (current - pos.avg_price) * pos.shares
                    ).quantize(Decimal("0.01"))

    async def _get_portfolio(self, user_id: uuid.UUID) -> Portfolio:
        result = await self.db.execute(
            select(Portfolio).where(Portfolio.user_id == user_id)
        )
        return result.scalar_one()
