import logging
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.armoriq.enforcement import ArmorIQEnforcer
from app.db.models.market_cache import MarketCache
from app.db.models.policy import Policy
from app.trading.engine import SimulatedTradingEngine
from app.ws.events import trade_denied_event, trade_executed_event, trade_held_event
from app.ws.manager import ConnectionManager

logger = logging.getLogger(__name__)


class TradeExecutor:
    def __init__(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        user_email: str,
        ws_manager: ConnectionManager,
    ):
        self.db = db
        self.user_id = user_id
        self.user_email = user_email
        self.ws_manager = ws_manager
        self.trading_engine = SimulatedTradingEngine(db=db)
        self.enforcer = ArmorIQEnforcer()

    async def execute(self, market: MarketCache, decision: dict, research: dict):
        action_str = decision.get("action", "pass")
        if action_str == "pass":
            return

        side = "YES" if action_str == "buy_yes" else "NO"
        price = float(market.yes_price) if side == "YES" else float(market.no_price)
        shares = decision.get("suggested_shares", 10)
        total = round(shares * price, 2)
        category = market.category or "_default"

        policy = await self._get_active_policy()
        enforcement = await self.enforcer.enforce(
            user_id=self.user_id,
            user_email=self.user_email,
            policy=policy,
            category=category,
            amount=total,
            market_id=market.condition_id,
            action="buy",
            side=side,
            shares=shares,
            price=price,
            reasoning=decision.get("reasoning", ""),
            confidence=decision.get("confidence", 0),
            sources_count=research.get("sources_count", 0),
            db=self.db,
        )

        trade_data = {
            "market_id": market.condition_id,
            "market_question": market.question,
            "market_category": category,
            "side": side,
            "action": "buy",
            "shares": shares,
            "price": price,
            "total_amount": total,
            "confidence_score": decision.get("confidence"),
            "edge": decision.get("edge"),
            "reasoning": decision.get("reasoning"),
            "sources_count": research.get("sources_count", 0),
        }

        if enforcement["result"] == "auto_approve":
            trade = await self.trading_engine.execute_buy(
                user_id=self.user_id,
                market=market,
                side=side,
                shares=Decimal(str(shares)),
                price=Decimal(str(price)),
                decision=decision,
                enforcement_result="auto_approved",
                policy_id=policy.id if policy else None,
            )
            trade_data["id"] = str(trade.id)
            trade_data["enforcement_result"] = "auto_approved"
            trade_data["armoriq_plan_hash"] = enforcement.get("plan_hash")
            await self.ws_manager.send_to_user(
                str(self.user_id), trade_executed_event(trade_data)
            )

        elif enforcement["result"] == "hold":
            trade_data["enforcement_result"] = "held"
            approval_data = {
                "trade": trade_data,
                "reasoning": decision.get("reasoning"),
                "confidence_score": decision.get("confidence"),
                "sources": research.get("news_items", [])[:3],
                "threshold_breached": enforcement.get("threshold_breached"),
            }
            await self.ws_manager.send_to_user(
                str(self.user_id), trade_held_event(trade_data, approval_data)
            )

        else:
            trade_data["enforcement_result"] = "denied"
            await self.ws_manager.send_to_user(
                str(self.user_id),
                trade_denied_event(trade_data, enforcement.get("reason", "Policy denied")),
            )

    async def _get_active_policy(self) -> Policy | None:
        result = await self.db.execute(
            select(Policy).where(Policy.user_id == self.user_id, Policy.is_active == True)
        )
        return result.scalar_one_or_none()
