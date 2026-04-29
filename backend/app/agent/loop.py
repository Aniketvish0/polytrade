import asyncio
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agent.state import AgentState, AgentStateManager
from app.config import settings
from app.llm.registry import LLMRegistry
from app.ws.events import agent_status_event, portfolio_update_event, trade_denied_event, trade_executed_event, trade_held_event
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

            batch = markets[:5]

            self.state_manager.state = AgentState.RESEARCHING
            self.current_task = f"Researching {len(batch)} markets in parallel"
            await self._broadcast_status()

            RESEARCH_TIMEOUT = 30
            research_tasks = [
                asyncio.wait_for(researcher.research(m), timeout=RESEARCH_TIMEOUT)
                for m in batch
            ]
            research_results = await asyncio.gather(*research_tasks, return_exceptions=True)

            for market, research in zip(batch, research_results):
                await self.state_manager.wait_if_paused()
                if self.state_manager.is_stopped():
                    break

                if isinstance(research, Exception):
                    logger.warning(f"Research failed for {market.condition_id}: {research}")
                    continue

                self.state_manager.state = AgentState.ANALYZING
                self.current_task = f"Analyzing: {market.question[:60]}"
                await self._broadcast_status()

                decision = await analyzer.analyze(market, research)

                if decision and decision.get("action") != "pass":
                    if len(LLMRegistry.available()) >= 2:
                        from app.agent.consensus import ConsensusAnalyzer
                        consensus = ConsensusAnalyzer()
                        decision = await consensus.check_consensus(
                            market, research, decision
                        )
                        if not decision:
                            logger.info(f"No consensus for {market.condition_id}, skipping")
                            continue

                    self.state_manager.state = AgentState.TRADING
                    self.current_task = f"Trading: {market.question[:60]}"
                    await self._broadcast_status()

                    await executor.execute(market, decision, research)

            await db.commit()

        await self._evaluate_positions()

        self.state_manager.state = AgentState.RUNNING
        self.current_task = None
        await self._broadcast_status()

    async def _evaluate_positions(self):
        from app.agent.position_manager import PositionManager

        try:
            async with self.db_session_factory() as db:
                manager = PositionManager(db=db, user_id=self.user_id)
                exits = await manager.evaluate_positions()

                for exit_info in exits:
                    trade = exit_info["trade"]
                    await self.ws_manager.send_to_user(
                        str(self.user_id),
                        trade_executed_event(trade),
                    )

                await db.commit()

                if exits:
                    from app.trading.engine import SimulatedTradingEngine
                    engine = SimulatedTradingEngine(db)
                    portfolio = await engine._get_portfolio(self.user_id)
                    await self.ws_manager.send_to_user(
                        str(self.user_id),
                        portfolio_update_event(portfolio),
                    )
        except Exception as e:
            logger.warning(f"Position evaluation error: {e}")

    async def _broadcast_status(self):
        event = agent_status_event(
            status=self.state_manager.state.value,
            current_task=self.current_task,
        )
        await self.ws_manager.send_to_user(str(self.user_id), event)
