from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.models.news_item import NewsItem
from app.db.models.user import User
from app.dependencies import get_current_user
from app.schemas.trade import TradeResponse

router = APIRouter()


@router.get("")
async def list_news(
    limit: int = Query(50, le=200),
    market_id: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(NewsItem)
    if market_id:
        query = query.where(NewsItem.market_ids.any(market_id))
    query = query.order_by(desc(NewsItem.fetched_at)).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    return [
        {
            "id": str(item.id),
            "source": item.source,
            "title": item.title,
            "url": item.url,
            "summary": item.summary,
            "relevance_score": float(item.relevance_score) if item.relevance_score else None,
            "credibility_score": float(item.credibility_score) if item.credibility_score else None,
            "sentiment_score": float(item.sentiment_score) if item.sentiment_score else None,
            "categories": item.categories,
            "fetched_at": item.fetched_at.isoformat() if item.fetched_at else None,
        }
        for item in items
    ]
