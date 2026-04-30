import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class MarketResponse(BaseModel):
    id: uuid.UUID
    condition_id: str
    question: str
    description: str | None
    category: str | None
    slug: str | None
    yes_price: Decimal | None
    no_price: Decimal | None
    volume: Decimal | None
    liquidity: Decimal | None
    end_date: datetime | None
    is_active: bool
    resolved: bool
    last_fetched_at: datetime

    model_config = {"from_attributes": True}


class EnhancedMarketResponse(MarketResponse):
    edge_potential: float | None = None
    liquidity_score: float | None = None
    composite_score: float | None = None
    research_status: str | None = None
    last_researched_at: datetime | None = None
    user_has_position: bool = False
    position_side: str | None = None
    spread: float | None = None
    hours_to_resolution: float | None = None
