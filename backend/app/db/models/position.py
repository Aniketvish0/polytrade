import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class Position(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "positions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False
    )

    market_id: Mapped[str] = mapped_column(String(255), nullable=False)
    market_slug: Mapped[str | None] = mapped_column(String(500))
    market_question: Mapped[str] = mapped_column(Text, nullable=False)
    market_category: Mapped[str | None] = mapped_column(String(100))
    token_id: Mapped[str] = mapped_column(String(255), nullable=False)

    side: Mapped[str] = mapped_column(String(3), nullable=False)
    shares: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    avg_price: Mapped[Decimal] = mapped_column(Numeric(8, 6), nullable=False)
    cost_basis: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    current_price: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    current_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    unrealized_pnl: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    resolved_outcome: Mapped[bool | None] = mapped_column(Boolean)
    realized_pnl: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))

    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
