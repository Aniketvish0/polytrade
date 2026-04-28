# ArmorIQ Predict — Polytrade

## Concept

AI-powered autonomous prediction market trading agent with cryptographic policy enforcement built on ArmorIQ SDK.

**Core idea:** User sets policies (per-category spending limits, approval thresholds, risk rules). An AI agent researches news about prediction market topics, analyzes odds, and makes trading decisions. Trades within policy auto-execute. Trades above threshold get delegated to the user for approval. Everything is cryptographically auditable.

## Why This Maps to ArmorIQ

| User Action | ArmorIQ Feature |
|---|---|
| User sets policies | ArmorIQ policy (allow/deny, amount thresholds) |
| Agent researches news | News/search MCP (read-only, no policy risk) |
| Agent decides to trade | Plan capture (intent-locked to specific market + amount) |
| Small trade within policy | Auto-executes via `invoke()` |
| Large trade / risky bet | `PolicyHoldException` -> delegation to user |
| User approves/rejects | Delegation flow -> execute or abort |
| Full audit trail | Cryptographic proof of research -> decision -> trade |

## Polymarket API

### Reading Markets (No Auth Required)
- `GET /markets` — list all active markets
- `GET /markets/{id}` — market details, current odds
- `GET /prices` — current YES/NO token prices

### Placing Trades (Requires Setup)
- Polygon wallet (EOA)
- USDC on Polygon
- Polymarket API key (generate from UI after connecting wallet)
- EIP-712 signature for orders
- `py-clob-client` library (`pip install py-clob-client`)

```python
from py_clob_client.client import ClobClient

client = ClobClient(
    host="https://clob.polymarket.com",
    key=api_key,
    chain_id=137,  # Polygon mainnet
    funder=wallet_address,
    signature_type=2,
    private_key=private_key
)

market = client.get_market("0x...")

order = client.create_and_post_order(
    OrderArgs(
        token_id="YES_TOKEN_ID",
        price=0.65,
        size=10,
        side="BUY"
    )
)
```

### No Testnet Available
- **Option A (Recommended):** Real Polymarket with tiny amounts ($1-5 per trade)
- **Option B:** Real API for reading + mock trade execution
- **Option C:** Different prediction market with testnet (e.g., Zeitgeist on Polkadot)

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                    USER                          │
│  Sets policies:                                  │
│  - "Sports: max $20/trade, auto-approve"         │
│  - "Politics: max $50/trade, approve above $25"  │
│  - "Crypto: max $10/trade, always approve"       │
│  Receives delegation requests for large trades   │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│              ARMORIQ SDK                         │
│                                                  │
│  Policy Engine:                                  │
│  ├─ Category-based amount limits                 │
│  ├─ Auto-approve below threshold                 │
│  ├─ Hold -> delegate above threshold             │
│  └─ Deny for blocked categories                  │
│                                                  │
│  Intent Verification:                            │
│  ├─ Plan: "research X, then buy YES at $0.65"    │
│  ├─ Token locks agent to this exact plan         │
│  └─ Agent can't secretly trade a different market│
└──────────────────────┬──────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
   ┌────────────┐ ┌─────────┐ ┌──────────────┐
   │ News MCP   │ │Polymarket│ │ Analysis MCP │
   │ (research) │ │  MCP     │ │ (sentiment)  │
   │            │ │ (trade)  │ │              │
   │ - search   │ │ - get    │ │ - summarize  │
   │ - fetch    │ │ - buy    │ │ - score      │
   │ - summarize│ │ - sell   │ │ - compare    │
   └────────────┘ │ - odds   │ └──────────────┘
                  └─────────┘
```

## Demo Flow

**Scene 1: User configures policies**
"For election markets, I'm comfortable with $30 auto-trades. Above $30, ask me. Never trade on crypto markets."

**Scene 2: Agent finds opportunity (auto-approved)**
Agent buys 40 YES shares on 'Fed holds rates' at $0.42. Total: $16.80 < $30 threshold. Executes automatically.

**Scene 3: Agent finds bigger opportunity (held for approval)**
Agent wants $80 trade. Held. Delegation request sent to user with research summary. User approves. Trade executes with cryptographic proof.

**Scene 4: Agent tries blocked category (denied)**
Agent attempts crypto trade. Category denied by policy. `PolicyBlockedException`. Agent moves on.

## Build Estimate

| Component | Hours | Details |
|---|---|---|
| Polymarket MCP | 3-4 hrs | Wrap py-clob-client: get_markets, get_odds, buy, sell, get_portfolio |
| News Research MCP | 2-3 hrs | Wrap a news API (NewsAPI, Tavily, or web search) |
| Agent Logic | 3-4 hrs | LLM analyzes market + news -> generates trade plan |
| ArmorIQ Integration | 2-3 hrs | Policy config, plan capture, token flow, hold/delegation |
| Simple Frontend | 3-4 hrs | Dashboard: active markets, agent recommendations, approval queue |
| Polish & Demo Prep | 2 hrs | Edge cases, demo script, fallback mocks |
| **Total** | **15-20 hrs** | |

**To cut to ~10 hrs:** Skip frontend (use CLI), mock trades, single news source.
