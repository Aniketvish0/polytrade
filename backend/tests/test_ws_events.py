"""Tests for app.ws.events — WSEvent dataclass and event factory functions."""

from datetime import datetime, timezone

from app.ws.events import (
    WSEvent,
    agent_message_event,
    agent_status_event,
    news_item_event,
    policy_updated_event,
    portfolio_update_event,
    strategy_updated_event,
    trade_denied_event,
    trade_executed_event,
    trade_held_event,
)


# ---------------------------------------------------------------------------
# WSEvent.to_dict
# ---------------------------------------------------------------------------

def test_ws_event_to_dict_structure():
    ev = WSEvent(type="test:event", data={"key": "value"})
    d = ev.to_dict()
    assert d["type"] == "test:event"
    assert d["data"] == {"key": "value"}
    assert "timestamp" in d
    # timestamp should be a valid ISO format string
    datetime.fromisoformat(d["timestamp"])


def test_ws_event_to_dict_preserves_nested_data():
    ev = WSEvent(type="x", data={"a": {"b": [1, 2, 3]}})
    d = ev.to_dict()
    assert d["data"]["a"]["b"] == [1, 2, 3]


def test_ws_event_custom_timestamp():
    ts = datetime(2025, 6, 1, tzinfo=timezone.utc).isoformat()
    ev = WSEvent(type="x", data={}, timestamp=ts)
    assert ev.to_dict()["timestamp"] == ts


# ---------------------------------------------------------------------------
# agent_status_event
# ---------------------------------------------------------------------------

def test_agent_status_event():
    ev = agent_status_event("running", current_task="scanning markets")
    d = ev.to_dict()
    assert d["type"] == "agent:status"
    assert d["data"]["status"] == "running"
    assert d["data"]["currentTask"] == "scanning markets"


def test_agent_status_event_no_task():
    ev = agent_status_event("idle")
    assert ev.data["currentTask"] is None


# ---------------------------------------------------------------------------
# agent_message_event
# ---------------------------------------------------------------------------

def test_agent_message_event_with_dict():
    ev = agent_message_event({"text": "hello", "extra": 42})
    d = ev.to_dict()
    assert d["type"] == "agent:message"
    assert d["data"]["message"] == {"text": "hello", "extra": 42}


def test_agent_message_event_with_string():
    ev = agent_message_event("plain string")
    assert ev.data["message"] == "plain string"


def test_agent_message_event_with_none():
    ev = agent_message_event(None)
    assert ev.data["message"] is None


def test_agent_message_event_with_int():
    ev = agent_message_event(42)
    assert ev.data["message"] == 42


# ---------------------------------------------------------------------------
# trade_executed_event
# ---------------------------------------------------------------------------

def test_trade_executed_event():
    trade = {"id": "t1", "action": "buy", "amount": 10}
    ev = trade_executed_event(trade)
    d = ev.to_dict()
    assert d["type"] == "trade:executed"
    assert d["data"]["trade"]["id"] == "t1"
    assert d["data"]["trade"]["action"] == "buy"


# ---------------------------------------------------------------------------
# trade_held_event
# ---------------------------------------------------------------------------

def test_trade_held_event():
    trade = {"id": "t2", "side": "YES"}
    approval = {"id": "a1", "reason": "needs review"}
    ev = trade_held_event(trade, approval)
    d = ev.to_dict()
    assert d["type"] == "trade:held"
    assert d["data"]["trade"]["id"] == "t2"
    assert d["data"]["approval"]["id"] == "a1"


# ---------------------------------------------------------------------------
# trade_denied_event
# ---------------------------------------------------------------------------

def test_trade_denied_event():
    trade = {"id": "t3", "action": "buy"}
    ev = trade_denied_event(trade, reason="Policy violation")
    d = ev.to_dict()
    assert d["type"] == "trade:denied"
    assert d["data"]["reason"] == "Policy violation"
    assert d["data"]["trade"]["id"] == "t3"


# ---------------------------------------------------------------------------
# portfolio_update_event
# ---------------------------------------------------------------------------

def test_portfolio_update_event():
    portfolio = {"balance": 950, "total_pnl": -50}
    ev = portfolio_update_event(portfolio)
    d = ev.to_dict()
    assert d["type"] == "portfolio:update"
    assert d["data"]["portfolio"]["balance"] == 950


# ---------------------------------------------------------------------------
# news_item_event
# ---------------------------------------------------------------------------

def test_news_item_event():
    item = {"title": "Breaking news", "source": "AP"}
    ev = news_item_event(item)
    d = ev.to_dict()
    assert d["type"] == "news:item"
    assert d["data"]["item"]["title"] == "Breaking news"


# ---------------------------------------------------------------------------
# policy_updated_event
# ---------------------------------------------------------------------------

def test_policy_updated_event():
    policy = {"id": "p1", "name": "Conservative"}
    ev = policy_updated_event(policy)
    d = ev.to_dict()
    assert d["type"] == "policy:updated"
    assert d["data"]["policy"]["name"] == "Conservative"


# ---------------------------------------------------------------------------
# strategy_updated_event
# ---------------------------------------------------------------------------

def test_strategy_updated_event():
    strategy = {"id": "s1", "name": "Aggressive"}
    ev = strategy_updated_event(strategy)
    d = ev.to_dict()
    assert d["type"] == "strategy:updated"
    assert d["data"]["strategy"]["name"] == "Aggressive"
