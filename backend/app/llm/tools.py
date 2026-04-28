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
