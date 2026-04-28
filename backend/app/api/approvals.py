import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.models.approval import Approval
from app.db.models.market_cache import MarketCache
from app.db.models.user import User
from app.dependencies import get_current_user
from app.schemas.trade import ApprovalAction, ApprovalResponse
from app.trading.engine import SimulatedTradingEngine
from app.ws.events import portfolio_update_event, trade_executed_event
from app.ws.manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter()


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
        )
        await db.flush()

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
