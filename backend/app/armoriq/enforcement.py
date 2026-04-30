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


def _get_armoriq_client():
    from armoriq_sdk import ArmorIQClient
    from app.config import settings

    if not settings.ARMORIQ_API_KEY:
        return None
    return ArmorIQClient(
        api_key=settings.ARMORIQ_API_KEY,
        user_id=settings.ARMORIQ_USER_ID,
        agent_id="polytrade-agent",
    )


class ArmorIQEnforcer:
    """
    Two-layer enforcement:
    1. Local policy evaluation (threshold-based auto-approve/hold/deny)
    2. ArmorIQ SDK (cryptographic audit trail, plan hashing, intent tokens, delegation)

    Flow:
    - capture_plan + get_intent_token → cryptographic proof of agent intent
    - session.check → ArmorIQ policy enforcement (allow/block/hold)
    - On hold → create_delegation_request → human approval via ArmorIQ dashboard
    - After execution → session.report → audit trail
    - complete_plan → marks plan as done
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
            sdk_result = self._enforce_with_sdk(
                user_email=user_email,
                local_decision=local_result["result"],
                category=category,
                amount=amount,
                market_id=market_id,
                action=action,
                side=side,
                shares=shares,
                price=price,
                reasoning=reasoning,
            )
            if sdk_result:
                local_result.update(sdk_result)
        except Exception as e:
            logger.warning(f"ArmorIQ SDK enforcement failed (non-blocking): {e}")

        return local_result

    def _enforce_with_sdk(
        self,
        user_email: str,
        local_decision: str,
        category: str,
        amount: float,
        market_id: str,
        action: str,
        side: str,
        shares: int,
        price: float,
        reasoning: str,
    ) -> dict | None:
        from armoriq_sdk import SessionOptions
        from armoriq_sdk.models import ToolCall

        client = _get_armoriq_client()
        if not client:
            return None

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

        # Step 1: Capture plan and mint intent token
        token = session.start_plan(
            [ToolCall(name="polymarket-mcp__buy_shares", args=trade_params)],
            goal=f"Buy {shares} {side} shares on market {market_id} at ${price}",
        )
        logger.info(
            f"ArmorIQ plan captured: hash={token.plan_hash[:16]}..., "
            f"token={token.token_id}, plan_id={token.plan_id}"
        )

        # Step 2: Check against ArmorIQ policies
        decision = session.check(
            "polymarket-mcp__buy_shares",
            trade_params,
            user_email=user_email,
        )
        logger.info(
            f"ArmorIQ check: action={decision.action}, allowed={decision.allowed}, "
            f"reason={decision.reason}, policy={decision.matched_policy}"
        )

        result = {
            "plan_hash": token.plan_hash,
            "plan_id": token.plan_id,
            "intent_token_id": token.token_id,
            "armoriq_decision": decision.action,
            "armoriq_allowed": decision.allowed,
            "armoriq_reason": decision.reason,
            "armoriq_matched_policy": decision.matched_policy,
            "_session": session,
            "_client": client,
            "_token": token,
            "_trade_params": trade_params,
        }

        # Step 3: For held trades, create a delegation request in ArmorIQ
        if local_decision == "hold":
            try:
                from armoriq_sdk.models import DelegationRequestParams

                delegation = client.create_delegation_request(DelegationRequestParams(
                    tool="polymarket-mcp__buy_shares",
                    action="buy_shares",
                    arguments=trade_params,
                    amount=amount,
                    requester_email=user_email,
                    requester_role="agent",
                    requester_limit=amount,
                    domain="polymarket",
                    plan_id=token.plan_id,
                    intent_reference=token.token_id,
                    merkle_root=token.plan_hash,
                    reason=f"Trade hold: {reasoning[:100]}",
                ))
                result["delegation_id"] = delegation.delegation_id
                result["delegation_expires_at"] = delegation.expires_at
                logger.info(
                    f"ArmorIQ delegation created: id={delegation.delegation_id}, "
                    f"status={delegation.status}"
                )
            except Exception as e:
                logger.warning(f"ArmorIQ delegation request failed: {e}")

        return result

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

        max_daily_spend = global_rules.get("daily_spend_limit", global_rules.get("max_daily_spend", global_rules.get("daily_limit", 200)))
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

        max_single = global_rules.get("max_single_trade", global_rules.get("max_per_trade", 100))
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


def report_trade_execution(enforcement: dict, result: dict) -> None:
    """Call after trade is executed to report to ArmorIQ audit trail."""
    session = enforcement.get("_session")
    if not session:
        return
    try:
        trade_params = enforcement.get("_trade_params", {})
        session.report(
            "polymarket-mcp__buy_shares",
            trade_params,
            result=result,
        )
        logger.info("ArmorIQ audit: trade execution reported")
    except Exception as e:
        logger.warning(f"ArmorIQ report failed: {e}")


def complete_trade_plan(enforcement: dict) -> None:
    """Call after trade is fully complete to mark the plan as done."""
    client = enforcement.get("_client")
    plan_id = enforcement.get("plan_id")
    if not client:
        logger.warning("ArmorIQ complete_plan skipped: no _client in enforcement")
        return
    if not plan_id:
        logger.warning("ArmorIQ complete_plan skipped: no plan_id in enforcement")
        return
    try:
        client.complete_plan(plan_id)
        logger.info(f"ArmorIQ plan completed: {plan_id}")
    except Exception as e:
        logger.warning(f"ArmorIQ complete_plan failed: {e}")


def check_delegation_approved(user_email: str, delegation_id: str, amount: float) -> dict | None:
    """Check if a held trade's delegation has been approved in ArmorIQ dashboard."""
    client = _get_armoriq_client()
    if not client:
        return None
    try:
        approved = client.check_approved_delegation(
            user_email=user_email,
            tool="polymarket-mcp__buy_shares",
            amount=amount,
        )
        if approved:
            return {
                "approved": True,
                "delegation_id": approved.delegation_id,
                "approver_email": approved.approver_email,
                "approver_role": approved.approver_role,
                "delegation_token": approved.delegation_token,
            }
        return None
    except Exception as e:
        logger.warning(f"ArmorIQ delegation check failed: {e}")
        return None


def mark_delegation_executed(user_email: str, delegation_id: str) -> None:
    """Mark a delegation as executed after the trade is completed."""
    client = _get_armoriq_client()
    if not client:
        return
    try:
        client.mark_delegation_executed(user_email, delegation_id)
        logger.info(f"ArmorIQ delegation marked executed: {delegation_id}")
    except Exception as e:
        logger.warning(f"ArmorIQ mark_delegation_executed failed: {e}")
