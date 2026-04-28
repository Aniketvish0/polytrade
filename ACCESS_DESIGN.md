# Access Design: Polymarket AI Trading Agent

## 1. Role Hierarchy

```
┌─────────────────────────────────────────────┐
│                  OWNER                       │
│  (Wallet holder / account owner)             │
│  - Full control over policies                │
│  - Approve/reject any trade                  │
│  - Set/modify agent budgets                  │
│  - Withdraw funds                            │
│  - Can delegate to Manager                   │
├─────────────────────────────────────────────┤
│                 MANAGER                      │
│  (Optional — for team/fund setups)           │
│  - Approve trades within delegated limit     │
│  - Cannot modify policies                    │
│  - Cannot withdraw                           │
│  - Can approve holds up to their own limit   │
├─────────────────────────────────────────────┤
│              TRADING AGENT                   │
│  (AI — lowest privilege)                     │
│  - Research: unrestricted                    │
│  - Trade: only within policy bounds          │
│  - Cannot modify own policies                │
│  - Cannot withdraw or transfer funds         │
│  - Cannot access wallet private key          │
└─────────────────────────────────────────────┘
```

## 2. Policy Schema

```yaml
version: armor.io/v1
name: polymarket-trading-policy
description: Prediction market agent access controls

# -- Global Limits --
global:
  max_daily_spend: 200
  max_single_trade: 100
  max_open_positions: 15
  max_daily_trades: 25
  cooldown_minutes: 5
  allowed_hours: "08:00-23:00"
  allowed_days: ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

# -- Category Policies --
categories:
  politics:
    enabled: true
    auto_approve_below: 25
    hold_above: 25
    deny_above: 75
    max_daily_spend: 80

  economics:
    enabled: true
    auto_approve_below: 30
    hold_above: 30
    deny_above: 100
    max_daily_spend: 100

  sports:
    enabled: true
    auto_approve_below: 15
    hold_above: 15
    deny_above: 40
    max_daily_spend: 40

  crypto:
    enabled: false
    reason: "Too volatile, not comfortable with AI trading crypto"

  entertainment:
    enabled: true
    auto_approve_below: 10
    hold_above: 10
    deny_above: 20
    max_daily_spend: 20

  science_tech:
    enabled: true
    auto_approve_below: 20
    hold_above: 20
    deny_above: 50
    max_daily_spend: 50

  _default:
    enabled: true
    auto_approve_below: 10
    hold_above: 10
    deny_above: 30
    max_daily_spend: 30

# -- Confidence Rules --
confidence:
  min_sources: 2
  min_confidence_score: 0.65
  require_reasoning: true
  high_confidence_bonus:
    threshold: 0.85
    auto_approve_multiplier: 1.5

# -- Risk Rules --
risk:
  max_loss_per_market: 50
  max_portfolio_exposure: 500
  no_trade_if_odds_above: 0.92
  no_trade_if_odds_below: 0.08
  max_position_per_market: 50
```

## 3. Action Permission Matrix

| Action | Agent | Manager | Owner |
|---|---|---|---|
| Read markets/odds | YES | YES | YES |
| Search news | YES | YES | YES |
| Analyze sentiment | YES | YES | YES |
| Get portfolio | YES | YES | YES |
| Get trade history | YES | YES | YES |
| Buy (within policy) | YES | YES | YES |
| Buy (above threshold) | HOLD | YES* | YES |
| Buy (above deny) | DENY | DENY | YES |
| Sell existing position | YES | YES | YES |
| Sell (at loss > 20%) | HOLD | YES* | YES |
| Modify policies | DENY | DENY | YES |
| Withdraw funds | DENY | DENY | YES |
| Transfer USDC | DENY | DENY | YES |
| Export private key | DENY | DENY | DENY |
| Change wallet | DENY | DENY | YES |
| View audit logs | own | all | all |
| Pause agent | DENY | YES | YES |
| Resume agent | DENY | YES | YES |

*Manager can only approve up to their delegated limit

## 4. ArmorIQ MCP Tool Mapping

```yaml
# -- polymarket-mcp --
tools:
  # READ (no restrictions)
  get_markets:        { risk: none,   policy: allow_always }
  get_market_odds:    { risk: none,   policy: allow_always }
  get_portfolio:      { risk: none,   policy: allow_always }
  get_trade_history:  { risk: none,   policy: allow_always }
  get_balance:        { risk: none,   policy: allow_always }

  # TRADE (policy-gated)
  buy_shares:
    risk: financial
    policy: category_threshold
    params_extract:
      amount: "params.size * params.price"
      category: "params.market_category"
    enforcement:
      below_auto:  execute
      above_hold:  hold -> delegate_to_owner
      above_deny:  block

  sell_shares:
    risk: financial
    policy: allow_with_loss_check
    params_extract:
      loss_pct: "(params.buy_price - params.sell_price) / params.buy_price"
    enforcement:
      loss_below_20pct: execute
      loss_above_20pct: hold -> delegate_to_owner

  # FORBIDDEN
  withdraw:           { risk: critical, policy: deny_always }
  transfer:           { risk: critical, policy: deny_always }

# -- news-mcp --
tools:
  search_news:        { risk: none, policy: allow_always }
  fetch_article:      { risk: none, policy: allow_always }
  summarize_topic:    { risk: none, policy: allow_always }

# -- analysis-mcp --
tools:
  sentiment_score:    { risk: none, policy: allow_always }
  source_credibility: { risk: none, policy: allow_always }
  compare_odds:       { risk: none, policy: allow_always }
```

## 5. Decision Flow

```
Agent finds interesting market
         |
         v
  RESEARCH PHASE (no policy restrictions — all read-only)
  - Fetch odds
  - Search 3+ sources
  - Score sentiment
  - Assess confidence
         |
         v
  PLAN CAPTURE
  - goal: "Buy 40 YES shares on 'Fed holds rates' at $0.42"
  - evidence: 3 sources cited, confidence: 0.78
  - amount: $16.80
  - category: economics
         |
         v
  POLICY ENGINE
  1. Is category enabled? economics -> YES
  2. Check global limits (daily spend, trade count, cooldown)
  3. Check category limits (category daily spend)
  4. Check amount threshold ($16.80 < $30 auto_approve)
  5. Check risk rules (odds range, position size)
  6. Check confidence rules (sources >= 2, confidence >= 0.65)
  RESULT: AUTO-APPROVE | HOLD | DENY
         |
         v
  Token issued -> invoke() -> trade executes
```

## 6. Audit Log Structure

```json
{
  "id": "tx_a8f3k29d",
  "timestamp": "2026-04-26T14:32:18Z",
  "agent_id": "polymarket-trader-v1",
  "user_id": "aniket@armoriq.io",
  "action": "buy_shares",
  "market": "Will Fed hold rates in May 2026?",
  "market_id": "0x3f8a...",
  "category": "economics",
  "params": {
    "side": "YES",
    "shares": 40,
    "price_per_share": 0.42,
    "total": 16.80
  },
  "research": {
    "sources_consulted": 3,
    "confidence_score": 0.78,
    "reasoning_hash": "sha256:e4a2f1..."
  },
  "policy_evaluation": {
    "category_enabled": true,
    "amount_check": "auto_approved",
    "threshold": 30.00,
    "global_daily_remaining": 138.20,
    "risk_checks_passed": true
  },
  "enforcement": "auto_approved",
  "delegation_id": null,
  "intent_token": "eyJ...",
  "merkle_proof": "0xab12...",
  "plan_hash": "sha256:7c3d..."
}
```

## 7. Edge Cases

| Scenario | What Happens |
|---|---|
| Agent tries disabled category (crypto) | PolicyBlockedException — hard deny, logged |
| Agent tries 26th trade of the day | Blocked by max_daily_trades: 25 |
| Agent tries to buy at $0.95 odds | Blocked by no_trade_if_odds_above: 0.92 |
| Agent researches only 1 source | Blocked by min_sources: 2 |
| Agent tries to sell at 30% loss | Hold -> delegation to owner |
| Two trades on same market within 3 min | Blocked by cooldown_minutes: 5 |
| Daily spend hits $200 | All further trades blocked until midnight reset |
| Agent tries to withdraw USDC | deny_always — never permitted |
| Market resolves while trade is held | Delegation expires, trade cancelled |
| Owner approves but odds changed >10% | Re-evaluate at execution time, warn user |
