from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class MarketCache(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "market_cache"

    condition_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(100))
    slug: Mapped[str | None] = mapped_column(String(500))

    yes_token_id: Mapped[str | None] = mapped_column(String(255))
    no_token_id: Mapped[str | None] = mapped_column(String(255))

    yes_price: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    no_price: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))

    volume: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    liquidity: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    outcome: Mapped[str | None] = mapped_column(String(10))

    raw_data: Mapped[dict | None] = mapped_column(JSONB)

    last_fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
