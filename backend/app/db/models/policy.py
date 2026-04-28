import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Policy(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "policies"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    global_rules: Mapped[dict] = mapped_column(JSONB, nullable=False)
    category_rules: Mapped[dict] = mapped_column(JSONB, nullable=False)
    confidence_rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    risk_rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    user: Mapped["User"] = relationship(back_populates="policies")
