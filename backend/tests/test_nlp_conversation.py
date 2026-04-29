"""Tests for ConversationEngine (app/nlp/conversation.py)."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.nlp.conversation import ConversationEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_llm(response):
    """Return an AsyncMock LLM provider that returns *response* from complete()."""
    llm = AsyncMock()
    llm.complete = AsyncMock(return_value=response)
    return llm


def _make_mock_trade():
    t = MagicMock()
    t.executed_at = datetime(2025, 6, 1, 12, 0, tzinfo=timezone.utc)
    t.action = "buy"
    t.side = "YES"
    t.shares = Decimal("50")
    t.price = Decimal("0.65")
    t.market_question = "Will X happen?"
    t.confidence_score = Decimal("0.80")
    t.enforcement_result = "auto_approved"
    return t


# ---------------------------------------------------------------------------
# respond() — basic
# ---------------------------------------------------------------------------


async def test_respond_returns_dict_with_required_keys(mock_db, mock_user, mock_llm_response):
    resp = mock_llm_response(
        tool_calls=[{
            "name": "chat_response",
            "arguments": {"message": "Hello!", "message_type": "text"},
        }]
    )
    llm = _make_mock_llm(resp)

    with patch("app.llm.registry.LLMRegistry.get", return_value=llm):
        engine = ConversationEngine(db=mock_db, user=mock_user)
        result = await engine.respond("hi")

    assert "type" in result
    assert "content" in result
    assert "message_type" in result
    assert result["type"] == "chat"
    assert result["content"] == "Hello!"
    assert result["message_type"] == "text"


# ---------------------------------------------------------------------------
# respond() — tool call with message extraction
# ---------------------------------------------------------------------------


async def test_respond_tool_call_extracts_message_and_type(mock_db, mock_user, mock_llm_response):
    resp = mock_llm_response(
        tool_calls=[{
            "name": "chat_response",
            "arguments": {"message": "Your balance is $1000.", "message_type": "portfolio"},
        }]
    )
    llm = _make_mock_llm(resp)

    with patch("app.llm.registry.LLMRegistry.get", return_value=llm):
        engine = ConversationEngine(db=mock_db, user=mock_user)
        result = await engine.respond("What is my balance?")

    assert result["content"] == "Your balance is $1000."
    assert result["message_type"] == "portfolio"


# ---------------------------------------------------------------------------
# respond() — tool call with action
# ---------------------------------------------------------------------------


async def test_respond_with_action_in_tool_call(mock_db, mock_user, mock_llm_response):
    resp = mock_llm_response(
        tool_calls=[{
            "name": "chat_response",
            "arguments": {
                "message": "Strategy activated.",
                "message_type": "text",
                "action": {"type": "activate_strategy", "name": "Aggressive"},
            },
        }]
    )
    llm = _make_mock_llm(resp)

    with patch("app.llm.registry.LLMRegistry.get", return_value=llm):
        engine = ConversationEngine(db=mock_db, user=mock_user)
        result = await engine.respond("Activate my aggressive strategy")

    assert "action" in result
    assert result["action"]["type"] == "activate_strategy"


# ---------------------------------------------------------------------------
# respond() — action type "none" excluded
# ---------------------------------------------------------------------------


async def test_respond_action_type_none_excluded(mock_db, mock_user, mock_llm_response):
    resp = mock_llm_response(
        tool_calls=[{
            "name": "chat_response",
            "arguments": {
                "message": "Just chatting.",
                "message_type": "text",
                "action": {"type": "none"},
            },
        }]
    )
    llm = _make_mock_llm(resp)

    with patch("app.llm.registry.LLMRegistry.get", return_value=llm):
        engine = ConversationEngine(db=mock_db, user=mock_user)
        result = await engine.respond("Hello")

    assert "action" not in result


# ---------------------------------------------------------------------------
# respond() — no tool calls falls back to content
# ---------------------------------------------------------------------------


async def test_respond_without_tool_calls_uses_content(mock_db, mock_user, mock_llm_response):
    resp = mock_llm_response(content="I can help you with that.", tool_calls=None)
    llm = _make_mock_llm(resp)

    with patch("app.llm.registry.LLMRegistry.get", return_value=llm):
        engine = ConversationEngine(db=mock_db, user=mock_user)
        result = await engine.respond("What is this?")

    assert result["content"] == "I can help you with that."
    assert result["message_type"] == "text"


# ---------------------------------------------------------------------------
# respond() — LLM error
# ---------------------------------------------------------------------------


async def test_respond_llm_error_returns_error_message(mock_db, mock_user):
    llm = AsyncMock()
    llm.complete = AsyncMock(side_effect=RuntimeError("LLM down"))

    with patch("app.llm.registry.LLMRegistry.get", return_value=llm):
        engine = ConversationEngine(db=mock_db, user=mock_user)
        result = await engine.respond("crash me")

    assert result["type"] == "chat"
    assert "error" in result["content"].lower()


# ---------------------------------------------------------------------------
# _build_context — queries 5 tables
# ---------------------------------------------------------------------------


async def test_build_context_queries_all_five_tables(mock_db, mock_user):
    engine = ConversationEngine(db=mock_db, user=mock_user)
    context = await engine._build_context()

    assert mock_db.execute.await_count == 5
    assert "portfolio" in context
    assert "positions" in context
    assert "strategies" in context
    assert "policies" in context
    assert "trades" in context


# ---------------------------------------------------------------------------
# _build_system_prompt — with portfolio
# ---------------------------------------------------------------------------


async def test_build_system_prompt_formats_portfolio(mock_db, mock_user, mock_portfolio):
    engine = ConversationEngine(db=mock_db, user=mock_user)
    template = (
        "{portfolio_summary}\n{open_positions}\n{active_strategies}\n"
        "{active_policies}\n{recent_trades}\n{agent_status}"
    )
    context = {
        "portfolio": mock_portfolio,
        "positions": [],
        "strategies": [],
        "policies": [],
        "trades": [],
    }
    result = engine._build_system_prompt(template, context)

    assert "$1000.00" in result
    assert "+50.00" in result or "$50.00" in result
    assert "60%" in result  # win rate 6/10


# ---------------------------------------------------------------------------
# _build_system_prompt — no portfolio
# ---------------------------------------------------------------------------


async def test_build_system_prompt_no_portfolio(mock_db, mock_user):
    engine = ConversationEngine(db=mock_db, user=mock_user)
    template = (
        "{portfolio_summary}\n{open_positions}\n{active_strategies}\n"
        "{active_policies}\n{recent_trades}\n{agent_status}"
    )
    context = {
        "portfolio": None,
        "positions": [],
        "strategies": [],
        "policies": [],
        "trades": [],
    }
    result = engine._build_system_prompt(template, context)

    assert "No portfolio data" in result


# ---------------------------------------------------------------------------
# _build_system_prompt — no positions
# ---------------------------------------------------------------------------


async def test_build_system_prompt_no_positions(mock_db, mock_user):
    engine = ConversationEngine(db=mock_db, user=mock_user)
    template = (
        "{portfolio_summary}\n{open_positions}\n{active_strategies}\n"
        "{active_policies}\n{recent_trades}\n{agent_status}"
    )
    context = {
        "portfolio": None,
        "positions": [],
        "strategies": [],
        "policies": [],
        "trades": [],
    }
    result = engine._build_system_prompt(template, context)

    assert "No open positions" in result


# ---------------------------------------------------------------------------
# _build_system_prompt — with strategies
# ---------------------------------------------------------------------------


async def test_build_system_prompt_with_strategies(mock_db, mock_user, mock_strategy):
    engine = ConversationEngine(db=mock_db, user=mock_user)
    template = (
        "{portfolio_summary}\n{open_positions}\n{active_strategies}\n"
        "{active_policies}\n{recent_trades}\n{agent_status}"
    )
    context = {
        "portfolio": None,
        "positions": [],
        "strategies": [mock_strategy],
        "policies": [],
        "trades": [],
    }
    result = engine._build_system_prompt(template, context)

    assert mock_strategy.name in result
    assert "ACTIVE" in result


# ---------------------------------------------------------------------------
# _build_system_prompt — with policies
# ---------------------------------------------------------------------------


async def test_build_system_prompt_with_policies(mock_db, mock_user, mock_policy):
    engine = ConversationEngine(db=mock_db, user=mock_user)
    template = (
        "{portfolio_summary}\n{open_positions}\n{active_strategies}\n"
        "{active_policies}\n{recent_trades}\n{agent_status}"
    )
    context = {
        "portfolio": None,
        "positions": [],
        "strategies": [],
        "policies": [mock_policy],
        "trades": [],
    }
    result = engine._build_system_prompt(template, context)

    assert mock_policy.name in result
    assert "ACTIVE" in result


# ---------------------------------------------------------------------------
# _build_system_prompt — with trades
# ---------------------------------------------------------------------------


async def test_build_system_prompt_with_trades(mock_db, mock_user):
    engine = ConversationEngine(db=mock_db, user=mock_user)
    template = (
        "{portfolio_summary}\n{open_positions}\n{active_strategies}\n"
        "{active_policies}\n{recent_trades}\n{agent_status}"
    )
    trade = _make_mock_trade()
    context = {
        "portfolio": None,
        "positions": [],
        "strategies": [],
        "policies": [],
        "trades": [trade],
    }
    result = engine._build_system_prompt(template, context)

    assert "BUY" in result
    assert "YES" in result
    assert "auto_approved" in result


# ---------------------------------------------------------------------------
# conversation_history mapping
# ---------------------------------------------------------------------------


async def test_conversation_history_role_mapping(mock_db, mock_user, mock_llm_response):
    resp = mock_llm_response(
        tool_calls=[{
            "name": "chat_response",
            "arguments": {"message": "Got it.", "message_type": "text"},
        }]
    )
    llm = _make_mock_llm(resp)

    history = [
        {"role": "user", "content": "Hi"},
        {"role": "agent", "content": "Hello!"},
        {"role": "system", "content": "System note"},
        {"role": "user", "content": "How are you?"},
    ]

    with patch("app.llm.registry.LLMRegistry.get", return_value=llm):
        engine = ConversationEngine(db=mock_db, user=mock_user)
        await engine.respond("Tell me more", conversation_history=history)

    call_args = llm.complete.call_args
    messages = call_args.kwargs["messages"]

    # system role entries should be skipped
    roles = [m.role for m in messages]
    assert "system" not in roles

    # "agent" role should be mapped to "assistant"
    assert "assistant" in roles

    # The final message is the current user_message
    assert messages[-1].role == "user"
    assert messages[-1].content == "Tell me more"
