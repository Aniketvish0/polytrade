import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User

logger = logging.getLogger(__name__)

SLASH_PATTERNS = [
    (r"^/policy\s+(update|list|delete|activate|deactivate)(?:\s+(.*))?$", "policy"),
    (r"^/strategy\s+(create|update|list|delete|activate|deactivate)(?:\s+(.*))?$", "strategy"),
    (r"^/pause\s*$", "agent"),
    (r"^/resume\s*$", "agent"),
    (r"^/portfolio(?:\s+(.*))?$", "portfolio"),
    (r"^/help\s*$", "help"),
]


class CommandParser:
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user

    async def process(self, text: str) -> dict:
        text = text.strip()

        if text.startswith("/"):
            result = self._parse_slash(text)
            if result:
                return await self._dispatch(result)

        try:
            result = await self._parse_with_llm(text)
            if result and result.get("type") == "command":
                return await self._dispatch(result)
        except Exception as e:
            logger.warning(f"LLM parse failed: {e}")

        return {
            "type": "chat",
            "content": f"I'll look into that for you. You said: '{text}'",
            "message_type": "text",
        }

    def _parse_slash(self, text: str) -> dict | None:
        for pattern, domain in SLASH_PATTERNS:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                if domain == "agent":
                    action = "pause" if "/pause" in text else "resume"
                    return {"type": "command", "domain": domain, "action": action, "params": {}}
                elif domain == "help":
                    return {"type": "command", "domain": "help", "action": "show", "params": {}}
                elif domain == "portfolio":
                    return {
                        "type": "command",
                        "domain": "portfolio",
                        "action": groups[0] or "summary",
                        "params": {},
                    }
                else:
                    action = groups[0] if groups else "list"
                    params_str = groups[1] if len(groups) > 1 and groups[1] else ""
                    params = self._parse_params(params_str)
                    return {
                        "type": "command",
                        "domain": domain,
                        "action": action,
                        "params": params,
                    }
        return None

    def _parse_params(self, params_str: str) -> dict:
        if not params_str:
            return {}
        params = {}
        parts = params_str.strip().split()
        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                try:
                    value = float(value)
                except ValueError:
                    pass
                params[key] = value
            elif not params.get("name"):
                params["name"] = part
        return params

    async def _parse_with_llm(self, text: str) -> dict | None:
        from app.llm.base import LLMMessage
        from app.llm.prompts.market_analysis import COMMAND_PARSING_SYSTEM
        from app.llm.registry import LLMRegistry
        from app.llm.tools import PARSE_COMMAND_TOOL

        llm = LLMRegistry.get()
        response = await llm.complete(
            messages=[LLMMessage(role="user", content=text)],
            tools=[PARSE_COMMAND_TOOL],
            system_prompt=COMMAND_PARSING_SYSTEM,
            temperature=0.1,
        )

        if response.tool_calls:
            return response.tool_calls[0].arguments
        return None

    async def _dispatch(self, command: dict) -> dict:
        domain = command.get("domain")
        action = command.get("action")
        params = command.get("params", {})

        if domain == "help":
            return {
                "type": "success",
                "content": self._help_text(),
                "message_type": "text",
            }

        if domain == "policy" and action == "list":
            from sqlalchemy import select
            from app.db.models.policy import Policy

            result = await self.db.execute(
                select(Policy).where(Policy.user_id == self.user.id)
            )
            policies = result.scalars().all()
            if not policies:
                return {"type": "info", "content": "No policies configured yet.", "message_type": "text"}

            lines = ["**Active Policies:**"]
            for p in policies:
                status = "ACTIVE" if p.is_active else "inactive"
                lines.append(f"- {p.name} [{status}]")
                cats = p.category_rules or {}
                for cat, rules in cats.items():
                    if cat == "_default":
                        continue
                    enabled = rules.get("enabled", True)
                    auto = rules.get("auto_approve_below", "?")
                    lines.append(f"  {cat}: {'enabled' if enabled else 'DISABLED'} (auto < ${auto})")
            return {"type": "success", "content": "\n".join(lines), "message_type": "text"}

        if domain == "strategy" and action == "list":
            from sqlalchemy import select
            from app.db.models.strategy import Strategy

            result = await self.db.execute(
                select(Strategy).where(Strategy.user_id == self.user.id)
            )
            strategies = result.scalars().all()
            if not strategies:
                return {"type": "info", "content": "No strategies configured yet.", "message_type": "text"}

            lines = ["**Strategies:**"]
            for s in strategies:
                status = "ACTIVE" if s.is_active else "inactive"
                lines.append(f"- {s.name} [{status}] priority={s.priority}")
            return {"type": "success", "content": "\n".join(lines), "message_type": "text"}

        if domain == "portfolio":
            return {"type": "info", "content": "Use the dashboard panel to view your portfolio.", "message_type": "text"}

        if domain == "agent":
            return {"type": "success", "content": f"Agent {action}d.", "message_type": "text"}

        return {
            "type": "info",
            "content": f"Command received: /{domain} {action} {params}",
            "message_type": "text",
        }

    def _help_text(self) -> str:
        return """**Available Commands:**
- `/policy list` — View all policies
- `/policy update <category> <field>=<value>` — Update policy
- `/policy delete <name>` — Delete a policy
- `/policy activate <name>` — Activate a policy
- `/strategy list` — View all strategies
- `/strategy create <name>` — Create a strategy
- `/strategy activate <name>` — Activate a strategy
- `/strategy deactivate <name>` — Deactivate a strategy
- `/pause` — Pause the trading agent
- `/resume` — Resume the trading agent
- `/portfolio` — View portfolio summary
- `/help` — Show this help

You can also type natural language, e.g.:
"Set my politics limit to $30"
"What markets look good today?"
"Show me my open positions" """
