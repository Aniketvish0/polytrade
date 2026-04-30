import asyncio
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agent.research_cache import get_cache
from app.agent.state import AgentState, AgentStateManager
from app.config import settings
from app.llm.registry import LLMRegistry
from app.ws.events import agent_activity_event, agent_status_event, portfolio_update_event, trade_denied_event, trade_executed_event, trade_held_event
from app.ws.manager import ConnectionManager

logger = logging.getLogger(__name__)

BATCH_SIZE = 10
RESEARCH_TIMEOUT = 30


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
        self.research_cache = get_cache(str(user_id))

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

        self.research_cache.cleanup()

        async with self.db_session_factory() as db:
            # ── Phase 1: SCAN ──
            self.state_manager.state = AgentState.SCANNING
            self.current_task = f"Scanning markets (cache: {len(self.research_cache)} entries)"
            await self._broadcast_status()

            scanner = MarketScanner(db=db, user_id=self.user_id, research_cache=self.research_cache)
            markets = await scanner.scan()

            await self._broadcast_activity("scan", f"Found {len(markets)} candidate markets", {
                "markets_count": len(markets),
                "cache_entries": len(self.research_cache),
            })

            if not markets:
                logger.info("[CYCLE] No markets to process after scan")
                await self._broadcast_activity("scan", "No markets to process — waiting for next cycle")
                self.state_manager.state = AgentState.RUNNING
                self.current_task = None
                await self._broadcast_status()
                return

            researcher = MarketResearcher(db=db, research_cache=self.research_cache)
            analyzer = TradeAnalyzer(db=db, user_id=self.user_id, research_cache=self.research_cache)
            executor = TradeExecutor(
                db=db,
                user_id=self.user_id,
                user_email=self.user_email,
                ws_manager=self.ws_manager,
            )

            batch = markets[:BATCH_SIZE]
            logger.info(f"[CYCLE] Phase 1 SCAN: {len(batch)} markets to process")

            # ── Phase 2: RESEARCH ALL ──
            self.state_manager.state = AgentState.RESEARCHING
            self.current_task = f"Researching {len(batch)} markets"
            await self._broadcast_status()

            research_tasks = [
                asyncio.wait_for(researcher.research_with_cache(m), timeout=RESEARCH_TIMEOUT)
                for m in batch
            ]
            research_results = await asyncio.gather(*research_tasks, return_exceptions=True)

            researched: list[tuple] = []
            failed_count = 0
            for market, result in zip(batch, research_results):
                if isinstance(result, Exception):
                    logger.warning(f"[RESEARCH] FAIL {market.question[:50]} — {result}")
                    failed_count += 1
                    continue
                src = result.get("sources_count", 0)
                logger.info(f"[RESEARCH] OK {market.question[:50]} — {src} sources")
                await self._broadcast_activity("research", f"Researched: {market.question[:60]}", {
                    "market_id": market.condition_id,
                    "sources_count": src,
                })
                researched.append((market, result))

            await self._broadcast_activity("research",
                f"Research complete: {len(researched)} succeeded, {failed_count} failed")

            if not researched:
                logger.info("[CYCLE] No markets survived research phase")
                await self._broadcast_activity("research", "No markets survived research — waiting for next cycle")
                self.state_manager.state = AgentState.RUNNING
                self.current_task = None
                await self._broadcast_status()
                return

            # ── Phase 3: ANALYZE ALL (collect decisions, don't trade yet) ──
            self.state_manager.state = AgentState.ANALYZING
            self.current_task = f"Analyzing {len(researched)} markets"
            await self._broadcast_status()

            candidates: list[tuple] = []
            for market, research in researched:
                await self.state_manager.wait_if_paused()
                if self.state_manager.is_stopped():
                    break

                mid = market.condition_id
                cached_entry = self.research_cache.get(mid)
                if cached_entry and cached_entry.analysis_result:
                    cached_action = cached_entry.analysis_result.get("action")
                    if cached_action == "pass":
                        current_price = float(market.yes_price) if market.yes_price else 0.5
                        if not self.research_cache.should_analyze(mid, current_price):
                            reason = cached_entry.analysis_result.get("reason", "no edge")
                            logger.info(f"[ANALYZE] SKIP {market.question[:50]} — cached pass ({reason})")
                            await self._broadcast_activity("analyze",
                                f"Skip (cached): {market.question[:50]} — {reason}")
                            continue

                self.current_task = f"Analyzing: {market.question[:60]}"
                await self._broadcast_status()

                decision = await analyzer.analyze(market, research)

                if not decision or decision.get("action") == "pass":
                    logger.info(f"[ANALYZE] PASS {market.question[:50]} — no trade signal")
                    await self._broadcast_activity("analyze",
                        f"Pass: {market.question[:50]} — no edge detected")
                    continue

                if len(LLMRegistry.available()) >= 2:
                    from app.agent.consensus import ConsensusAnalyzer
                    consensus = ConsensusAnalyzer()
                    decision = await consensus.check_consensus(market, research, decision)
                    if not decision:
                        logger.info(f"[ANALYZE] SKIP {market.question[:50]} — no consensus")
                        await self._broadcast_activity("analyze",
                            f"No consensus: {market.question[:50]} — LLMs disagree")
                        continue

                conf = decision.get("confidence", 0)
                edge = decision.get("edge", 0)
                shares = decision.get("suggested_shares", 0)
                price = float(market.yes_price) if decision.get("action") == "buy_yes" else float(market.no_price or 0.5)
                logger.info(
                    f"[ANALYZE] BUY {market.question[:50]} — "
                    f"conf={conf:.0%} edge={edge:.1%} shares={shares} "
                    f"est_cost=${shares * price:.2f}"
                )
                await self._broadcast_activity("analyze",
                    f"Trade signal: {market.question[:50]}",
                    {"confidence": round(conf, 3), "edge": round(edge, 4),
                     "shares": shares, "est_cost": round(shares * price, 2),
                     "side": decision.get("action", "").replace("buy_", "").upper()})
                candidates.append((market, research, decision))

            if not candidates:
                logger.info("[CYCLE] No trade candidates after analysis")
                await self._broadcast_activity("analyze", "No trade candidates — cycle complete")
                await db.commit()
                await self._evaluate_positions()
                self.state_manager.state = AgentState.RUNNING
                self.current_task = None
                await self._broadcast_status()
                return

            # ── Phase 4: RANK candidates ──
            candidates.sort(
                key=lambda x: x[2].get("confidence", 0) * abs(x[2].get("edge", 0)),
                reverse=True,
            )
            await self._broadcast_activity("rank",
                f"Ranked {len(candidates)} candidates by confidence × edge")
            logger.info(f"[RANKING] {len(candidates)} trade candidates:")
            for i, (m, _r, d) in enumerate(candidates):
                score = d.get("confidence", 0) * abs(d.get("edge", 0))
                logger.info(
                    f"  #{i+1} {m.question[:50]} | "
                    f"conf={d.get('confidence', 0):.0%} edge={d.get('edge', 0):.1%} "
                    f"score={score:.4f} shares={d.get('suggested_shares', 0)}"
                )

            # ── Phase 5: EXECUTE from ranked list ──
            self.state_manager.state = AgentState.TRADING
            executed_count = 0
            denied_count = 0

            for market, research, decision in candidates:
                await self.state_manager.wait_if_paused()
                if self.state_manager.is_stopped():
                    break

                self.current_task = f"Trading: {market.question[:60]}"
                await self._broadcast_status()

                result = await executor.execute(market, decision, research)

                if result == "executed":
                    self.research_cache.record_trade(market.condition_id)
                    executed_count += 1
                    logger.info(f"[TRADE] EXECUTED {market.question[:50]}")
                    await self._broadcast_activity("trade",
                        f"Executed: {market.question[:50]}",
                        {"result": "executed", "market_id": market.condition_id})
                elif result == "held":
                    self.research_cache.record_trade(market.condition_id)
                    logger.info(f"[TRADE] HELD for approval: {market.question[:50]}")
                    await self._broadcast_activity("trade",
                        f"Held for approval: {market.question[:50]}",
                        {"result": "held", "market_id": market.condition_id})
                elif result == "denied":
                    self.research_cache.record_denied(market.condition_id)
                    denied_count += 1
                    logger.info(f"[TRADE] DENIED {market.question[:50]} — stopping (likely daily limit)")
                    await self._broadcast_activity("trade",
                        f"Denied: {market.question[:50]} — daily limit reached, stopping trades",
                        {"result": "denied", "market_id": market.condition_id})
                    break

            await self._broadcast_activity("cycle",
                f"Cycle complete: {executed_count} executed, {denied_count} denied out of {len(candidates)} candidates")
            logger.info(f"[CYCLE] Complete: {executed_count} executed, {denied_count} denied, {len(candidates)} candidates")

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

    async def _broadcast_activity(self, phase: str, message: str, detail: dict | None = None):
        event = agent_activity_event(phase=phase, message=message, detail=detail)
        await self.ws_manager.send_to_user(str(self.user_id), event)
