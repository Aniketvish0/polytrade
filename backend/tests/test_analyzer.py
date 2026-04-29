"""Tests for TradeAnalyzer (app/agent/analyzer.py)."""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agent.analyzer import TradeAnalyzer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

USER_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


def _make_strategy(entry_criteria=None, position_sizing=None, context="Test strategy"):
    s = MagicMock()
    s.id = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
    s.user_id = USER_ID
    s.is_active = True
    s.priority = 0
    s.context = context
    s.rules = {
        "entry_criteria": entry_criteria or {"min_confidence": 0.65, "min_edge": 0.05, "min_sources": 2},
        "position_sizing": position_sizing or {"max_trade_amount": 50},
        "categories": ["politics"],
    }
    return s


def _make_research():
    return {
        "current_yes_price": 0.65,
        "current_no_price": 0.35,
        "sources_count": 3,
        "news_items": [
            {"source": "Reuters", "title": "Big event happening", "relevance_score": 0.9, "sentiment_score": 0.5},
            {"source": "AP", "title": "Related story", "relevance_score": 0.7, "sentiment_score": 0.3},
        ],
    }


def _make_mock_llm(response):
    llm = AsyncMock()
    llm.complete = AsyncMock(return_value=response)
    return llm


def _setup_db_strategy(mock_db, strategy):
    result = MagicMock()
    scalars = MagicMock()
    scalars.first.return_value = strategy
    result.scalars.return_value = scalars
    mock_db.execute = AsyncMock(return_value=result)


# ---------------------------------------------------------------------------
# analyze() — returns decision from tool call
# ---------------------------------------------------------------------------


async def test_analyze_returns_decision_from_tool_call(mock_db, mock_market, mock_llm_response):
    strategy = _make_strategy()
    _setup_db_strategy(mock_db, strategy)

    # Ensure market is not expired
    mock_market.end_date = datetime.now(timezone.utc) + timedelta(days=30)

    decision = {
        "action": "buy_yes",
        "confidence": 0.8,
        "edge": 0.15,
        "reasoning": "Strong political signal",
        "suggested_shares": 20,
    }
    resp = mock_llm_response(tool_calls=[{"name": "analyze_market", "arguments": decision}])
    llm = _make_mock_llm(resp)

    with patch("app.agent.analyzer.LLMRegistry") as MockReg:
        MockReg.get.return_value = llm
        analyzer = TradeAnalyzer(db=mock_db, user_id=USER_ID)
        result = await analyzer.analyze(mock_market, _make_research())

    assert result is not None
    assert result["action"] == "buy_yes"
    assert result["confidence"] == 0.8
    assert result["strategy_id"] == str(strategy.id)


# ---------------------------------------------------------------------------
# analyze() — returns None when no active strategy
# ---------------------------------------------------------------------------


async def test_analyze_returns_none_no_active_strategy(mock_db, mock_market):
    _setup_db_strategy(mock_db, None)
    mock_market.end_date = datetime.now(timezone.utc) + timedelta(days=30)

    analyzer = TradeAnalyzer(db=mock_db, user_id=USER_ID)
    result = await analyzer.analyze(mock_market, _make_research())

    assert result is None


# ---------------------------------------------------------------------------
# analyze() — returns None when LLM fails
# ---------------------------------------------------------------------------


async def test_analyze_returns_none_when_llm_fails(mock_db, mock_market):
    strategy = _make_strategy()
    _setup_db_strategy(mock_db, strategy)
    mock_market.end_date = datetime.now(timezone.utc) + timedelta(days=30)

    llm = AsyncMock()
    llm.complete = AsyncMock(side_effect=RuntimeError("LLM error"))

    with patch("app.agent.analyzer.LLMRegistry") as MockReg:
        MockReg.get.return_value = llm
        analyzer = TradeAnalyzer(db=mock_db, user_id=USER_ID)
        result = await analyzer.analyze(mock_market, _make_research())

    assert result is None


# ---------------------------------------------------------------------------
# _validate_decision — confidence below threshold
# ---------------------------------------------------------------------------


async def test_validate_decision_confidence_below_threshold(mock_db):
    strategy = _make_strategy(entry_criteria={"min_confidence": 0.7, "min_edge": 0.05})
    analyzer = TradeAnalyzer(db=mock_db, user_id=USER_ID)

    decision = {"action": "buy_yes", "confidence": 0.5, "edge": 0.10}
    result = analyzer._validate_decision(decision, {"min_confidence": 0.7, "min_edge": 0.05}, {}, strategy)

    assert result is None


# ---------------------------------------------------------------------------
# _validate_decision — edge below threshold
# ---------------------------------------------------------------------------


async def test_validate_decision_edge_below_threshold(mock_db):
    strategy = _make_strategy()
    analyzer = TradeAnalyzer(db=mock_db, user_id=USER_ID)

    decision = {"action": "buy_yes", "confidence": 0.9, "edge": 0.02}
    result = analyzer._validate_decision(decision, {"min_confidence": 0.65, "min_edge": 0.05}, {}, strategy)

    assert result is None


# ---------------------------------------------------------------------------
# _validate_decision — "pass" action passes through
# ---------------------------------------------------------------------------


async def test_validate_decision_pass_action_passes_through(mock_db):
    strategy = _make_strategy()
    analyzer = TradeAnalyzer(db=mock_db, user_id=USER_ID)

    decision = {"action": "pass", "confidence": 0.2, "edge": 0.01, "reasoning": "Not enough info"}
    result = analyzer._validate_decision(decision, {"min_confidence": 0.65, "min_edge": 0.05}, {}, strategy)

    assert result is not None
    assert result["action"] == "pass"


# ---------------------------------------------------------------------------
# time_decay_note — market expiring < 24h
# ---------------------------------------------------------------------------


async def test_time_decay_note_less_than_24h(mock_db, mock_market, mock_llm_response):
    strategy = _make_strategy()
    _setup_db_strategy(mock_db, strategy)

    # Set market to expire in 12 hours
    mock_market.end_date = datetime.now(timezone.utc) + timedelta(hours=12)

    decision = {"action": "buy_yes", "confidence": 0.9, "edge": 0.15, "suggested_shares": 10}
    resp = mock_llm_response(tool_calls=[{"name": "analyze_market", "arguments": decision}])
    llm = _make_mock_llm(resp)

    with patch("app.agent.analyzer.LLMRegistry") as MockReg:
        MockReg.get.return_value = llm
        analyzer = TradeAnalyzer(db=mock_db, user_id=USER_ID)
        await analyzer.analyze(mock_market, _make_research())

    # Verify the user prompt sent to LLM contains time-sensitive warning
    call_args = llm.complete.call_args
    messages = call_args.kwargs["messages"]
    user_msg = messages[0].content
    assert "TIME-SENSITIVE" in user_msg


# ---------------------------------------------------------------------------
# time_decay_note — market expiring < 48h
# ---------------------------------------------------------------------------


async def test_time_decay_note_less_than_48h(mock_db, mock_market, mock_llm_response):
    strategy = _make_strategy()
    _setup_db_strategy(mock_db, strategy)

    # Set market to expire in 36 hours
    mock_market.end_date = datetime.now(timezone.utc) + timedelta(hours=36)

    decision = {"action": "buy_yes", "confidence": 0.9, "edge": 0.15, "suggested_shares": 10}
    resp = mock_llm_response(tool_calls=[{"name": "analyze_market", "arguments": decision}])
    llm = _make_mock_llm(resp)

    with patch("app.agent.analyzer.LLMRegistry") as MockReg:
        MockReg.get.return_value = llm
        analyzer = TradeAnalyzer(db=mock_db, user_id=USER_ID)
        await analyzer.analyze(mock_market, _make_research())

    call_args = llm.complete.call_args
    messages = call_args.kwargs["messages"]
    user_msg = messages[0].content
    assert "time-decay" in user_msg.lower()


# ---------------------------------------------------------------------------
# expired market returns None
# ---------------------------------------------------------------------------


async def test_expired_market_returns_none(mock_db, mock_market):
    strategy = _make_strategy()
    _setup_db_strategy(mock_db, strategy)

    # Set market to have already expired
    mock_market.end_date = datetime.now(timezone.utc) - timedelta(hours=1)

    analyzer = TradeAnalyzer(db=mock_db, user_id=USER_ID)
    result = await analyzer.analyze(mock_market, _make_research())

    assert result is None


# ---------------------------------------------------------------------------
# _format_news — with items
# ---------------------------------------------------------------------------


async def test_format_news_with_items(mock_db):
    analyzer = TradeAnalyzer(db=mock_db, user_id=USER_ID)
    items = [
        {"source": "Reuters", "title": "Big event", "relevance_score": 0.9, "sentiment_score": 0.5},
        {"source": "AP", "title": "Related", "relevance_score": 0.7, "sentiment_score": 0.3},
    ]
    result = analyzer._format_news(items)

    assert "Reuters" in result
    assert "Big event" in result
    assert "AP" in result


# ---------------------------------------------------------------------------
# _format_news — empty list
# ---------------------------------------------------------------------------


async def test_format_news_empty_list(mock_db):
    analyzer = TradeAnalyzer(db=mock_db, user_id=USER_ID)
    result = analyzer._format_news([])

    assert result == "No news available."
