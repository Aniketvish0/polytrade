from app.llm.base import ToolDefinition

ANALYZE_MARKET_TOOL = ToolDefinition(
    name="analyze_market",
    description="Analyze a prediction market and return a trade recommendation",
    parameters={
        "type": "object",
        "properties": {
            "estimated_probability": {
                "type": "number",
                "description": "Your estimated probability of YES outcome (0.0-1.0)",
            },
            "edge": {
                "type": "number",
                "description": "Edge = estimated probability - current market price",
            },
            "confidence": {
                "type": "number",
                "description": "Confidence score (0.0-1.0)",
            },
            "action": {
                "type": "string",
                "enum": ["buy_yes", "buy_no", "pass"],
                "description": "Recommended action",
            },
            "reasoning": {
                "type": "string",
                "description": "Brief reasoning for the recommendation (2-3 sentences)",
            },
            "suggested_shares": {
                "type": "integer",
                "description": "Suggested number of shares to trade",
            },
        },
        "required": [
            "estimated_probability",
            "edge",
            "confidence",
            "action",
            "reasoning",
            "suggested_shares",
        ],
    },
)

SCORE_NEWS_TOOL = ToolDefinition(
    name="score_news",
    description="Score a batch of news articles for relevance, credibility, and sentiment",
    parameters={
        "type": "object",
        "properties": {
            "scores": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "index": {"type": "integer"},
                        "relevance_score": {"type": "number"},
                        "credibility_score": {"type": "number"},
                        "sentiment_score": {"type": "number"},
                    },
                    "required": [
                        "index",
                        "relevance_score",
                        "credibility_score",
                        "sentiment_score",
                    ],
                },
            }
        },
        "required": ["scores"],
    },
)

PARSE_COMMAND_TOOL = ToolDefinition(
    name="parse_command",
    description="Parse a natural language input into a structured terminal command",
    parameters={
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "enum": ["command", "chat"],
            },
            "domain": {
                "type": "string",
                "enum": ["policy", "strategy", "trade", "portfolio", "agent", "help", "chat"],
            },
            "action": {"type": "string"},
            "params": {"type": "object"},
        },
        "required": ["type", "domain"],
    },
)

CHAT_RESPONSE_TOOL = ToolDefinition(
    name="chat_response",
    description="Respond to the user's message with optional actions like creating strategies or policies",
    parameters={
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "The response text to show the user",
            },
            "action": {
                "type": "object",
                "description": "Optional action to execute",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": [
                            "create_strategy",
                            "update_strategy",
                            "create_policy",
                            "update_policy",
                            "start_agent",
                            "pause_agent",
                            "none",
                        ],
                    },
                    "data": {
                        "type": "object",
                        "description": "Action-specific data",
                    },
                },
                "required": ["type"],
            },
            "message_type": {
                "type": "string",
                "enum": ["text", "strategy_preview", "policy_preview", "market_analysis"],
                "description": "Type of message for frontend rendering",
            },
        },
        "required": ["message", "message_type"],
    },
)

EXTRACT_CATEGORIES_TOOL = ToolDefinition(
    name="extract_categories",
    description="Extract the market categories the user wants to trade from their message",
    parameters={
        "type": "object",
        "properties": {
            "categories": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of categories (e.g. politics, sports, crypto, entertainment, science, business)",
            },
            "excluded_categories": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Categories the user explicitly wants to avoid",
            },
            "response": {
                "type": "string",
                "description": "Confirmation message to the user",
            },
        },
        "required": ["categories", "response"],
    },
)

EXTRACT_RISK_PARAMS_TOOL = ToolDefinition(
    name="extract_risk_params",
    description="Extract risk parameters from the user's message",
    parameters={
        "type": "object",
        "properties": {
            "daily_limit": {
                "type": "number",
                "description": "Maximum daily spending in dollars",
            },
            "max_per_trade": {
                "type": "number",
                "description": "Maximum spend per individual trade in dollars",
            },
            "auto_approve_below": {
                "type": "number",
                "description": "Auto-approve trades below this dollar amount",
            },
            "min_confidence": {
                "type": "number",
                "description": "Minimum confidence score (0.0-1.0) to consider a trade",
            },
            "response": {
                "type": "string",
                "description": "Confirmation message to the user",
            },
        },
        "required": ["daily_limit", "max_per_trade", "response"],
    },
)

CREATE_STRATEGY_FROM_NL_TOOL = ToolDefinition(
    name="create_strategy_from_nl",
    description="Create a structured trading strategy from the user's natural language description",
    parameters={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Short name for the strategy",
            },
            "context": {
                "type": "string",
                "description": "The strategy description for the LLM agent to follow",
            },
            "rules": {
                "type": "object",
                "description": "Structured strategy rules",
                "properties": {
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "min_confidence": {"type": "number"},
                    "min_edge": {"type": "number"},
                    "max_position_size": {"type": "number"},
                    "preferred_odds_range": {
                        "type": "object",
                        "properties": {
                            "min": {"type": "number"},
                            "max": {"type": "number"},
                        },
                    },
                    "category_weights": {
                        "type": "object",
                        "description": "Weight per category (0.0-1.0) for prioritizing research",
                    },
                },
            },
            "response": {
                "type": "string",
                "description": "Confirmation message to the user",
            },
        },
        "required": ["name", "context", "rules", "response"],
    },
)
