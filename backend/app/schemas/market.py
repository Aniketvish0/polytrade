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
