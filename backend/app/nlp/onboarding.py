import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User

logger = logging.getLogger(__name__)

AVAILABLE_CATEGORIES = [
    "politics", "sports", "crypto", "entertainment",
    "science", "business", "technology", "world-events",
]


class OnboardingEngine:
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user

    async def process_step(self, user_message: str) -> dict:
        step = self.user.onboarding_step or 0
        data = self.user.onboarding_data or {}

        if step == 0:
            return self._welcome()

        if step == 1:
            return await self._handle_categories(user_message, data)

        if step == 2:
            return await self._handle_risk(user_message, data)

        if step == 3:
            return await self._handle_strategy(user_message, data)

        return self._welcome()

    def _welcome(self) -> dict:
        self.user.onboarding_step = 1
        self.user.onboarding_data = {}

        cats = ", ".join(AVAILABLE_CATEGORIES)
        return {
            "type": "chat",
            "content": (
                f"Welcome to POLYTRADE! I'll help you set up your trading agent in 3 quick steps.\n\n"
                f"**Step 1/3 — Categories**\n"
                f"Which prediction market categories interest you? Available: {cats}\n\n"
                f"You can pick specific ones (e.g. \"politics and crypto\") or say \"all\"."
            ),
            "message_type": "onboarding_step",
            "data": {
                "step": 1,
                "step_name": "categories",
                "options": AVAILABLE_CATEGORIES,
            },
        }

    async def _handle_categories(self, message: str, data: dict) -> dict:
        from app.llm.base import LLMMessage
        from app.llm.prompts.terminal import ONBOARDING_SYSTEM_PROMPT
        from app.llm.registry import LLMRegistry
        from app.llm.tools import EXTRACT_CATEGORIES_TOOL

        try:
            llm = LLMRegistry.get()
            prompt = ONBOARDING_SYSTEM_PROMPT.format(
                current_step="1 — Categories",
                onboarding_data="{}",
                available_categories=", ".join(AVAILABLE_CATEGORIES),
            )
            response = await llm.complete(
                messages=[LLMMessage(role="user", content=message)],
                tools=[EXTRACT_CATEGORIES_TOOL],
                system_prompt=prompt,
                temperature=0.2,
            )

            if response.tool_calls:
                args = response.tool_calls[0].arguments
                categories = args.get("categories", AVAILABLE_CATEGORIES)
                excluded = args.get("excluded_categories", [])
                resp_text = args.get("response", "")
            else:
                categories = AVAILABLE_CATEGORIES
                excluded = []
                resp_text = "I'll set you up with all categories."

        except Exception as e:
            logger.warning(f"Category extraction failed: {e}")
            categories = AVAILABLE_CATEGORIES
            excluded = []
            resp_text = "I'll set you up with all categories."

        data["categories"] = categories
        data["excluded_categories"] = excluded
        self.user.onboarding_data = data
        self.user.onboarding_step = 2

        return {
            "type": "chat",
            "content": (
                f"{resp_text}\n\n"
                f"**Step 2/3 — Risk Parameters**\n"
                f"Now let's set your risk limits:\n"
                f"- **Daily spending limit** — max $ the agent can spend per day (default: $50)\n"
                f"- **Max per trade** — max $ per individual trade (default: $10)\n"
                f"- **Auto-approve threshold** — trades below this $ auto-execute (default: $5)\n\n"
                f"Tell me your preferences, or say \"use defaults\"."
            ),
            "message_type": "onboarding_step",
            "data": {
                "step": 2,
                "step_name": "risk",
                "categories": categories,
            },
        }

    async def _handle_risk(self, message: str, data: dict) -> dict:
        from app.llm.base import LLMMessage
        from app.llm.prompts.terminal import ONBOARDING_SYSTEM_PROMPT
        from app.llm.registry import LLMRegistry
        from app.llm.tools import EXTRACT_RISK_PARAMS_TOOL

        try:
            llm = LLMRegistry.get()
            prompt = ONBOARDING_SYSTEM_PROMPT.format(
                current_step="2 — Risk Parameters",
                onboarding_data=str(data),
                available_categories=", ".join(AVAILABLE_CATEGORIES),
            )
            response = await llm.complete(
                messages=[LLMMessage(role="user", content=message)],
                tools=[EXTRACT_RISK_PARAMS_TOOL],
                system_prompt=prompt,
                temperature=0.2,
            )

            if response.tool_calls:
                args = response.tool_calls[0].arguments
                daily_limit = args.get("daily_limit", 50)
                max_per_trade = args.get("max_per_trade", 10)
                auto_approve_below = args.get("auto_approve_below", 5)
                min_confidence = args.get("min_confidence", 0.6)
                resp_text = args.get("response", "")
            else:
                daily_limit, max_per_trade, auto_approve_below, min_confidence = 50, 10, 5, 0.6
                resp_text = "I'll use the default risk parameters."

        except Exception as e:
            logger.warning(f"Risk extraction failed: {e}")
            daily_limit, max_per_trade, auto_approve_below, min_confidence = 50, 10, 5, 0.6
            resp_text = "I'll use the default risk parameters."

        data["daily_limit"] = daily_limit
        data["max_per_trade"] = max_per_trade
        data["auto_approve_below"] = auto_approve_below
        data["min_confidence"] = min_confidence
        self.user.onboarding_data = data
        self.user.onboarding_step = 3

        return {
            "type": "chat",
            "content": (
                f"{resp_text}\n\n"
                f"**Step 3/3 — Trading Strategy**\n"
                f"Finally, describe your trading approach in plain language. For example:\n"
                f"- \"Focus on US politics, bet on likely outcomes with high media coverage\"\n"
                f"- \"Conservative approach — only high-confidence trades on major events\"\n"
                f"- \"Aggressive crypto trading, willing to take risks on volatile markets\"\n\n"
                f"What's your approach?"
            ),
            "message_type": "onboarding_step",
            "data": {
                "step": 3,
                "step_name": "strategy",
                "risk_params": {
                    "daily_limit": daily_limit,
                    "max_per_trade": max_per_trade,
                    "auto_approve_below": auto_approve_below,
                },
            },
        }

    async def _handle_strategy(self, message: str, data: dict) -> dict:
        from app.llm.base import LLMMessage
        from app.llm.prompts.terminal import ONBOARDING_SYSTEM_PROMPT
        from app.llm.registry import LLMRegistry
        from app.llm.tools import CREATE_STRATEGY_FROM_NL_TOOL

        categories = data.get("categories", AVAILABLE_CATEGORIES)

        try:
            llm = LLMRegistry.get()
            prompt = ONBOARDING_SYSTEM_PROMPT.format(
                current_step="3 — Strategy",
                onboarding_data=str(data),
                available_categories=", ".join(AVAILABLE_CATEGORIES),
            )
            response = await llm.complete(
                messages=[LLMMessage(role="user", content=message)],
                tools=[CREATE_STRATEGY_FROM_NL_TOOL],
                system_prompt=prompt,
                temperature=0.3,
            )

            if response.tool_calls:
                args = response.tool_calls[0].arguments
                strategy_name = args.get("name", "My Strategy")
                context = args.get("context", message)
                rules = args.get("rules", {})
                resp_text = args.get("response", "Strategy created!")
            else:
                strategy_name = "My Strategy"
                context = message
                rules = {}
                resp_text = "I've created your strategy based on your description."

        except Exception as e:
            logger.warning(f"Strategy creation failed: {e}")
            strategy_name = "My Strategy"
            context = message
            rules = {}
            resp_text = "I've created your strategy based on your description."

        if "categories" not in rules:
            rules["categories"] = categories
        if "min_confidence" not in rules:
            rules["min_confidence"] = data.get("min_confidence", 0.6)
        if "min_edge" not in rules:
            rules["min_edge"] = 0.05

        policy_global = {
            "daily_limit": data.get("daily_limit", 50),
            "max_per_trade": data.get("max_per_trade", 10),
        }
        policy_category = {}
        auto_below = data.get("auto_approve_below", 5)
        for cat in categories:
            policy_category[cat] = {
                "enabled": True,
                "auto_approve_below": auto_below,
            }

        return {
            "type": "chat",
            "content": (
                f"{resp_text}\n\n"
                f"**Setup Complete!** Here's what I configured:\n"
                f"- **Strategy**: {strategy_name}\n"
                f"- **Categories**: {', '.join(categories)}\n"
                f"- **Daily Limit**: ${policy_global['daily_limit']}\n"
                f"- **Max per Trade**: ${policy_global['max_per_trade']}\n\n"
                f"Starting your trading agent now..."
            ),
            "message_type": "onboarding_step",
            "data": {"step": 4, "step_name": "complete"},
            "action": {
                "type": "complete_onboarding",
                "data": {
                    "strategy": {
                        "name": strategy_name,
                        "context": context,
                        "rules": rules,
                    },
                    "policy": {
                        "name": "Default Policy",
                        "global_rules": policy_global,
                        "category_rules": policy_category,
                        "confidence_rules": {"min_confidence": data.get("min_confidence", 0.6)},
                        "risk_rules": {},
                    },
                },
            },
        }
