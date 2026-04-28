from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class NewsItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "news_items"

    source: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    market_ids: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    categories: Mapped[list[str] | None] = mapped_column(ARRAY(String))

    relevance_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    credibility_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    sentiment_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))

    raw_data: Mapped[dict | None] = mapped_column(JSONB)

    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
