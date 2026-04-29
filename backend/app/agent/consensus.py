import asyncio
import logging

from app.db.models.market_cache import MarketCache
from app.llm.base import LLMMessage
from app.llm.prompts.market_analysis import MARKET_ANALYSIS_SYSTEM
from app.llm.registry import LLMRegistry
from app.llm.tools import ANALYZE_MARKET_TOOL

logger = logging.getLogger(__name__)


class ConsensusAnalyzer:
    MIN_AGREEMENT = 2

    async def check_consensus(
        self, market: MarketCache, research: dict, primary_decision: dict, strategy_context: str = ""
    ) -> dict | None:
        providers = LLMRegistry.available()
        if len(providers) < 2:
            return primary_decision

        system_prompt = MARKET_ANALYSIS_SYSTEM.format(strategy_context=strategy_context)

        news_lines = []
        for i, item in enumerate(research.get("news_items", [])[:5]):
            news_lines.append(f"{i+1}. [{item.get('source')}] {item.get('title')}")
        news_text = "\n".join(news_lines) or "No news."

        user_prompt = (
            f"Market: {market.question}\n"
            f"Category: {market.category}\n"
            f"YES price: {research.get('current_yes_price', 0.5)}\n"
            f"NO price: {research.get('current_no_price', 0.5)}\n\n"
            f"News:\n{news_text}\n\n"
            f"Analyze and provide your trade recommendation."
        )

        tasks = []
        for provider_name in providers:
            tasks.append(self._query_provider(provider_name, system_prompt, user_prompt))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        decisions = []
        for provider_name, result in zip(providers, results):
            if isinstance(result, Exception):
                logger.warning(f"Consensus query failed for {provider_name}: {result}")
                continue
            if result:
                result["provider"] = provider_name
                decisions.append(result)

        if not decisions:
            return primary_decision

        primary_action = primary_decision.get("action", "pass")
        agreeing = [d for d in decisions if d.get("action") == primary_action]

        if len(agreeing) >= self.MIN_AGREEMENT:
            avg_confidence = sum(d.get("confidence", 0) for d in agreeing) / len(agreeing)
            providers_agreed = [d["provider"] for d in agreeing]
            providers_disagreed = [d["provider"] for d in decisions if d.get("action") != primary_action]

            return {
                **primary_decision,
                "confidence": avg_confidence,
                "consensus": True,
                "consensus_detail": {
                    "agreed": providers_agreed,
                    "disagreed": providers_disagreed,
                    "total_queried": len(decisions),
                    "agreement_count": len(agreeing),
                },
                "reasoning": (
                    f"{primary_decision.get('reasoning', '')} "
                    f"[Consensus: {len(agreeing)}/{len(decisions)} LLMs agree]"
                ),
            }

        logger.info(
            f"Consensus not reached for {market.condition_id}: "
            f"{len(agreeing)}/{len(decisions)} agree on {primary_action}"
        )
        return None

    async def _query_provider(self, provider_name: str, system_prompt: str, user_prompt: str) -> dict | None:
        try:
            llm = LLMRegistry.get(provider_name)
            response = await asyncio.wait_for(
                llm.complete(
                    messages=[LLMMessage(role="user", content=user_prompt)],
                    tools=[ANALYZE_MARKET_TOOL],
                    system_prompt=system_prompt,
                    temperature=0.3,
                ),
                timeout=20,
            )
            if response.tool_calls:
                return response.tool_calls[0].arguments
            return None
        except Exception as e:
            raise RuntimeError(f"Provider {provider_name} failed: {e}")
