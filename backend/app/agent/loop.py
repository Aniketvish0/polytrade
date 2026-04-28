import asyncio
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agent.state import AgentState, AgentStateManager
from app.config import settings
from app.ws.events import agent_status_event, trade_denied_event, trade_executed_event, trade_held_event
from app.ws.manager import ConnectionManager

logger = logging.getLogger(__name__)


class AgentLoop:
    SCAN_INTERVAL = 30

    def __init__(
        self,
        user_id: uuid.UUID,
        user_email: str,
        db_session_factory: async_sessionmaker,
        ws_manager: ConnectionManager,
    ):
        self.user_id = user_id
        self.user_email = user_email
        self.db_session_factory = db_session_factory
        self.ws_manager = ws_manager
        self.state_manager = AgentStateManager()
        self.current_task: str | None = None
        self._task: asyncio.Task | None = None

    async def start(self):
        self._task = asyncio.create_task(self._run_loop())

    def pause(self):
        self.state_manager.pause()
        self.current_task = None
        asyncio.create_task(self._broadcast_status())

    def resume(self):
        self.state_manager.resume()
        asyncio.create_task(self._broadcast_status())

    def stop(self):
        self.state_manager.stop()
        if self._task:
            self._task.cancel()

    async def _run_loop(self):
        self.state_manager.state = AgentState.RUNNING
        await self._broadcast_status()

        while not self.state_manager.is_stopped():
            await self.state_manager.wait_if_paused()
            if self.state_manager.is_stopped():
                break

            try:
                await self._scan_and_trade()
            except Exception as e:
                logger.exception("Agent loop error")
                self.state_manager.state = AgentState.ERROR
                self.current_task = str(e)
                await self._broadcast_status()
                await asyncio.sleep(10)

            for _ in range(self.SCAN_INTERVAL):
                if self.state_manager.is_stopped():
                    break
                await asyncio.sleep(1)

    async def _scan_and_trade(self):
        from app.agent.scanner import MarketScanner
        from app.agent.researcher import MarketResearcher
        from app.agent.analyzer import TradeAnalyzer
        from app.agent.executor import TradeExecutor

        async with self.db_session_factory() as db:
            self.state_manager.state = AgentState.SCANNING
            self.current_task = "Scanning active markets"
            await self._broadcast_status()

            scanner = MarketScanner(db=db, user_id=self.user_id)
            markets = await scanner.scan()

            if not markets:
                self.state_manager.state = AgentState.RUNNING
                self.current_task = None
                await self._broadcast_status()
                return

            researcher = MarketResearcher(db=db)
            analyzer = TradeAnalyzer(db=db, user_id=self.user_id)
            executor = TradeExecutor(
                db=db,
                user_id=self.user_id,
                user_email=self.user_email,
                ws_manager=self.ws_manager,
            )

            for market in markets[:5]:
                await self.state_manager.wait_if_paused()
                if self.state_manager.is_stopped():
                    break

                self.state_manager.state = AgentState.RESEARCHING
                self.current_task = f"Researching: {market.question[:60]}"
                await self._broadcast_status()

                research = await researcher.research(market)

                self.state_manager.state = AgentState.ANALYZING
                self.current_task = f"Analyzing: {market.question[:60]}"
                await self._broadcast_status()

                decision = await analyzer.analyze(market, research)

                if decision and decision.get("action") != "pass":
                    self.state_manager.state = AgentState.TRADING
                    self.current_task = f"Trading: {market.question[:60]}"
                    await self._broadcast_status()

                    await executor.execute(market, decision, research)

            await db.commit()

        self.state_manager.state = AgentState.RUNNING
        self.current_task = None
        await self._broadcast_status()

    async def _broadcast_status(self):
        event = agent_status_event(
            status=self.state_manager.state.value,
            current_task=self.current_task,
        )
        await self.ws_manager.send_to_user(str(self.user_id), event)
