"""Tests for OnboardingEngine (app/nlp/onboarding.py)."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.nlp.onboarding import AVAILABLE_CATEGORIES, OnboardingEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(step=0, data=None):
    user = MagicMock()
    user.id = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
    user.onboarding_step = step
    user.onboarding_data = data or {}
    return user


def _make_mock_llm(response):
    llm = AsyncMock()
    llm.complete = AsyncMock(return_value=response)
    return llm


# ---------------------------------------------------------------------------
# Step 0 — welcome
# ---------------------------------------------------------------------------


async def test_step_0_returns_welcome_and_sets_step_1(mock_db, mock_llm_response):
    user = _make_user(step=0)
    engine = OnboardingEngine(db=mock_db, user=user)
    result = await engine.process_step("hello")

    assert result["type"] == "chat"
    assert "Welcome" in result["content"]
    assert result["message_type"] == "onboarding_step"
    assert result["data"]["step"] == 1
    assert user.onboarding_step == 1


# ---------------------------------------------------------------------------
# Step 1 — categories (LLM extraction)
# ---------------------------------------------------------------------------


async def test_step_1_categories_llm_extraction(mock_db, mock_llm_response):
    user = _make_user(step=1)
    resp = mock_llm_response(
        tool_calls=[{
            "name": "extract_categories",
            "arguments": {
                "categories": ["politics", "crypto"],
                "excluded_categories": ["sports"],
                "response": "Great, politics and crypto it is!",
            },
        }]
    )
    llm = _make_mock_llm(resp)

    with patch("app.llm.registry.LLMRegistry.get", return_value=llm):
        engine = OnboardingEngine(db=mock_db, user=user)
        result = await engine.process_step("I like politics and crypto")

    assert user.onboarding_step == 2
    assert result["data"]["categories"] == ["politics", "crypto"]
    assert "politics and crypto" in result["content"]


# ---------------------------------------------------------------------------
# Step 1 — fallback when LLM fails
# ---------------------------------------------------------------------------


async def test_step_1_fallback_uses_all_categories(mock_db):
    user = _make_user(step=1)
    llm = AsyncMock()
    llm.complete = AsyncMock(side_effect=RuntimeError("LLM down"))

    with patch("app.llm.registry.LLMRegistry.get", return_value=llm):
        engine = OnboardingEngine(db=mock_db, user=user)
        result = await engine.process_step("some message")

    assert user.onboarding_step == 2
    assert user.onboarding_data["categories"] == AVAILABLE_CATEGORIES
    assert "all categories" in result["content"]


# ---------------------------------------------------------------------------
# Step 2 — risk (LLM extraction)
# ---------------------------------------------------------------------------


async def test_step_2_risk_llm_extraction(mock_db, mock_llm_response):
    user = _make_user(step=2, data={"categories": ["politics"]})
    resp = mock_llm_response(
        tool_calls=[{
            "name": "extract_risk_params",
            "arguments": {
                "daily_limit": 100,
                "max_per_trade": 20,
                "auto_approve_below": 10,
                "min_confidence": 0.7,
                "response": "Set your limits to $100/day.",
            },
        }]
    )
    llm = _make_mock_llm(resp)

    with patch("app.llm.registry.LLMRegistry.get", return_value=llm):
        engine = OnboardingEngine(db=mock_db, user=user)
        result = await engine.process_step("$100 daily, $20 per trade")

    assert user.onboarding_step == 3
    assert user.onboarding_data["daily_limit"] == 100
    assert user.onboarding_data["max_per_trade"] == 20
    assert result["data"]["risk_params"]["daily_limit"] == 100


# ---------------------------------------------------------------------------
# Step 2 — fallback uses defaults
# ---------------------------------------------------------------------------


async def test_step_2_fallback_uses_defaults(mock_db):
    user = _make_user(step=2, data={"categories": ["politics"]})
    llm = AsyncMock()
    llm.complete = AsyncMock(side_effect=RuntimeError("LLM down"))

    with patch("app.llm.registry.LLMRegistry.get", return_value=llm):
        engine = OnboardingEngine(db=mock_db, user=user)
        result = await engine.process_step("use defaults")

    assert user.onboarding_step == 3
    assert user.onboarding_data["daily_limit"] == 50
    assert user.onboarding_data["max_per_trade"] == 10
    assert user.onboarding_data["auto_approve_below"] == 5
    assert user.onboarding_data["min_confidence"] == 0.6


# ---------------------------------------------------------------------------
# Step 3 — strategy returns complete_onboarding action
# ---------------------------------------------------------------------------


async def test_step_3_returns_complete_onboarding_action(mock_db, mock_llm_response):
    user = _make_user(
        step=3,
        data={
            "categories": ["politics", "sports"],
            "daily_limit": 50,
            "max_per_trade": 10,
            "auto_approve_below": 5,
            "min_confidence": 0.6,
        },
    )
    resp = mock_llm_response(
        tool_calls=[{
            "name": "create_strategy_from_nl",
            "arguments": {
                "name": "Political Focus",
                "context": "Focus on US politics",
                "rules": {"categories": ["politics"]},
                "response": "Created your Political Focus strategy!",
            },
        }]
    )
    llm = _make_mock_llm(resp)

    with patch("app.llm.registry.LLMRegistry.get", return_value=llm):
        engine = OnboardingEngine(db=mock_db, user=user)
        result = await engine.process_step("Focus on politics")

    assert result["action"]["type"] == "complete_onboarding"
    assert result["data"]["step"] == 4


# ---------------------------------------------------------------------------
# Step 3 — includes strategy and policy data
# ---------------------------------------------------------------------------


async def test_step_3_includes_strategy_and_policy_data(mock_db, mock_llm_response):
    user = _make_user(
        step=3,
        data={
            "categories": ["politics", "crypto"],
            "daily_limit": 80,
            "max_per_trade": 15,
            "auto_approve_below": 8,
            "min_confidence": 0.7,
        },
    )
    resp = mock_llm_response(
        tool_calls=[{
            "name": "create_strategy_from_nl",
            "arguments": {
                "name": "My Strategy",
                "context": "Aggressive trading",
                "rules": {},
                "response": "Done!",
            },
        }]
    )
    llm = _make_mock_llm(resp)

    with patch("app.llm.registry.LLMRegistry.get", return_value=llm):
        engine = OnboardingEngine(db=mock_db, user=user)
        result = await engine.process_step("be aggressive")

    action_data = result["action"]["data"]

    # Strategy data
    assert action_data["strategy"]["name"] == "My Strategy"
    assert action_data["strategy"]["context"] == "Aggressive trading"

    # Policy data
    assert action_data["policy"]["global_rules"]["daily_limit"] == 80
    assert action_data["policy"]["global_rules"]["max_per_trade"] == 15
    assert action_data["policy"]["confidence_rules"]["min_confidence"] == 0.7


# ---------------------------------------------------------------------------
# Step 3 — fallback when LLM fails
# ---------------------------------------------------------------------------


async def test_step_3_fallback_when_llm_fails(mock_db):
    user = _make_user(
        step=3,
        data={
            "categories": ["politics"],
            "daily_limit": 50,
            "max_per_trade": 10,
            "auto_approve_below": 5,
            "min_confidence": 0.6,
        },
    )
    llm = AsyncMock()
    llm.complete = AsyncMock(side_effect=RuntimeError("LLM down"))

    with patch("app.llm.registry.LLMRegistry.get", return_value=llm):
        engine = OnboardingEngine(db=mock_db, user=user)
        result = await engine.process_step("whatever")

    assert result["action"]["type"] == "complete_onboarding"
    assert result["action"]["data"]["strategy"]["name"] == "My Strategy"


# ---------------------------------------------------------------------------
# Step 3 — categories from data are included in rules
# ---------------------------------------------------------------------------


async def test_step_3_categories_from_data_in_rules(mock_db, mock_llm_response):
    user = _make_user(
        step=3,
        data={
            "categories": ["crypto", "entertainment"],
            "daily_limit": 50,
            "max_per_trade": 10,
            "auto_approve_below": 5,
            "min_confidence": 0.6,
        },
    )
    # LLM returns rules without categories — should be filled from data
    resp = mock_llm_response(
        tool_calls=[{
            "name": "create_strategy_from_nl",
            "arguments": {
                "name": "Crypto Fun",
                "context": "crypto stuff",
                "rules": {},  # no categories key
                "response": "Done!",
            },
        }]
    )
    llm = _make_mock_llm(resp)

    with patch("app.llm.registry.LLMRegistry.get", return_value=llm):
        engine = OnboardingEngine(db=mock_db, user=user)
        result = await engine.process_step("crypto and entertainment")

    strategy_rules = result["action"]["data"]["strategy"]["rules"]
    assert strategy_rules["categories"] == ["crypto", "entertainment"]

    # Policy category rules should also have entries for each category
    policy_cats = result["action"]["data"]["policy"]["category_rules"]
    assert "crypto" in policy_cats
    assert "entertainment" in policy_cats


# ---------------------------------------------------------------------------
# Step > 3 — resets to welcome
# ---------------------------------------------------------------------------


async def test_step_above_3_returns_welcome(mock_db):
    user = _make_user(step=5)
    engine = OnboardingEngine(db=mock_db, user=user)
    result = await engine.process_step("hi")

    assert "Welcome" in result["content"]
    assert user.onboarding_step == 1


# ---------------------------------------------------------------------------
# QA-level tests — full flows, cross-step persistence, user-facing behavior
# ---------------------------------------------------------------------------


async def test_full_onboarding_flow_step_0_through_3(mock_db, mock_llm_response):
    """Walk through all 4 steps on the same user, verifying data accumulates."""
    user = _make_user(step=0)
    engine = OnboardingEngine(db=mock_db, user=user)

    # Step 0 -> 1: welcome
    result_0 = await engine.process_step("hello")
    assert user.onboarding_step == 1
    assert "Welcome" in result_0["content"]

    # Step 1 -> 2: categories
    cat_resp = mock_llm_response(
        tool_calls=[{
            "name": "extract_categories",
            "arguments": {
                "categories": ["politics", "crypto"],
                "excluded_categories": [],
                "response": "Politics and crypto selected!",
            },
        }]
    )
    cat_llm = _make_mock_llm(cat_resp)
    with patch("app.llm.registry.LLMRegistry.get", return_value=cat_llm):
        result_1 = await engine.process_step("I like politics and crypto")

    assert user.onboarding_step == 2
    assert user.onboarding_data["categories"] == ["politics", "crypto"]

    # Step 2 -> 3: risk
    risk_resp = mock_llm_response(
        tool_calls=[{
            "name": "extract_risk_params",
            "arguments": {
                "daily_limit": 100,
                "max_per_trade": 25,
                "auto_approve_below": 10,
                "min_confidence": 0.8,
                "response": "Set to $100/day.",
            },
        }]
    )
    risk_llm = _make_mock_llm(risk_resp)
    with patch("app.llm.registry.LLMRegistry.get", return_value=risk_llm):
        result_2 = await engine.process_step("$100 daily, $25 per trade")

    assert user.onboarding_step == 3
    assert user.onboarding_data["daily_limit"] == 100
    assert user.onboarding_data["max_per_trade"] == 25

    # Step 3 -> complete: strategy
    strat_resp = mock_llm_response(
        tool_calls=[{
            "name": "create_strategy_from_nl",
            "arguments": {
                "name": "Political Trader",
                "context": "Focus on politics",
                "rules": {},
                "response": "Created your strategy!",
            },
        }]
    )
    strat_llm = _make_mock_llm(strat_resp)
    with patch("app.llm.registry.LLMRegistry.get", return_value=strat_llm):
        result_3 = await engine.process_step("Focus on politics")

    assert result_3["action"]["type"] == "complete_onboarding"
    assert result_3["data"]["step"] == 4

    # Verify the accumulated data flows into the final action
    action_data = result_3["action"]["data"]
    assert action_data["strategy"]["name"] == "Political Trader"
    assert action_data["policy"]["global_rules"]["daily_limit"] == 100
    assert action_data["policy"]["global_rules"]["max_per_trade"] == 25
    assert action_data["policy"]["confidence_rules"]["min_confidence"] == 0.8


async def test_onboarding_step_data_persists_across_steps(mock_db, mock_llm_response):
    """Categories chosen in step 1 appear in the policy created at step 3."""
    user = _make_user(step=1)
    chosen_categories = ["science", "technology", "business"]

    # Step 1: pick categories
    cat_resp = mock_llm_response(
        tool_calls=[{
            "name": "extract_categories",
            "arguments": {
                "categories": chosen_categories,
                "excluded_categories": [],
                "response": "Science, tech, and business!",
            },
        }]
    )
    with patch("app.llm.registry.LLMRegistry.get", return_value=_make_mock_llm(cat_resp)):
        engine = OnboardingEngine(db=mock_db, user=user)
        await engine.process_step("science, technology, business")

    # Step 2: set risk
    risk_resp = mock_llm_response(
        tool_calls=[{
            "name": "extract_risk_params",
            "arguments": {
                "daily_limit": 75,
                "max_per_trade": 15,
                "auto_approve_below": 8,
                "min_confidence": 0.7,
                "response": "Done!",
            },
        }]
    )
    with patch("app.llm.registry.LLMRegistry.get", return_value=_make_mock_llm(risk_resp)):
        await engine.process_step("$75 daily")

    # Step 3: create strategy — verify categories from step 1 persist
    strat_resp = mock_llm_response(
        tool_calls=[{
            "name": "create_strategy_from_nl",
            "arguments": {
                "name": "Tech Trader",
                "context": "tech focus",
                "rules": {},
                "response": "Done!",
            },
        }]
    )
    with patch("app.llm.registry.LLMRegistry.get", return_value=_make_mock_llm(strat_resp)):
        result = await engine.process_step("tech focused")

    action_data = result["action"]["data"]

    # Categories from step 1 must appear in strategy rules
    assert action_data["strategy"]["rules"]["categories"] == chosen_categories

    # Categories from step 1 must appear as keys in policy category_rules
    for cat in chosen_categories:
        assert cat in action_data["policy"]["category_rules"]


async def test_risk_defaults_produce_valid_policy(mock_db, mock_llm_response):
    """When user says 'use defaults', fallback values (50, 10, 5, 0.6) produce a valid policy."""
    user = _make_user(step=2, data={"categories": ["politics"]})
    llm = AsyncMock()
    llm.complete = AsyncMock(side_effect=RuntimeError("LLM down"))

    with patch("app.llm.registry.LLMRegistry.get", return_value=llm):
        engine = OnboardingEngine(db=mock_db, user=user)
        await engine.process_step("use defaults")

    # Defaults are now stored
    assert user.onboarding_data["daily_limit"] == 50
    assert user.onboarding_data["max_per_trade"] == 10
    assert user.onboarding_data["auto_approve_below"] == 5
    assert user.onboarding_data["min_confidence"] == 0.6

    # Now complete step 3 and verify defaults carry into a valid policy
    strat_resp = mock_llm_response(
        tool_calls=[{
            "name": "create_strategy_from_nl",
            "arguments": {
                "name": "Default Strat",
                "context": "defaults",
                "rules": {},
                "response": "Done!",
            },
        }]
    )
    with patch("app.llm.registry.LLMRegistry.get", return_value=_make_mock_llm(strat_resp)):
        result = await engine.process_step("just go")

    action_data = result["action"]["data"]
    policy = action_data["policy"]
    assert policy["global_rules"]["daily_limit"] == 50
    assert policy["global_rules"]["max_per_trade"] == 10
    assert policy["confidence_rules"]["min_confidence"] == 0.6
    # Each category gets an auto_approve_below entry
    for cat_rules in policy["category_rules"].values():
        assert cat_rules["auto_approve_below"] == 5
        assert cat_rules["enabled"] is True


async def test_step_transitions_cannot_skip_from_step_1_to_step_3(mock_db, mock_llm_response):
    """User at step 1 processes a message and goes to step 2, not step 3."""
    user = _make_user(step=1)

    cat_resp = mock_llm_response(
        tool_calls=[{
            "name": "extract_categories",
            "arguments": {
                "categories": ["sports"],
                "excluded_categories": [],
                "response": "Sports it is!",
            },
        }]
    )
    with patch("app.llm.registry.LLMRegistry.get", return_value=_make_mock_llm(cat_resp)):
        engine = OnboardingEngine(db=mock_db, user=user)
        result = await engine.process_step("sports only")

    # Must go to step 2, not step 3
    assert user.onboarding_step == 2
    assert result["data"]["step"] == 2
    assert result["data"]["step_name"] == "risk"


async def test_each_step_response_includes_next_step_guidance(mock_db, mock_llm_response):
    """Each step's response content contains clear prompts for what to do next."""
    user = _make_user(step=0)
    engine = OnboardingEngine(db=mock_db, user=user)

    # Step 0 -> 1: should prompt about categories
    result_0 = await engine.process_step("hi")
    assert "Step 1/3" in result_0["content"]
    assert "categories" in result_0["content"].lower()

    # Step 1 -> 2: should prompt about risk
    cat_resp = mock_llm_response(
        tool_calls=[{
            "name": "extract_categories",
            "arguments": {
                "categories": ["politics"],
                "excluded_categories": [],
                "response": "Politics!",
            },
        }]
    )
    with patch("app.llm.registry.LLMRegistry.get", return_value=_make_mock_llm(cat_resp)):
        result_1 = await engine.process_step("politics")

    assert "Step 2/3" in result_1["content"]
    assert "risk" in result_1["content"].lower() or "limit" in result_1["content"].lower()

    # Step 2 -> 3: should prompt about strategy
    risk_resp = mock_llm_response(
        tool_calls=[{
            "name": "extract_risk_params",
            "arguments": {
                "daily_limit": 50,
                "max_per_trade": 10,
                "auto_approve_below": 5,
                "min_confidence": 0.6,
                "response": "Defaults!",
            },
        }]
    )
    with patch("app.llm.registry.LLMRegistry.get", return_value=_make_mock_llm(risk_resp)):
        result_2 = await engine.process_step("defaults")

    assert "Step 3/3" in result_2["content"]
    assert "strategy" in result_2["content"].lower() or "approach" in result_2["content"].lower()

    # Step 3 -> complete: should tell user setup is done
    strat_resp = mock_llm_response(
        tool_calls=[{
            "name": "create_strategy_from_nl",
            "arguments": {
                "name": "Test",
                "context": "test",
                "rules": {},
                "response": "Done!",
            },
        }]
    )
    with patch("app.llm.registry.LLMRegistry.get", return_value=_make_mock_llm(strat_resp)):
        result_3 = await engine.process_step("go conservative")

    assert "Complete" in result_3["content"] or "complete" in result_3["content"]
