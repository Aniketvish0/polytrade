import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Strategy(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "strategies"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    rules: Mapped[dict] = mapped_column(JSONB, nullable=False)
    context: Mapped[str] = mapped_column(Text, nullable=False, default="")

    user: Mapped["User"] = relationship(back_populates="strategies")
