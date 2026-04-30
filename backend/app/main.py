import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

_fh = logging.FileHandler("/tmp/polytrade-debug.log", mode="a")
_fh.setLevel(logging.DEBUG)
_fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(name)s — %(message)s"))
logging.getLogger("app").addHandler(_fh)
logging.getLogger("app").setLevel(logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio
    import logging

    from app.llm.registry import LLMRegistry
    from app.services.market_service import MarketService

    logger = logging.getLogger(__name__)

    LLMRegistry.initialize()

    market_service = MarketService()
    app.state.market_service = market_service
    app.state.agent_loops = {}

    async def market_poll_loop():
        while True:
            try:
                await market_service.fetch_and_cache_markets()
            except Exception as e:
                logger.error(f"Market poll error: {e}")
            await asyncio.sleep(30)

    app.state.market_poll_task = asyncio.create_task(market_poll_loop())

    yield

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
