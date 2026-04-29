"""Tests for MarketScanner (app/agent/scanner.py)."""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agent.scanner import MarketScanner


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

USER_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


def _make_market(condition_id="0x1", category="politics", volume=Decimal("10000"), yes_price=Decimal("0.50")):
    m = MagicMock()
    m.condition_id = condition_id
    m.category = category
    m.volume = volume
    m.yes_price = yes_price
    m.no_price = Decimal("1") - yes_price
    m.is_active = True
    m.resolved = False
    return m


def _make_strategy(categories=None, rules=None):
    s = MagicMock()
    s.id = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
    s.user_id = USER_ID
    s.is_active = True
    s.priority = 0
    s.rules = rules or {}
    if categories and "categories" not in s.rules:
        s.rules["categories"] = categories
    return s


def _setup_db(mock_db, strategy=None, markets=None):
    """
    Configure mock_db.execute to return strategy on first call (for _get_active_strategy)
    and markets on second call (for the main scan query).
    """
    strategy_result = MagicMock()
    strategy_scalars = MagicMock()
    strategy_scalars.first.return_value = strategy
    strategy_result.scalars.return_value = strategy_scalars

    market_result = MagicMock()
    market_scalars = MagicMock()
    market_scalars.all.return_value = markets or []
    market_result.scalars.return_value = market_scalars

    mock_db.execute = AsyncMock(side_effect=[strategy_result, market_result])


# ---------------------------------------------------------------------------
# scan() — returns markets from DB
# ---------------------------------------------------------------------------


async def test_scan_returns_markets(mock_db):
    markets = [_make_market("0x1"), _make_market("0x2")]
    _setup_db(mock_db, strategy=None, markets=markets)

    scanner = MarketScanner(db=mock_db, user_id=USER_ID)
    result = await scanner.scan()

    assert len(result) == 2
    assert result[0].condition_id == "0x1"


# ---------------------------------------------------------------------------
# scan() — no active strategy returns all markets
# ---------------------------------------------------------------------------


async def test_scan_no_active_strategy_returns_all_markets(mock_db):
    markets = [_make_market(f"0x{i}") for i in range(5)]
    _setup_db(mock_db, strategy=None, markets=markets)

    scanner = MarketScanner(db=mock_db, user_id=USER_ID)
    result = await scanner.scan()

    assert len(result) == 5


# ---------------------------------------------------------------------------
# scan() — filters by strategy categories
# ---------------------------------------------------------------------------


async def test_scan_filters_by_strategy_categories(mock_db):
    strategy = _make_strategy(categories=["politics", "sports"])
    markets = [_make_market("0x1", category="politics"), _make_market("0x2", category="sports")]
    _setup_db(mock_db, strategy=strategy, markets=markets)

    scanner = MarketScanner(db=mock_db, user_id=USER_ID)
    result = await scanner.scan()

    # The DB filtering happens in the query, so we just verify execute was called
    assert mock_db.execute.await_count == 2
    assert len(result) == 2


# ---------------------------------------------------------------------------
# scan() — filters by odds range (dict format)
# ---------------------------------------------------------------------------


async def test_scan_filters_by_odds_range_dict_format(mock_db):
    strategy = _make_strategy(rules={
        "market_filters": {
            "odds_range": {"min": 0.20, "max": 0.80},
        },
    })
    markets = [_make_market("0x1", yes_price=Decimal("0.50"))]
    _setup_db(mock_db, strategy=strategy, markets=markets)

    scanner = MarketScanner(db=mock_db, user_id=USER_ID)
    result = await scanner.scan()

    assert mock_db.execute.await_count == 2


# ---------------------------------------------------------------------------
# scan() — filters by odds range (list format)
# ---------------------------------------------------------------------------


async def test_scan_filters_by_odds_range_list_format(mock_db):
    strategy = _make_strategy(rules={
        "market_filters": {
            "odds_range": [0.15, 0.85],
        },
    })
    markets = [_make_market("0x1")]
    _setup_db(mock_db, strategy=strategy, markets=markets)

    scanner = MarketScanner(db=mock_db, user_id=USER_ID)
    result = await scanner.scan()

    assert mock_db.execute.await_count == 2


# ---------------------------------------------------------------------------
# scan() — sorts by category_weights
# ---------------------------------------------------------------------------


async def test_scan_sorts_by_category_weights(mock_db):
    strategy = _make_strategy(rules={
        "categories": ["politics", "sports", "crypto"],
        "category_weights": {"politics": 0.9, "sports": 0.5, "crypto": 0.3},
    })
    markets = [
        _make_market("0x1", category="crypto"),
        _make_market("0x2", category="politics"),
        _make_market("0x3", category="sports"),
    ]
    _setup_db(mock_db, strategy=strategy, markets=markets)

    scanner = MarketScanner(db=mock_db, user_id=USER_ID)
    result = await scanner.scan()

    # politics (0.9) > sports (0.5) > crypto (0.3)
    assert result[0].category == "politics"
    assert result[1].category == "sports"
    assert result[2].category == "crypto"


# ---------------------------------------------------------------------------
# scan() — limits to 10 results
# ---------------------------------------------------------------------------


async def test_scan_limits_to_10_results(mock_db):
    strategy = _make_strategy(rules={
        "category_weights": {"politics": 0.9},
    })
    markets = [_make_market(f"0x{i}", category="politics") for i in range(15)]
    _setup_db(mock_db, strategy=strategy, markets=markets)

    scanner = MarketScanner(db=mock_db, user_id=USER_ID)
    result = await scanner.scan()

    assert len(result) <= 10


# ---------------------------------------------------------------------------
# scan() — min_volume filter
# ---------------------------------------------------------------------------


async def test_scan_with_min_volume_filter(mock_db):
    strategy = _make_strategy(rules={
        "market_filters": {
            "min_volume": 5000,
        },
    })
    markets = [_make_market("0x1", volume=Decimal("10000"))]
    _setup_db(mock_db, strategy=strategy, markets=markets)

    scanner = MarketScanner(db=mock_db, user_id=USER_ID)
    result = await scanner.scan()

    # The volume filter is applied in the SQL query, so just verify we got results
    assert mock_db.execute.await_count == 2


# ---------------------------------------------------------------------------
# scan() — multiple active strategies picks highest priority (no crash)
# ---------------------------------------------------------------------------


async def test_scan_with_multiple_active_strategies_does_not_crash(mock_db):
    """Regression: scalar_one_or_none() crashed with MultipleResultsFound."""
    strategy = _make_strategy(categories=["politics"])
    markets = [_make_market("0x1", category="politics")]

    strategy_result = MagicMock()
    strategy_scalars = MagicMock()
    strategy_scalars.first.return_value = strategy
    strategy_result.scalars.return_value = strategy_scalars

    market_result = MagicMock()
    market_scalars = MagicMock()
    market_scalars.all.return_value = markets
    market_result.scalars.return_value = market_scalars

    mock_db.execute = AsyncMock(side_effect=[strategy_result, market_result])

    scanner = MarketScanner(db=mock_db, user_id=USER_ID)
    result = await scanner.scan()

    assert len(result) == 1
