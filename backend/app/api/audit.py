import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.models.audit_log import AuditLog
from app.db.models.user import User
from app.dependencies import get_current_user

router = APIRouter()


@router.get("")
async def list_audit_logs(
    limit: int = Query(50, le=200),
    offset: int = 0,
    action: str | None = None,
    entity_type: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(AuditLog).where(AuditLog.user_id == user.id)
    if action:
        query = query.where(AuditLog.action == action)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    query = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()
    return [
        {
            "id": str(log.id),
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": str(log.entity_id) if log.entity_id else None,
            "details": log.details,
            "armoriq_plan_hash": log.armoriq_plan_hash,
            "armoriq_intent_token": log.armoriq_intent_token,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]
