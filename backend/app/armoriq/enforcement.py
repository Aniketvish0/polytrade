import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.approval import Approval
from app.db.models.policy import Policy
from app.db.models.position import Position
from app.db.models.trade import Trade

logger = logging.getLogger(__name__)


class ArmorIQEnforcer:
    """
    Two-layer enforcement:
    1. Local policy evaluation (threshold-based auto-approve/hold/deny)
    2. ArmorIQ SDK (cryptographic audit trail, plan hashing, intent tokens)

    Local rules decide the outcome. ArmorIQ SDK adds verifiable proof.
    """

    async def enforce(
        self,
        user_id: uuid.UUID,
        user_email: str,
        policy: Policy | None,
        category: str,
        amount: float,
        market_id: str,
        action: str,
        side: str,
        shares: int,
        price: float,
        reasoning: str,
        confidence: float,
        sources_count: int,
        db: AsyncSession,
    ) -> dict:
        if not policy:
            return {"result": "auto_approve", "reason": "No active policy"}

        local_result = await self._enforce_local(
            user_id=user_id,
            policy=policy,
            category=category,
            amount=amount,
            confidence=confidence,
            sources_count=sources_count,
            db=db,
        )

        try:
            from app.config import settings

            if settings.ARMORIQ_API_KEY:
                sdk_proof = await self._get_sdk_proof(
                    user_email=user_email,
                    category=category,
                    amount=amount,
                    market_id=market_id,
                    action=action,
                    side=side,
                    shares=shares,
                    price=price,
                    reasoning=reasoning,
                )
                local_result["plan_hash"] = sdk_proof.get("plan_hash")
                local_result["intent_token_id"] = sdk_proof.get("intent_token_id")
                local_result["armoriq_decision"] = sdk_proof.get("sdk_decision")
        except ImportError:
            logger.info("ArmorIQ SDK not available")
        except Exception as e:
            logger.warning(f"ArmorIQ SDK proof failed (non-blocking): {e}")

        return local_result

    async def _get_sdk_proof(
        self,
        user_email: str,
        category: str,
        amount: float,
        market_id: str,
        action: str,
        side: str,
        shares: int,
        price: float,
        reasoning: str,
    ) -> dict:
        from armoriq_sdk import ArmorIQClient, SessionOptions
        from armoriq_sdk.models import ToolCall
        from app.config import settings

        client = ArmorIQClient(
            api_key=settings.ARMORIQ_API_KEY,
            user_id=settings.ARMORIQ_USER_ID,
            agent_id="polytrade-agent",
        )

        scoped = client.for_user(user_email)
        session = scoped.start_session(SessionOptions(
            mode="sdk",
            default_mcp_name="polymarket-mcp",
            validity_seconds=300,
        ))

        trade_params = {
            "market_id": market_id,
            "action": action,
            "side": side,
            "shares": shares,
            "price": price,
            "market_category": category,
            "total_amount": round(shares * price, 2),
            "reasoning_summary": reasoning[:200],
        }

        token = session.start_plan(
            [ToolCall(name="polymarket-mcp__buy_shares", args=trade_params)],
            goal=f"Buy {shares} {side} shares on market {market_id} at ${price}",
        )

        decision = session.check(
            "polymarket-mcp__buy_shares",
            trade_params,
            user_email=user_email,
        )

        session.report(
            "polymarket-mcp__buy_shares",
            trade_params,
            result={"status": "checked", "amount": amount},
        )

        return {
            "plan_hash": getattr(token, "plan_hash", None),
            "intent_token_id": getattr(token, "token_id", None),
            "sdk_decision": decision.action if decision else None,
        }

    async def _enforce_local(
        self,
        user_id: uuid.UUID,
        policy: Policy,
        category: str,
        amount: float,
        confidence: float,
        sources_count: int,
        db: AsyncSession,
    ) -> dict:
        category_rules = policy.category_rules or {}
        global_rules = policy.global_rules or {}
        confidence_rules = policy.confidence_rules or {}

        cat_config = category_rules.get(category, category_rules.get("_default", {}))

        if not cat_config.get("enabled", True):
            return {
                "result": "deny",
                "reason": f"Category '{category}' is disabled by policy",
            }

        max_daily_spend = global_rules.get("daily_spend_limit", global_rules.get("max_daily_spend", 200))
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        daily_result = await db.execute(
            select(func.coalesce(func.sum(Trade.total_amount), 0)).where(
                Trade.user_id == user_id,
                Trade.executed_at >= today_start,
            )
        )
        daily_spent = float(daily_result.scalar() or 0)

        if daily_spent + amount > max_daily_spend:
            return {"result": "deny", "reason": f"Daily spend limit exceeded (${max_daily_spend})"}

        max_single = global_rules.get("max_single_trade", 100)
        if amount > max_single:
            return {"result": "deny", "reason": f"Exceeds max single trade (${max_single})"}

        max_positions = global_rules.get("max_open_positions", 15)
        pos_count = await db.execute(
            select(func.count()).select_from(Position).where(
                Position.user_id == user_id, Position.status == "open"
            )
        )
        if (pos_count.scalar() or 0) >= max_positions:
            return {"result": "deny", "reason": f"Max open positions reached ({max_positions})"}

        min_sources = confidence_rules.get("min_sources", 2)
        if sources_count < min_sources:
            return {"result": "deny", "reason": f"Insufficient sources ({sources_count} < {min_sources})"}

        min_confidence = confidence_rules.get("min_confidence", confidence_rules.get("min_confidence_score", 0.65))
        if confidence < min_confidence:
            return {"result": "deny", "reason": f"Confidence too low ({confidence:.2f} < {min_confidence})"}

        auto_approve_below = cat_config.get("auto_approve_below", 10)
        hold_above = cat_config.get("hold_above", 10)
        deny_above = cat_config.get("deny_above", 100)

        high_conf = confidence_rules.get("high_confidence_bonus", {})
        if high_conf and confidence >= high_conf.get("threshold", 0.85):
            multiplier = high_conf.get("auto_approve_multiplier", 1.5)
            auto_approve_below *= multiplier

        if amount >= deny_above:
            return {"result": "deny", "reason": f"Amount ${amount} exceeds deny threshold (${deny_above})"}

        if amount >= hold_above:
            return {
                "result": "hold",
                "threshold_breached": "hold_above",
                "reason": f"Amount ${amount} exceeds auto-approve threshold (${auto_approve_below})",
            }

        cat_daily_limit = cat_config.get("max_daily_spend", 100)
        cat_daily_result = await db.execute(
            select(func.coalesce(func.sum(Trade.total_amount), 0)).where(
                Trade.user_id == user_id,
                Trade.market_category == category,
                Trade.executed_at >= today_start,
            )
        )
        cat_daily_spent = float(cat_daily_result.scalar() or 0)
        if cat_daily_spent + amount > cat_daily_limit:
            return {"result": "deny", "reason": f"Category daily limit exceeded (${cat_daily_limit})"}

        return {"result": "auto_approve"}
