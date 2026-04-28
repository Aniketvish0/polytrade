from fastapi import APIRouter

from app.api import agent, approvals, auth, chat, markets, news, policies, portfolio, strategies, trades

api_router = APIRouter()


@api_router.get("/health")
async def health():
    return {"status": "ok"}


api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(policies.router, prefix="/policies", tags=["policies"])
api_router.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(trades.router, prefix="/trades", tags=["trades"])
api_router.include_router(markets.router, prefix="/markets", tags=["markets"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
