from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.llm.registry import LLMRegistry
    from app.services.market_service import MarketService

    LLMRegistry.initialize()

    market_service = MarketService()
    app.state.market_service = market_service
    app.state.market_poll_task = None
    app.state.agent_loops = {}

    yield

    if app.state.market_poll_task:
        app.state.market_poll_task.cancel()
    for loop in app.state.agent_loops.values():
        loop.stop()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Polytrade",
        description="AI-powered simulated prediction market trading agent",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.api.router import api_router

    app.include_router(api_router, prefix="/api")

    from app.api.ws import router as ws_router

    app.include_router(ws_router)

    return app


app = create_app()
