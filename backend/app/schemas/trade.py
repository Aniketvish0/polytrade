import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class TradeResponse(BaseModel):
    id: uuid.UUID
    market_id: str
    market_question: str
    market_category: str | None
    action: str
    side: str
    shares: Decimal
    price: Decimal
    total_amount: Decimal
    confidence_score: Decimal | None
    edge: Decimal | None
    sources_count: int | None
    reasoning: str | None
    enforcement_result: str
    armoriq_plan_hash: str | None
    executed_at: datetime

    model_config = {"from_attributes": True}


class ApprovalResponse(BaseModel):
    id: uuid.UUID
    market_id: str
    market_question: str
    action: str
    side: str
    shares: Decimal
    price: Decimal
    total_amount: Decimal
    category: str | None
    confidence_score: Decimal | None
    reasoning: str | None
    sources: dict | None
    threshold_breached: str | None
    status: str
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class ApprovalAction(BaseModel):
    note: str | None = None
