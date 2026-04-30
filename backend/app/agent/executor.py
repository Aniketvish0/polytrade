import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.armoriq.enforcement import ArmorIQEnforcer, report_trade_execution, complete_trade_plan
from app.db.models.approval import Approval
from app.db.models.audit_log import AuditLog
from app.db.models.market_cache import MarketCache
from app.db.models.policy import Policy
from app.trading.engine import SimulatedTradingEngine
from app.ws.events import portfolio_update_event, trade_denied_event, trade_executed_event, trade_held_event
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

    async def execute(self, market: MarketCache, decision: dict, research: dict) -> str:
        """Returns 'executed', 'held', 'denied', or 'pass'."""
        action_str = decision.get("action", "pass")
        if action_str == "pass":
            return "pass"

        side = "YES" if action_str == "buy_yes" else "NO"
        price = float(market.yes_price) if side == "YES" else float(market.no_price)
        shares = decision.get("suggested_shares", 10)
        total = round(shares * price, 2)
        category = market.category or "_default"

        policy = await self._get_active_policy()

        # Cap to policy max_single_trade
        if policy:
            max_single = policy.global_rules.get("max_single_trade", policy.global_rules.get("max_per_trade", 100))
            if price > 0:
                max_shares = int(max_single / price)
                if shares > max_shares:
                    shares = max(max_shares, 1)  # at least 1 share
                    total = round(shares * price, 2)

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
                armoriq_plan_hash=enforcement.get("plan_hash"),
                armoriq_intent_token_id=enforcement.get("intent_token_id"),
            )
            trade_data["id"] = str(trade.id)
            trade_data["enforcement_result"] = "auto_approved"
            trade_data["armoriq_plan_hash"] = enforcement.get("plan_hash")
            trade_data["armoriq_intent_token"] = enforcement.get("intent_token_id")
            await self.ws_manager.send_to_user(
                str(self.user_id), trade_executed_event(trade_data)
            )
            portfolio = await self.trading_engine._get_portfolio(self.user_id)
            await self.ws_manager.send_to_user(
                str(self.user_id), portfolio_update_event(portfolio)
            )

            report_trade_execution(enforcement, {
                "status": "executed",
                "trade_id": str(trade.id),
                "shares": shares,
                "price": price,
                "total_amount": total,
            })
            complete_trade_plan(enforcement)

            audit = AuditLog(
                user_id=self.user_id,
                action=f"trade_{enforcement['result']}",
                entity_type="trade",
                entity_id=trade.id,
                details={
                    "market_id": market.condition_id,
                    "market_question": market.question,
                    "side": side,
                    "shares": shares,
                    "price": price,
                    "total_amount": total,
                    "category": category,
                    "confidence": decision.get("confidence"),
                    "reasoning": decision.get("reasoning", "")[:200],
                    "enforcement_reason": enforcement.get("reason", ""),
                    "threshold_breached": enforcement.get("threshold_breached"),
                    "armoriq_decision": enforcement.get("armoriq_decision"),
                    "armoriq_matched_policy": enforcement.get("armoriq_matched_policy"),
                },
                armoriq_plan_hash=enforcement.get("plan_hash"),
                armoriq_intent_token=enforcement.get("intent_token_id"),
            )
            self.db.add(audit)
            return "executed"

        elif enforcement["result"] == "hold":
            trade_data["enforcement_result"] = "held"

            # Check for existing pending approval for same market
            existing = await self.db.execute(
                select(func.count()).select_from(Approval).where(
                    Approval.user_id == self.user_id,
                    Approval.market_id == market.condition_id,
                    Approval.status == "pending",
                )
            )
            if (existing.scalar() or 0) > 0:
                logger.info(f"Skipping duplicate approval for {market.condition_id}")
                return

            approval = Approval(
                user_id=self.user_id,
                market_id=market.condition_id,
                market_question=market.question,
                action="buy",
                side=side,
                shares=Decimal(str(shares)),
                price=Decimal(str(price)),
                total_amount=Decimal(str(total)),
                category=category,
                confidence_score=Decimal(str(decision.get("confidence", 0))),
                reasoning=decision.get("reasoning"),
                sources=[
                    {"title": n.get("title"), "source": n.get("source")}
                    for n in research.get("news_items", [])[:3]
                ],
                policy_id=policy.id if policy else None,
                threshold_breached=enforcement.get("threshold_breached"),
                armoriq_delegation_id=enforcement.get("delegation_id"),
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
            )
            self.db.add(approval)
            await self.db.flush()

            approval_data = {
                "id": str(approval.id),
                "trade": trade_data,
                "reasoning": decision.get("reasoning"),
                "confidence_score": decision.get("confidence"),
                "sources": approval.sources,
                "threshold_breached": enforcement.get("threshold_breached"),
                "expires_at": approval.expires_at.isoformat(),
            }
            await self.ws_manager.send_to_user(
                str(self.user_id), trade_held_event(trade_data, approval_data)
            )

            audit = AuditLog(
                user_id=self.user_id,
                action=f"trade_{enforcement['result']}",
                entity_type="trade",
                entity_id=approval.id,
                details={
                    "market_id": market.condition_id,
                    "market_question": market.question,
                    "side": side,
                    "shares": shares,
                    "price": price,
                    "total_amount": total,
                    "category": category,
                    "confidence": decision.get("confidence"),
                    "reasoning": decision.get("reasoning", "")[:200],
                    "enforcement_reason": enforcement.get("reason", ""),
                    "threshold_breached": enforcement.get("threshold_breached"),
                    "armoriq_decision": enforcement.get("armoriq_decision"),
                    "armoriq_matched_policy": enforcement.get("armoriq_matched_policy"),
                    "delegation_id": enforcement.get("delegation_id"),
                },
                armoriq_plan_hash=enforcement.get("plan_hash"),
                armoriq_intent_token=enforcement.get("intent_token_id"),
            )
            self.db.add(audit)
            return "held"

        else:
            trade_data["enforcement_result"] = "denied"
            await self.ws_manager.send_to_user(
                str(self.user_id),
                trade_denied_event(trade_data, enforcement.get("reason", "Policy denied")),
            )

            report_trade_execution(enforcement, {
                "status": "denied",
                "reason": enforcement.get("reason", "Policy denied"),
            })

            audit = AuditLog(
                user_id=self.user_id,
                action=f"trade_{enforcement['result']}",
                entity_type="trade",
                entity_id=None,
                details={
                    "market_id": market.condition_id,
                    "market_question": market.question,
                    "side": side,
                    "shares": shares,
                    "price": price,
                    "total_amount": total,
                    "category": category,
                    "confidence": decision.get("confidence"),
                    "reasoning": decision.get("reasoning", "")[:200],
                    "enforcement_reason": enforcement.get("reason", ""),
                    "threshold_breached": enforcement.get("threshold_breached"),
                    "armoriq_decision": enforcement.get("armoriq_decision"),
                    "armoriq_matched_policy": enforcement.get("armoriq_matched_policy"),
                },
                armoriq_plan_hash=enforcement.get("plan_hash"),
                armoriq_intent_token=enforcement.get("intent_token_id"),
            )
            self.db.add(audit)
            return "denied"

    async def _get_active_policy(self) -> Policy | None:
        result = await self.db.execute(
            select(Policy).where(Policy.user_id == self.user_id, Policy.is_active == True)
            .order_by(Policy.created_at.desc())
        )
        return result.scalars().first()
