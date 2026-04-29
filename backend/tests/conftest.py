"""Shared fixtures for Polytrade backend tests."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.llm.base import LLMResponse, ToolCallRequest


# ---------------------------------------------------------------------------
# Database session
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db():
    """AsyncMock of ``AsyncSession`` with common result helpers."""
    session = AsyncMock()

    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=None)
    result.scalar = MagicMock(return_value=None)

    scalars = MagicMock()
    scalars.all = MagicMock(return_value=[])
    scalars.first = MagicMock(return_value=None)
    result.scalars = MagicMock(return_value=scalars)

    session.execute = AsyncMock(return_value=result)
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    session.refresh = AsyncMock()

    # Attach the result object for tests that want to customise it further.
    session._mock_result = result
    session._mock_scalars = scalars
    return session


# ---------------------------------------------------------------------------
# User fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_user():
    """A fully-onboarded user."""
    user = MagicMock()
    user.id = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    user.email = "trader@example.com"
    user.display_name = "Trader One"
    user.password_hash = "$2b$12$hashedpasswordplaceholder"
    user.role = "owner"
    user.initial_balance = Decimal("1000.00")
    user.armoriq_user_id = "armoriq-123"
    user.is_active = True
    user.onboarding_completed = True
    user.onboarding_step = 4
    user.onboarding_data = {}
    user.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    user.updated_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return user


@pytest.fixture
def mock_user_new():
    """A brand-new user who hasn't started onboarding."""
    user = MagicMock()
    user.id = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
    user.email = "new@example.com"
    user.display_name = None
    user.password_hash = "$2b$12$hashedpasswordplaceholder"
    user.role = "owner"
    user.initial_balance = Decimal("1000.00")
    user.armoriq_user_id = None
    user.is_active = True
    user.onboarding_completed = False
    user.onboarding_step = 0
    user.onboarding_data = None
    user.created_at = datetime(2025, 6, 1, tzinfo=timezone.utc)
    user.updated_at = datetime(2025, 6, 1, tzinfo=timezone.utc)
    return user


# ---------------------------------------------------------------------------
# Portfolio
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_portfolio():
    portfolio = MagicMock()
    portfolio.id = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
    portfolio.user_id = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    portfolio.balance = Decimal("1000.00")
    portfolio.total_deposited = Decimal("1000.00")
    portfolio.total_pnl = Decimal("50.00")
    portfolio.total_trades = 10
    portfolio.winning_trades = 6
    portfolio.losing_trades = 4
    portfolio.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    portfolio.updated_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return portfolio


# ---------------------------------------------------------------------------
# Market
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_market():
    market = MagicMock()
    market.id = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
    market.condition_id = "0xabcdef1234567890"
    market.question = "Will X happen by end of 2025?"
    market.description = "A test prediction market"
    market.category = "politics"
    market.slug = "will-x-happen-by-end-of-2025"
    market.yes_token_id = "token-yes-123"
    market.no_token_id = "token-no-456"
    market.yes_price = Decimal("0.650000")
    market.no_price = Decimal("0.350000")
    market.volume = Decimal("100000.00")
    market.liquidity = Decimal("50000.00")
    market.end_date = datetime(2025, 12, 31, tzinfo=timezone.utc)
    market.is_active = True
    market.resolved = False
    market.outcome = None
    market.raw_data = {}
    market.last_fetched_at = datetime(2025, 6, 1, tzinfo=timezone.utc)
    market.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    market.updated_at = datetime(2025, 6, 1, tzinfo=timezone.utc)
    return market


# ---------------------------------------------------------------------------
# Position
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_position():
    pos = MagicMock()
    pos.id = uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
    pos.user_id = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    pos.portfolio_id = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
    pos.market_id = "0xabcdef1234567890"
    pos.market_slug = "will-x-happen-by-end-of-2025"
    pos.market_question = "Will X happen by end of 2025?"
    pos.market_category = "politics"
    pos.token_id = "token-yes-123"
    pos.side = "YES"
    pos.shares = Decimal("100.0000")
    pos.avg_price = Decimal("0.600000")
    pos.cost_basis = Decimal("60.00")
    pos.current_price = Decimal("0.700000")
    pos.current_value = Decimal("70.00")
    pos.unrealized_pnl = Decimal("10.00")
    pos.status = "open"
    pos.resolved_outcome = None
    pos.realized_pnl = None
    pos.opened_at = datetime(2025, 3, 1, tzinfo=timezone.utc)
    pos.closed_at = None
    pos.created_at = datetime(2025, 3, 1, tzinfo=timezone.utc)
    pos.updated_at = datetime(2025, 3, 1, tzinfo=timezone.utc)
    return pos


# ---------------------------------------------------------------------------
# Strategy
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_strategy():
    strategy = MagicMock()
    strategy.id = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
    strategy.user_id = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    strategy.name = "Test Strategy"
    strategy.is_active = True
    strategy.priority = 0
    strategy.rules = {
        "categories": ["politics", "sports"],
        "min_confidence": 0.7,
        "min_edge": 0.05,
        "max_position_size": 50,
    }
    strategy.context = "Focus on high-confidence political events"
    strategy.created_at = datetime(2025, 2, 1, tzinfo=timezone.utc)
    strategy.updated_at = datetime(2025, 2, 1, tzinfo=timezone.utc)
    return strategy


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_policy():
    policy = MagicMock()
    policy.id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    policy.user_id = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    policy.name = "Default Policy"
    policy.is_active = True
    policy.global_rules = {
        "daily_limit": 100,
        "max_per_trade": 25,
        "auto_approve_below": 10,
    }
    policy.category_rules = {
        "politics": {"allowed": True, "max_per_trade": 20},
        "crypto": {"allowed": False},
    }
    policy.confidence_rules = {
        "min_confidence": 0.6,
        "require_multiple_sources": True,
    }
    policy.risk_rules = {
        "max_portfolio_exposure": 0.5,
        "stop_loss_threshold": 0.2,
    }
    policy.created_at = datetime(2025, 1, 15, tzinfo=timezone.utc)
    policy.updated_at = datetime(2025, 1, 15, tzinfo=timezone.utc)
    return policy


# ---------------------------------------------------------------------------
# WebSocket manager
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_ws_manager():
    manager = AsyncMock()
    manager.connect = AsyncMock()
    manager.disconnect = MagicMock()
    manager.send_to_user = AsyncMock()
    manager.broadcast = AsyncMock()
    return manager


# ---------------------------------------------------------------------------
# LLM response factory
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_llm_response():
    """Factory fixture that builds an ``LLMResponse`` with optional tool calls."""

    def _factory(
        content: str | None = "ok",
        tool_calls: list[dict] | None = None,
        model: str = "gpt-4o",
        finish_reason: str = "stop",
    ) -> LLMResponse:
        tc = []
        if tool_calls:
            for idx, call in enumerate(tool_calls):
                tc.append(
                    ToolCallRequest(
                        id=call.get("id", f"call_{idx}"),
                        name=call["name"],
                        arguments=call.get("arguments", {}),
                    )
                )
        return LLMResponse(
            content=content,
            tool_calls=tc,
            raw_response=None,
            usage={"prompt_tokens": 100, "completion_tokens": 50},
            model=model,
            finish_reason=finish_reason,
        )

    return _factory
