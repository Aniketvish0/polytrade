"""Tests for app.llm.tools — tool definitions."""

from app.llm.tools import (
    ANALYZE_MARKET_TOOL,
    CHAT_RESPONSE_TOOL,
    CREATE_STRATEGY_FROM_NL_TOOL,
    EXTRACT_CATEGORIES_TOOL,
    EXTRACT_RISK_PARAMS_TOOL,
    PARSE_COMMAND_TOOL,
    SCORE_NEWS_TOOL,
)


def _has_required(tool, expected_required):
    """Assert the tool's parameters contain the expected required fields."""
    actual = set(tool.parameters.get("required", []))
    expected = set(expected_required)
    assert expected.issubset(actual), (
        f"{tool.name}: missing required fields {expected - actual}"
    )


def _has_properties(tool, expected_props):
    """Assert the tool's parameters.properties contain the expected keys."""
    props = tool.parameters.get("properties", {})
    for key in expected_props:
        assert key in props, f"{tool.name}: missing property '{key}'"


# ---------------------------------------------------------------------------
# ANALYZE_MARKET_TOOL
# ---------------------------------------------------------------------------

def test_analyze_market_tool_has_required_fields():
    _has_required(ANALYZE_MARKET_TOOL, [
        "estimated_probability", "edge", "confidence", "action", "reasoning", "suggested_shares",
    ])


def test_analyze_market_tool_name_and_description():
    assert ANALYZE_MARKET_TOOL.name == "analyze_market"
    assert len(ANALYZE_MARKET_TOOL.description) > 0


def test_analyze_market_tool_action_enum():
    props = ANALYZE_MARKET_TOOL.parameters["properties"]
    assert set(props["action"]["enum"]) == {"buy_yes", "buy_no", "pass"}


def test_analyze_market_tool_probability_is_number():
    props = ANALYZE_MARKET_TOOL.parameters["properties"]
    assert props["estimated_probability"]["type"] == "number"


# ---------------------------------------------------------------------------
# SCORE_NEWS_TOOL
# ---------------------------------------------------------------------------

def test_score_news_tool_has_required_fields():
    _has_required(SCORE_NEWS_TOOL, ["scores"])


def test_score_news_tool_scores_is_array():
    props = SCORE_NEWS_TOOL.parameters["properties"]
    assert props["scores"]["type"] == "array"


def test_score_news_tool_item_schema():
    items = SCORE_NEWS_TOOL.parameters["properties"]["scores"]["items"]
    required = set(items.get("required", []))
    assert {"index", "relevance_score", "credibility_score", "sentiment_score"}.issubset(required)


# ---------------------------------------------------------------------------
# PARSE_COMMAND_TOOL
# ---------------------------------------------------------------------------

def test_parse_command_tool_has_required_fields():
    _has_required(PARSE_COMMAND_TOOL, ["type", "domain"])


def test_parse_command_tool_type_enum():
    props = PARSE_COMMAND_TOOL.parameters["properties"]
    assert set(props["type"]["enum"]) == {"command", "chat"}


def test_parse_command_tool_domain_enum():
    props = PARSE_COMMAND_TOOL.parameters["properties"]
    expected = {"policy", "strategy", "trade", "portfolio", "agent", "help", "chat"}
    assert set(props["domain"]["enum"]) == expected


def test_parse_command_tool_has_params_property():
    _has_properties(PARSE_COMMAND_TOOL, ["params"])


# ---------------------------------------------------------------------------
# CHAT_RESPONSE_TOOL
# ---------------------------------------------------------------------------

def test_chat_response_tool_has_required_fields():
    _has_required(CHAT_RESPONSE_TOOL, ["message", "message_type"])


def test_chat_response_tool_action_enum():
    action_props = CHAT_RESPONSE_TOOL.parameters["properties"]["action"]
    action_type = action_props["properties"]["type"]
    expected = {
        "create_strategy", "update_strategy",
        "create_policy", "update_policy",
        "start_agent", "pause_agent", "none",
    }
    assert set(action_type["enum"]) == expected


def test_chat_response_tool_message_type_enum():
    props = CHAT_RESPONSE_TOOL.parameters["properties"]
    expected = {"text", "strategy_preview", "policy_preview", "market_analysis"}
    assert set(props["message_type"]["enum"]) == expected


def test_chat_response_tool_action_has_required_type():
    action_props = CHAT_RESPONSE_TOOL.parameters["properties"]["action"]
    assert "type" in action_props.get("required", [])


# ---------------------------------------------------------------------------
# EXTRACT_CATEGORIES_TOOL
# ---------------------------------------------------------------------------

def test_extract_categories_tool_has_required_fields():
    _has_required(EXTRACT_CATEGORIES_TOOL, ["categories", "response"])


def test_extract_categories_tool_categories_is_array():
    props = EXTRACT_CATEGORIES_TOOL.parameters["properties"]
    assert props["categories"]["type"] == "array"
    assert props["categories"]["items"]["type"] == "string"


def test_extract_categories_tool_has_excluded_categories():
    _has_properties(EXTRACT_CATEGORIES_TOOL, ["excluded_categories"])


# ---------------------------------------------------------------------------
# EXTRACT_RISK_PARAMS_TOOL
# ---------------------------------------------------------------------------

def test_extract_risk_params_tool_has_required_fields():
    _has_required(EXTRACT_RISK_PARAMS_TOOL, ["daily_limit", "max_per_trade", "response"])


def test_extract_risk_params_tool_has_optional_fields():
    _has_properties(EXTRACT_RISK_PARAMS_TOOL, [
        "auto_approve_below", "min_confidence",
    ])


def test_extract_risk_params_tool_daily_limit_is_number():
    props = EXTRACT_RISK_PARAMS_TOOL.parameters["properties"]
    assert props["daily_limit"]["type"] == "number"


# ---------------------------------------------------------------------------
# CREATE_STRATEGY_FROM_NL_TOOL
# ---------------------------------------------------------------------------

def test_create_strategy_from_nl_tool_has_required_fields():
    _has_required(CREATE_STRATEGY_FROM_NL_TOOL, ["name", "context", "rules", "response"])


def test_create_strategy_from_nl_tool_rules_has_categories():
    rules_props = CREATE_STRATEGY_FROM_NL_TOOL.parameters["properties"]["rules"]
    assert "categories" in rules_props.get("properties", {})


def test_create_strategy_from_nl_tool_rules_has_preferred_odds_range():
    rules_props = CREATE_STRATEGY_FROM_NL_TOOL.parameters["properties"]["rules"]
    assert "preferred_odds_range" in rules_props.get("properties", {})
    odds = rules_props["properties"]["preferred_odds_range"]
    assert "min" in odds.get("properties", {})
    assert "max" in odds.get("properties", {})


def test_all_tools_are_tool_definition_instances():
    from app.llm.base import ToolDefinition
    tools = [
        ANALYZE_MARKET_TOOL, SCORE_NEWS_TOOL, PARSE_COMMAND_TOOL,
        CHAT_RESPONSE_TOOL, EXTRACT_CATEGORIES_TOOL, EXTRACT_RISK_PARAMS_TOOL,
        CREATE_STRATEGY_FROM_NL_TOOL,
    ]
    for t in tools:
        assert isinstance(t, ToolDefinition), f"{t} is not a ToolDefinition"
        assert isinstance(t.name, str) and len(t.name) > 0
        assert isinstance(t.description, str) and len(t.description) > 0
        assert isinstance(t.parameters, dict)
        assert t.parameters.get("type") == "object"
