import asyncio
import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User

logger = logging.getLogger(__name__)


class ConversationEngine:
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user

    async def respond(self, user_message: str, conversation_history: list[dict] | None = None) -> dict:
        from app.llm.base import LLMMessage
        from app.llm.prompts.terminal import TERMINAL_SYSTEM_PROMPT
        from app.llm.registry import LLMRegistry
        from app.llm.tools import CHAT_RESPONSE_TOOL

        context = await self._build_context()
        system_prompt = self._build_system_prompt(TERMINAL_SYSTEM_PROMPT, context)

        messages = []
        if conversation_history:
            for entry in conversation_history[-10:]:
                role = entry.get("role", "user")
                content = entry.get("content", "")
                if role == "agent":
                    role = "assistant"
                elif role == "system":
                    continue
                if content:
                    messages.append(LLMMessage(role=role, content=content))

        messages.append(LLMMessage(role="user", content=user_message))

        try:
            llm = LLMRegistry.get()
            response = await llm.complete(
                messages=messages,
                tools=[CHAT_RESPONSE_TOOL],
                system_prompt=system_prompt,
                temperature=0.4,
            )

            if response.tool_calls:
                args = response.tool_calls[0].arguments
                result = {
                    "type": "chat",
                    "content": args.get("message", ""),
                    "message_type": args.get("message_type", "text"),
                }
                action = args.get("action")
                if action and action.get("type") != "none":
                    result["action"] = action
                return result

            return {
                "type": "chat",
                "content": response.content or "I'm not sure how to help with that.",
                "message_type": "text",
            }

        except Exception as e:
            logger.exception("ConversationEngine error")
            return {
                "type": "chat",
                "content": f"Sorry, I encountered an error processing your request. Please try again.",
                "message_type": "text",
            }

    async def _build_context(self) -> dict:
        from app.db.models.policy import Policy
        from app.db.models.portfolio import Portfolio
        from app.db.models.position import Position
        from app.db.models.strategy import Strategy
        from app.db.models.trade import Trade

        results = await asyncio.gather(
            self.db.execute(select(Portfolio).where(Portfolio.user_id == self.user.id)),
            self.db.execute(select(Position).where(Position.user_id == self.user.id, Position.status == "open")),
            self.db.execute(select(Strategy).where(Strategy.user_id == self.user.id)),
            self.db.execute(select(Policy).where(Policy.user_id == self.user.id)),
            self.db.execute(select(Trade).where(Trade.user_id == self.user.id).order_by(Trade.executed_at.desc()).limit(10)),
        )

        portfolio = results[0].scalar_one_or_none()
        positions = results[1].scalars().all()
        strategies = results[2].scalars().all()
        policies = results[3].scalars().all()
        trades = results[4].scalars().all()

        return {
            "portfolio": portfolio,
            "positions": positions,
            "strategies": strategies,
            "policies": policies,
            "trades": trades,
        }

    def _build_system_prompt(self, template: str, context: dict) -> str:
        portfolio = context["portfolio"]
        if portfolio:
            portfolio_text = (
                f"Balance: ${portfolio.balance:.2f} | "
                f"Total P&L: ${portfolio.total_pnl:+.2f} | "
                f"Total Trades: {portfolio.total_trades} | "
                f"Win Rate: {(portfolio.winning_trades / max(portfolio.total_trades, 1) * 100):.0f}%"
            )
        else:
            portfolio_text = "No portfolio data."

        positions = context["positions"]
        if positions:
            pos_lines = []
            for p in positions:
                pnl = f"${p.unrealized_pnl:+.2f}" if p.unrealized_pnl else "N/A"
                pos_lines.append(
                    f"- {p.market_question[:60]} | {p.side.upper()} {p.shares} @ ${p.avg_price:.2f} | P&L: {pnl}"
                )
            positions_text = "\n".join(pos_lines)
        else:
            positions_text = "No open positions."

        strategies = context["strategies"]
        if strategies:
            strat_lines = []
            for s in strategies:
                status = "ACTIVE" if s.is_active else "inactive"
                cats = s.rules.get("categories", []) if s.rules else []
                strat_lines.append(
                    f"- {s.name} [{status}] categories={cats} context=\"{s.context[:80]}\""
                )
            strategies_text = "\n".join(strat_lines)
        else:
            strategies_text = "No strategies configured."

        policies = context["policies"]
        if policies:
            pol_lines = []
            for p in policies:
                status = "ACTIVE" if p.is_active else "inactive"
                global_r = p.global_rules or {}
                pol_lines.append(
                    f"- {p.name} [{status}] daily_limit=${global_r.get('daily_spend_limit', global_r.get('daily_limit', '?'))} max_trade=${global_r.get('max_single_trade', global_r.get('max_per_trade', '?'))}"
                )
                for cat, rules in (p.category_rules or {}).items():
                    if cat == "_default":
                        continue
                    pol_lines.append(f"  {cat}: enabled={rules.get('enabled', True)} auto_below=${rules.get('auto_approve_below', '?')}")
            policies_text = "\n".join(pol_lines)
        else:
            policies_text = "No policies configured."

        trades = context["trades"]
        if trades:
            trade_lines = []
            for t in trades:
                trade_lines.append(
                    f"- {t.executed_at.strftime('%m/%d %H:%M')} | {t.action.upper()} {t.side.upper()} {t.shares} @ ${t.price:.2f} | "
                    f"{t.market_question[:50]} | conf={t.confidence_score or 'N/A'} | {t.enforcement_result}"
                )
            trades_text = "\n".join(trade_lines)
        else:
            trades_text = "No trades yet."

        agent_status = "Check agent status via /status command."

        return template.format(
            portfolio_summary=portfolio_text,
            open_positions=positions_text,
            active_strategies=strategies_text,
            active_policies=policies_text,
            recent_trades=trades_text,
            agent_status=agent_status,
        )
