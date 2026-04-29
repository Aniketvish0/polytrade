"""Tests for ConsensusAnalyzer (app/agent/consensus.py)."""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agent.consensus import ConsensusAnalyzer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_market():
    m = MagicMock()
    m.condition_id = "0xabc"
    m.question = "Will X happen?"
    m.category = "politics"
    m.yes_price = Decimal("0.65")
    m.no_price = Decimal("0.35")
    return m


def _make_research():
    return {
        "current_yes_price": 0.65,
        "current_no_price": 0.35,
        "news_items": [
            {"source": "Reuters", "title": "Big event"},
            {"source": "AP", "title": "Related story"},
        ],
    }


def _make_primary_decision(action="buy_yes", confidence=0.8, edge=0.15):
    return {
        "action": action,
        "confidence": confidence,
        "edge": edge,
        "reasoning": "Strong signal from news.",
    }


def _make_mock_llm_provider(decision_args):
    """Create a mock LLM provider that returns a tool call with given arguments."""
    from app.llm.base import LLMResponse, ToolCallRequest

    response = LLMResponse(
        content=None,
        tool_calls=[ToolCallRequest(id="call_0", name="analyze_market", arguments=decision_args)],
        raw_response=None,
        usage={},
        model="test",
        finish_reason="stop",
    )
    llm = AsyncMock()
    llm.complete = AsyncMock(return_value=response)
    return llm


# ---------------------------------------------------------------------------
# returns primary_decision when < 2 providers
# ---------------------------------------------------------------------------


async def test_returns_primary_when_less_than_2_providers():
    primary = _make_primary_decision()

    with patch("app.agent.consensus.LLMRegistry") as MockReg:
        MockReg.available.return_value = ["openai"]  # only 1 provider

        analyzer = ConsensusAnalyzer()
        result = await analyzer.check_consensus(
            _make_market(), _make_research(), primary
        )

    assert result == primary


# ---------------------------------------------------------------------------
# consensus reached — 2/3 agree
# ---------------------------------------------------------------------------


async def test_consensus_reached_averaged_confidence():
    primary = _make_primary_decision(action="buy_yes", confidence=0.8)

    # Two providers agree with buy_yes
    llm_agree_1 = _make_mock_llm_provider({"action": "buy_yes", "confidence": 0.9})
    llm_agree_2 = _make_mock_llm_provider({"action": "buy_yes", "confidence": 0.7})
    llm_disagree = _make_mock_llm_provider({"action": "pass", "confidence": 0.3})

    with patch("app.agent.consensus.LLMRegistry") as MockReg:
        MockReg.available.return_value = ["openai", "anthropic", "gemini"]
        MockReg.get.side_effect = lambda name: {
            "openai": llm_agree_1,
            "anthropic": llm_agree_2,
            "gemini": llm_disagree,
        }[name]

        analyzer = ConsensusAnalyzer()
        result = await analyzer.check_consensus(
            _make_market(), _make_research(), primary
        )

    assert result is not None
    assert result["consensus"] is True
    # Average confidence of the two agreeing: (0.9 + 0.7) / 2 = 0.8
    assert result["confidence"] == pytest.approx(0.8, abs=0.01)


# ---------------------------------------------------------------------------
# consensus not reached
# ---------------------------------------------------------------------------


async def test_consensus_not_reached_returns_none():
    primary = _make_primary_decision(action="buy_yes", confidence=0.8)

    # Only 1 out of 3 agrees
    llm_agree = _make_mock_llm_provider({"action": "buy_yes", "confidence": 0.7})
    llm_disagree_1 = _make_mock_llm_provider({"action": "pass", "confidence": 0.3})
    llm_disagree_2 = _make_mock_llm_provider({"action": "buy_no", "confidence": 0.6})

    with patch("app.agent.consensus.LLMRegistry") as MockReg:
        MockReg.available.return_value = ["openai", "anthropic", "gemini"]
        MockReg.get.side_effect = lambda name: {
            "openai": llm_agree,
            "anthropic": llm_disagree_1,
            "gemini": llm_disagree_2,
        }[name]

        analyzer = ConsensusAnalyzer()
        result = await analyzer.check_consensus(
            _make_market(), _make_research(), primary
        )

    assert result is None


# ---------------------------------------------------------------------------
# handles provider query failure gracefully
# ---------------------------------------------------------------------------


async def test_handles_provider_failure_gracefully():
    primary = _make_primary_decision(action="buy_yes", confidence=0.8)

    llm_ok = _make_mock_llm_provider({"action": "buy_yes", "confidence": 0.85})
    llm_fail = AsyncMock()
    llm_fail.complete = AsyncMock(side_effect=RuntimeError("Provider crashed"))

    with patch("app.agent.consensus.LLMRegistry") as MockReg:
        MockReg.available.return_value = ["openai", "anthropic", "gemini"]
        MockReg.get.side_effect = lambda name: {
            "openai": llm_ok,
            "anthropic": llm_fail,
            "gemini": llm_ok,
        }[name]

        analyzer = ConsensusAnalyzer()
        # Should not raise — failed provider is just skipped
        result = await analyzer.check_consensus(
            _make_market(), _make_research(), primary
        )

    # 2 providers succeeded and both agree, so consensus should be reached
    assert result is not None
    assert result["consensus"] is True


# ---------------------------------------------------------------------------
# consensus_detail includes agreed/disagreed providers
# ---------------------------------------------------------------------------


async def test_consensus_detail_includes_agreed_disagreed():
    primary = _make_primary_decision(action="buy_yes", confidence=0.8)

    llm_agree = _make_mock_llm_provider({"action": "buy_yes", "confidence": 0.85})
    llm_disagree = _make_mock_llm_provider({"action": "pass", "confidence": 0.3})

    with patch("app.agent.consensus.LLMRegistry") as MockReg:
        MockReg.available.return_value = ["openai", "anthropic", "gemini"]
        MockReg.get.side_effect = lambda name: {
            "openai": llm_agree,
            "anthropic": llm_agree,
            "gemini": llm_disagree,
        }[name]

        analyzer = ConsensusAnalyzer()
        result = await analyzer.check_consensus(
            _make_market(), _make_research(), primary
        )

    assert "consensus_detail" in result
    detail = result["consensus_detail"]
    assert "agreed" in detail
    assert "disagreed" in detail
    assert len(detail["agreed"]) == 2
    assert len(detail["disagreed"]) == 1


# ---------------------------------------------------------------------------
# reasoning includes consensus count
# ---------------------------------------------------------------------------


async def test_reasoning_includes_consensus_count():
    primary = _make_primary_decision(action="buy_yes", confidence=0.8)

    llm_agree = _make_mock_llm_provider({"action": "buy_yes", "confidence": 0.85})

    with patch("app.agent.consensus.LLMRegistry") as MockReg:
        MockReg.available.return_value = ["openai", "anthropic"]
        MockReg.get.side_effect = lambda name: {
            "openai": llm_agree,
            "anthropic": llm_agree,
        }[name]

        analyzer = ConsensusAnalyzer()
        result = await analyzer.check_consensus(
            _make_market(), _make_research(), primary
        )

    assert "Consensus:" in result["reasoning"]
    assert "2/" in result["reasoning"]
