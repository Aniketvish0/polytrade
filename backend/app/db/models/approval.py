import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class Approval(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "approvals"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    market_id: Mapped[str] = mapped_column(String(255), nullable=False)
    market_question: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(String(4), nullable=False)
    side: Mapped[str] = mapped_column(String(3), nullable=False)
    shares: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(8, 6), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))

    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    reasoning: Mapped[str | None] = mapped_column(Text)
    sources: Mapped[dict | None] = mapped_column(JSONB)

    policy_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("policies.id")
    )
    threshold_breached: Mapped[str | None] = mapped_column(String(50))
    armoriq_delegation_id: Mapped[str | None] = mapped_column(String(255))

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_note: Mapped[str | None] = mapped_column(Text)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
