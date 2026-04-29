"""Tests for PositionManager (app/agent/position_manager.py)."""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agent.position_manager import STOP_LOSS_PCT, TAKE_PROFIT_THRESHOLD, PositionManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

USER_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


def _make_position(
    avg_price=Decimal("0.60"),
    shares=Decimal("100"),
    side="YES",
    market_id="0xabc",
    unrealized_pnl=Decimal("10.00"),
):
    pos = MagicMock()
    pos.id = uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
    pos.user_id = USER_ID
    pos.market_id = market_id
    pos.side = side
    pos.shares = shares
    pos.avg_price = avg_price
    pos.status = "open"
    pos.unrealized_pnl = unrealized_pnl
    pos.current_price = None
    pos.current_value = None
    return pos


def _make_market(
    condition_id="0xabc",
    yes_price=Decimal("0.70"),
    no_price=Decimal("0.30"),
    end_date=None,
):
    m = MagicMock()
    m.condition_id = condition_id
    m.yes_price = yes_price
    m.no_price = no_price
    m.end_date = end_date or datetime(2025, 12, 31, tzinfo=timezone.utc)
    return m


def _setup_db_for_positions(mock_db, positions, market_map):
    """
    Set up mock_db.execute to:
    - First call: return positions list
    - Subsequent calls: return market for each position
    """
    pos_result = MagicMock()
    pos_scalars = MagicMock()
    pos_scalars.all.return_value = positions
    pos_result.scalars.return_value = pos_scalars

    market_results = []
    for pos in positions:
        mr = MagicMock()
        mr.scalar_one_or_none.return_value = market_map.get(pos.market_id)
        market_results.append(mr)

    mock_db.execute = AsyncMock(side_effect=[pos_result] + market_results)


# ---------------------------------------------------------------------------
# take_profit — price >= 0.92
# ---------------------------------------------------------------------------


async def test_take_profit_triggers_exit(mock_db, mock_position):
    market = _make_market(yes_price=Decimal("0.95"), no_price=Decimal("0.05"))
    _setup_db_for_positions(mock_db, [mock_position], {mock_position.market_id: market})

    mock_trade = MagicMock()
    with patch("app.agent.position_manager.SimulatedTradingEngine") as MockEngine:
        engine_instance = AsyncMock()
        engine_instance.execute_sell = AsyncMock(return_value=mock_trade)
        MockEngine.return_value = engine_instance

        pm = PositionManager(db=mock_db, user_id=USER_ID)
        exits = await pm.evaluate_positions()

    assert len(exits) == 1
    assert "take_profit" in exits[0]["reason"]
    assert exits[0]["trade"] == mock_trade


# ---------------------------------------------------------------------------
# stop_loss — down >= 25%
# ---------------------------------------------------------------------------


async def test_stop_loss_triggers_exit(mock_db):
    pos = _make_position(avg_price=Decimal("0.80"))
    # Price dropped to 0.55, loss = (0.80-0.55)/0.80 = 31.25%
    market = _make_market(
        condition_id=pos.market_id,
        yes_price=Decimal("0.55"),
        no_price=Decimal("0.45"),
    )
    _setup_db_for_positions(mock_db, [pos], {pos.market_id: market})

    mock_trade = MagicMock()
    with patch("app.agent.position_manager.SimulatedTradingEngine") as MockEngine:
        engine_instance = AsyncMock()
        engine_instance.execute_sell = AsyncMock(return_value=mock_trade)
        MockEngine.return_value = engine_instance

        pm = PositionManager(db=mock_db, user_id=USER_ID)
        exits = await pm.evaluate_positions()

    assert len(exits) == 1
    assert "stop_loss" in exits[0]["reason"]


# ---------------------------------------------------------------------------
# time_decay — < 24h to expiry and profitable
# ---------------------------------------------------------------------------


async def test_time_decay_exit_profitable_near_expiry(mock_db):
    pos = _make_position(avg_price=Decimal("0.50"), unrealized_pnl=Decimal("5.00"))
    market = _make_market(
        condition_id=pos.market_id,
        yes_price=Decimal("0.60"),
        no_price=Decimal("0.40"),
        end_date=datetime.now(timezone.utc) + timedelta(hours=10),
    )
    _setup_db_for_positions(mock_db, [pos], {pos.market_id: market})

    mock_trade = MagicMock()
    with patch("app.agent.position_manager.SimulatedTradingEngine") as MockEngine:
        engine_instance = AsyncMock()
        engine_instance.execute_sell = AsyncMock(return_value=mock_trade)
        MockEngine.return_value = engine_instance

        pm = PositionManager(db=mock_db, user_id=USER_ID)
        exits = await pm.evaluate_positions()

    assert len(exits) == 1
    assert "time_decay" in exits[0]["reason"]


# ---------------------------------------------------------------------------
# no exit — normal position
# ---------------------------------------------------------------------------


async def test_no_exit_when_position_is_normal(mock_db):
    pos = _make_position(avg_price=Decimal("0.60"), unrealized_pnl=Decimal("5.00"))
    market = _make_market(
        condition_id=pos.market_id,
        yes_price=Decimal("0.70"),
        no_price=Decimal("0.30"),
        end_date=datetime.now(timezone.utc) + timedelta(days=90),
    )
    _setup_db_for_positions(mock_db, [pos], {pos.market_id: market})

    with patch("app.agent.position_manager.SimulatedTradingEngine") as MockEngine:
        engine_instance = AsyncMock()
        MockEngine.return_value = engine_instance

        pm = PositionManager(db=mock_db, user_id=USER_ID)
        exits = await pm.evaluate_positions()

    assert len(exits) == 0


# ---------------------------------------------------------------------------
# no exit — time_decay but position is unprofitable
# ---------------------------------------------------------------------------


async def test_no_exit_time_decay_but_unprofitable(mock_db):
    pos = _make_position(avg_price=Decimal("0.60"), unrealized_pnl=Decimal("-5.00"))
    market = _make_market(
        condition_id=pos.market_id,
        yes_price=Decimal("0.55"),
        no_price=Decimal("0.45"),
        end_date=datetime.now(timezone.utc) + timedelta(hours=10),
    )
    _setup_db_for_positions(mock_db, [pos], {pos.market_id: market})

    with patch("app.agent.position_manager.SimulatedTradingEngine") as MockEngine:
        engine_instance = AsyncMock()
        MockEngine.return_value = engine_instance

        pm = PositionManager(db=mock_db, user_id=USER_ID)
        exits = await pm.evaluate_positions()

    assert len(exits) == 0


# ---------------------------------------------------------------------------
# handles missing market gracefully
# ---------------------------------------------------------------------------


async def test_handles_missing_market_gracefully(mock_db):
    pos = _make_position(market_id="0xmissing")
    # Market is None for this position
    _setup_db_for_positions(mock_db, [pos], {"0xmissing": None})

    with patch("app.agent.position_manager.SimulatedTradingEngine") as MockEngine:
        engine_instance = AsyncMock()
        MockEngine.return_value = engine_instance

        pm = PositionManager(db=mock_db, user_id=USER_ID)
        exits = await pm.evaluate_positions()

    assert len(exits) == 0


# ---------------------------------------------------------------------------
# handles execute_sell error gracefully
# ---------------------------------------------------------------------------


async def test_handles_execute_sell_error_gracefully(mock_db):
    pos = _make_position(avg_price=Decimal("0.60"))
    # Price high enough to trigger take_profit
    market = _make_market(
        condition_id=pos.market_id,
        yes_price=Decimal("0.95"),
        no_price=Decimal("0.05"),
    )
    _setup_db_for_positions(mock_db, [pos], {pos.market_id: market})

    with patch("app.agent.position_manager.SimulatedTradingEngine") as MockEngine:
        engine_instance = AsyncMock()
        engine_instance.execute_sell = AsyncMock(side_effect=RuntimeError("DB error"))
        MockEngine.return_value = engine_instance

        pm = PositionManager(db=mock_db, user_id=USER_ID)
        # Should not raise
        exits = await pm.evaluate_positions()

    # The exit failed, so it shouldn't appear in results
    assert len(exits) == 0


# ---------------------------------------------------------------------------
# returns list of exits with trade and reason
# ---------------------------------------------------------------------------


async def test_returns_list_of_exits_with_trade_and_reason(mock_db):
    pos1 = _make_position(avg_price=Decimal("0.50"), market_id="0x1")
    pos2 = _make_position(avg_price=Decimal("0.80"), market_id="0x2")

    market1 = _make_market(condition_id="0x1", yes_price=Decimal("0.95"))  # take_profit
    market2 = _make_market(condition_id="0x2", yes_price=Decimal("0.55"))  # stop_loss (31.25% drop)

    # Set up multi-position DB mock
    pos_result = MagicMock()
    pos_scalars = MagicMock()
    pos_scalars.all.return_value = [pos1, pos2]
    pos_result.scalars.return_value = pos_scalars

    mr1 = MagicMock()
    mr1.scalar_one_or_none.return_value = market1
    mr2 = MagicMock()
    mr2.scalar_one_or_none.return_value = market2

    mock_db.execute = AsyncMock(side_effect=[pos_result, mr1, mr2])

    trade1 = MagicMock()
    trade2 = MagicMock()

    with patch("app.agent.position_manager.SimulatedTradingEngine") as MockEngine:
        engine_instance = AsyncMock()
        engine_instance.execute_sell = AsyncMock(side_effect=[trade1, trade2])
        MockEngine.return_value = engine_instance

        pm = PositionManager(db=mock_db, user_id=USER_ID)
        exits = await pm.evaluate_positions()

    assert len(exits) == 2
    assert all("trade" in e for e in exits)
    assert all("reason" in e for e in exits)
    assert all("position" in e for e in exits)
