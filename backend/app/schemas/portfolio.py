import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class PortfolioResponse(BaseModel):
    id: uuid.UUID
    balance: Decimal
    total_deposited: Decimal
    total_pnl: Decimal
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    open_positions: int
    today_pnl: Decimal
    today_trades: int
    daily_spend_used: Decimal
    daily_spend_limit: Decimal

    model_config = {"from_attributes": True}


class PositionResponse(BaseModel):
    id: uuid.UUID
    market_id: str
    market_question: str
    market_category: str | None
    side: str
    shares: Decimal
    avg_price: Decimal
    current_price: Decimal | None
    current_value: Decimal | None
    unrealized_pnl: Decimal | None
    cost_basis: Decimal
    status: str
    opened_at: datetime

    model_config = {"from_attributes": True}
