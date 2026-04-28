import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class Trade(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "trades"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    position_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("positions.id")
    )

    market_id: Mapped[str] = mapped_column(String(255), nullable=False)
    market_question: Mapped[str] = mapped_column(Text, nullable=False)
    market_category: Mapped[str | None] = mapped_column(String(100))

    action: Mapped[str] = mapped_column(String(4), nullable=False)
    side: Mapped[str] = mapped_column(String(3), nullable=False)
    shares: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(8, 6), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    edge: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    sources_count: Mapped[int | None] = mapped_column(Integer)
    reasoning: Mapped[str | None] = mapped_column(Text)
    strategy_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("strategies.id")
    )

    enforcement_result: Mapped[str] = mapped_column(String(20), nullable=False)
    policy_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("policies.id")
    )
    approval_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("approvals.id")
    )
    armoriq_plan_hash: Mapped[str | None] = mapped_column(String(255))
    armoriq_intent_token_id: Mapped[str | None] = mapped_column(String(255))

    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
