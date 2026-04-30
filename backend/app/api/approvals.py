import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.models.approval import Approval
from app.db.models.audit_log import AuditLog
from app.db.models.market_cache import MarketCache
from app.db.models.user import User
from app.dependencies import get_current_user
from app.schemas.trade import ApprovalAction, ApprovalResponse
from app.trading.engine import SimulatedTradingEngine
from app.ws.events import portfolio_update_event, trade_executed_event
from app.ws.manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter()


def _run_armoriq_approval_lifecycle(user_email: str, approval: Approval, delegation_id: str | None) -> dict:
    """Run full ArmorIQ SDK lifecycle for an approved trade: plan capture, check, report, complete."""
    try:
        from armoriq_sdk import SessionOptions
        from armoriq_sdk.models import ToolCall
        from app.armoriq.enforcement import _get_armoriq_client, mark_delegation_executed

        client = _get_armoriq_client()
        if not client:
            return {}

        if delegation_id:
            mark_delegation_executed(user_email, delegation_id)

        scoped = client.for_user(user_email)
        session = scoped.start_session(SessionOptions(
            mode="sdk",
            default_mcp_name="polymarket-mcp",
            validity_seconds=300,
        ))

        trade_params = {
            "market_id": approval.market_id,
            "action": approval.action,
            "side": approval.side,
            "shares": int(approval.shares),
            "price": float(approval.price),
            "market_category": approval.category or "_default",
            "total_amount": float(approval.total_amount),
            "reasoning_summary": (approval.reasoning or "")[:200],
            "approval_id": str(approval.id),
            "human_approved": True,
        }

        token = session.start_plan(
            [ToolCall(name="polymarket-mcp__buy_shares", args=trade_params)],
            goal=f"Human-approved trade: Buy {int(approval.shares)} {approval.side} shares on {approval.market_id}",
        )
        logger.info(
            f"ArmorIQ approval plan captured: hash={token.plan_hash[:16]}..., "
            f"token={token.token_id}, plan_id={token.plan_id}"
        )

        decision = session.check(
            "polymarket-mcp__buy_shares",
            trade_params,
            user_email=user_email,
        )
        logger.info(
            f"ArmorIQ approval check: action={decision.action}, allowed={decision.allowed}"
        )

        session.report(
            "polymarket-mcp__buy_shares",
            trade_params,
            result={"status": "human_approved", "approval_id": str(approval.id)},
        )
        logger.info("ArmorIQ approval audit: trade execution reported")

        client.complete_plan(token.plan_id)
        logger.info(f"ArmorIQ approval plan completed: {token.plan_id}")

        return {
            "plan_hash": token.plan_hash,
            "intent_token_id": token.token_id,
            "plan_id": token.plan_id,
        }

    except Exception as e:
        logger.warning(f"ArmorIQ approval lifecycle failed (non-blocking): {e}")
        return {}


@router.get("", response_model=list[ApprovalResponse])
async def list_approvals(
    status: str | None = "pending",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Approval).where(Approval.user_id == user.id)
    if status:
        query = query.where(Approval.status == status)
    query = query.order_by(desc(Approval.created_at))
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/{approval_id}/approve", response_model=ApprovalResponse)
async def approve_trade(
    approval_id: uuid.UUID,
    body: ApprovalAction = ApprovalAction(),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Approval).where(Approval.id == approval_id, Approval.user_id == user.id)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail=f"Approval already {approval.status}")
    if approval.expires_at < datetime.now(timezone.utc):
        approval.status = "expired"
        await db.flush()
        raise HTTPException(status_code=400, detail="Approval expired")

    approval.status = "approved"
    approval.resolved_by = user.id
    approval.resolved_at = datetime.now(timezone.utc)
    approval.resolution_note = body.note
    await db.flush()

    armoriq_result = _run_armoriq_approval_lifecycle(
        user_email=user.email,
        approval=approval,
        delegation_id=approval.armoriq_delegation_id,
    )

    market_result = await db.execute(
        select(MarketCache).where(MarketCache.condition_id == approval.market_id)
    )
    market = market_result.scalar_one_or_none()
    if market:
        engine = SimulatedTradingEngine(db)
        trade = await engine.execute_buy(
            user_id=user.id,
            market=market,
            side=approval.side,
            shares=approval.shares,
            price=approval.price,
            decision={
                "confidence": float(approval.confidence_score or 0),
                "reasoning": approval.reasoning,
                "sources_count": len(approval.sources or []),
            },
            enforcement_result="approved",
            policy_id=approval.policy_id,
            armoriq_plan_hash=armoriq_result.get("plan_hash"),
            armoriq_intent_token_id=armoriq_result.get("intent_token_id"),
        )
        await db.flush()

        audit = AuditLog(
            user_id=user.id,
            action="trade_approved",
            entity_type="trade",
            entity_id=trade.id,
            details={
                "market_id": approval.market_id,
                "market_question": approval.market_question,
                "side": approval.side,
                "shares": int(approval.shares),
                "price": float(approval.price),
                "total_amount": float(approval.total_amount),
                "category": approval.category,
                "confidence": float(approval.confidence_score or 0),
                "reasoning": (approval.reasoning or "")[:200],
                "enforcement_reason": "Human approved via dashboard",
                "approval_id": str(approval.id),
                "armoriq_decision": "human_approved",
            },
            armoriq_plan_hash=armoriq_result.get("plan_hash"),
            armoriq_intent_token=armoriq_result.get("intent_token_id"),
        )
        db.add(audit)

        user_key = str(user.id)
        await ws_manager.send_to_user(user_key, trade_executed_event(trade))

        portfolio = await engine._get_portfolio(user.id)
        await ws_manager.send_to_user(user_key, portfolio_update_event(portfolio))

    return approval


@router.post("/{approval_id}/reject", response_model=ApprovalResponse)
async def reject_trade(
    approval_id: uuid.UUID,
    body: ApprovalAction = ApprovalAction(),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Approval).where(Approval.id == approval_id, Approval.user_id == user.id)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail=f"Approval already {approval.status}")

    approval.status = "rejected"
    approval.resolved_by = user.id
    approval.resolved_at = datetime.now(timezone.utc)
    approval.resolution_note = body.note
    await db.flush()
    return approval
