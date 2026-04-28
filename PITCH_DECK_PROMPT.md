# Pitch Deck — AI Slide Maker Prompt

Paste this entire prompt into Gamma, Beautiful.ai, SlidesAI, Tome, or similar.

---

Create a professional, modern investor/hackathon pitch deck for "ArmorIQ Predict" — an AI-powered autonomous prediction market trading agent with cryptographic policy enforcement. The deck should be visually striking with a dark theme (deep navy/black background with electric blue, cyan, and subtle green accents for profit/success). Use clean sans-serif typography, generous whitespace, and data-visualization style layouts. Every slide should feel like a fintech product launch, not a college project.

Include relevant icons and logos throughout: use the Polymarket logo, Polygon/MATIC logo, shield/lock icons for security, brain/AI icons for intelligence, chart/candlestick icons for trading, checkmark/approval icons for delegation flows, chain-link icons for cryptographic proofs, news/newspaper icons for research, and wallet icons for funds. Use icon sets from Phosphor Icons, Lucide, or similar modern icon libraries. Place small contextual icons next to key bullet points and section headers.

---

## SLIDE 1 — TITLE SLIDE

Title: "ArmorIQ Predict"
Subtitle: "Autonomous AI Trading Agent for Prediction Markets — With Cryptographic Guardrails"
Tagline below: "Your AI trades. Your policies decide. Every action cryptographically proven."
Visual: A sleek hero illustration showing an AI brain connected to a trading chart on one side and a shield/lock on the other. Include small Polymarket logo and ArmorIQ logo in corners. Dark gradient background with a subtle grid pattern.

---

## SLIDE 2 — THE PROBLEM

Title: "The Problem: AI Agents + Real Money = Real Risk"

Three columns with icons:

Column 1 — Icon: robot with warning sign
"Uncontrolled AI Trading"
"AI agents can execute trades without limits. One bad prompt, one hallucination, one compromised agent — your money is gone."

Column 2 — Icon: broken shield
"No Guardrails Exist"
"Current AI trading bots have no policy enforcement. No spending limits per category. No human approval for large bets. No audit trail."

Column 3 — Icon: eye with slash (no visibility)
"Zero Accountability"
"If an AI agent makes a bad trade, there's no cryptographic proof of WHY it traded, WHAT research it did, or WHO approved it."

Bottom text: "Prediction markets hit $1B+ volume in 2024. AI agents are coming to trade them. Who controls them?"

---

## SLIDE 3 — THE SOLUTION

Title: "ArmorIQ Predict: AI That Trades Within YOUR Rules"

Center visual: A flow diagram showing:
User (person icon) -> Sets Policies (shield icon) -> AI Agent (brain icon) -> Researches (newspaper icon) -> Trades (chart icon) -> Cryptographic Proof (chain-link icon)

Three key points below with icons:
1. Lock icon — "You set the rules — per category, per amount, per time of day"
2. Brain + shield icon — "AI researches and trades autonomously within those rules"
3. Chain icon — "Every action is cryptographically signed and auditable"

---

## SLIDE 4 — HOW IT WORKS (Architecture Overview)

Title: "How It Works"

Visual: A clean system architecture diagram with these components connected by arrows:

Top layer: "User / Owner" with person icon
  -> (arrow labeled "Sets Policies")
Middle layer: "ArmorIQ Policy Engine" with shield icon
  -> (arrows going to three boxes below)
Bottom layer — three boxes side by side:
  Box 1: "News MCP" with newspaper icon — "Searches news, fetches articles, scores sentiment"
  Box 2: "Polymarket MCP" with Polymarket logo — "Reads markets, fetches odds, executes trades"
  Box 3: "Analysis MCP" with chart icon — "Compares odds, assesses confidence, validates sources"

Arrow from Policy Engine labeled "Auto-approve / Hold / Deny" pointing to Polymarket MCP
Arrow from Policy Engine labeled "Delegation Request" pointing back up to User

Use the Polymarket logo, Polygon logo, and ArmorIQ shield throughout.

---

## SLIDE 5 — THE AGENT WORKFLOW (Step by Step)

Title: "From Research to Trade in 60 Seconds"

Visual: A horizontal timeline/pipeline with 6 steps, each with an icon:

Step 1 — Magnifying glass icon: "DISCOVER" — "Agent scans active Polymarket markets for opportunities"
Step 2 — Newspaper icon: "RESEARCH" — "Pulls news from 3+ sources, scores credibility and sentiment"
Step 3 — Brain icon: "ANALYZE" — "LLM assesses probability, compares with market odds, calculates edge"
Step 4 — Document with checkmark icon: "PLAN" — "Captures intent: exact market, position, amount, reasoning — cryptographically locked"
Step 5 — Shield with checkmark icon: "ENFORCE" — "ArmorIQ checks policy: auto-approve, hold for human, or deny"
Step 6 — Candlestick chart icon: "EXECUTE" — "Trade executes on Polymarket via Polygon with signed proof"

---

## SLIDE 6 — POLICY ENGINE (The Core Innovation)

Title: "Smart Policies: You Set the Rules, AI Follows Them"

Visual: A policy configuration card/panel that looks like a real product UI:

| Category | Auto-Approve | Hold | Deny |
|---|---|---|---|
| Politics | < $25 | $25-$75 | > $75 |
| Economics | < $30 | $30-$100 | > $100 |
| Sports | < $15 | $15-$40 | > $40 |
| Crypto | BLOCKED | BLOCKED | BLOCKED |
| Entertainment | < $10 | $10-$20 | > $20 |

Below the table, three icon callouts:
- Clock icon: "Time restrictions — no trading while you sleep"
- Counter icon: "Rate limits — max 25 trades/day"
- Target icon: "Risk rules — no bets above 92c or below 8c odds"

---

## SLIDE 7 — LIVE DEMO FLOW (The Money Slide)

Title: "See It In Action"

Visual: Three scenario panels side by side, styled like terminal/app notifications:

Panel 1 — Green border, checkmark icon: "AUTO-APPROVED"
"Agent buys 40 YES shares on 'Fed holds rates' at $0.42"
"Total: $16.80 | Category: Economics | Under $30 threshold"
"Executed in 1.2 seconds"

Panel 2 — Yellow/amber border, pause icon: "HELD FOR APPROVAL"
"Agent wants to buy 107 YES shares — Total: $45.00"
"Research: 3 sources, 78% confidence"
"Sent to owner -> Owner approves -> Trade executes"

Panel 3 — Red border, X icon: "BLOCKED"
"Agent attempts crypto market trade"
"Category disabled by policy"
"Agent moves on. Zero dollars lost."

---

## SLIDE 8 — CRYPTOGRAPHIC PROOF (Trust Layer)

Title: "Don't Trust. Verify."
Subtitle: "Every trade has cryptographic proof of intent"

Visual: Show a simplified proof chain with lock/chain icons:
Research Hash -> Plan Hash -> Merkle Proof -> Ed25519 Signature

Key points with icons:
- Fingerprint icon: "Intent Lock — agent can ONLY execute what was in the declared plan"
- Tree icon: "Merkle Proof — O(log n) verification that each trade was pre-approved"
- Key icon: "Ed25519 Signature — tamper-proof, server-signed, time-limited tokens"
- Eye icon: "Full Audit Trail — who traded, what, when, why, with whose approval"

---

## SLIDE 9 — APPROVAL & DELEGATION

Title: "Human-in-the-Loop When It Matters"

Visual: A mobile-style notification card:
```
ArmorIQ Predict — Approval Needed

Your agent wants to trade:

Market: "Will Fed hold rates in May?"
Position: 107 YES shares at $0.42
Total: $45.00
Category: Economics (limit: $30)

Agent's Research:
- Reuters: Fed signals pause (0.82)
- Bloomberg: Inflation cooling (0.79)
- WSJ: Labor market softening (0.74)
Confidence: 78%

   [ APPROVE ]    [ REJECT ]
```

Side callouts:
- "Owner receives delegation request with full context"
- "Research summary included so humans make informed decisions"
- "Approval is cryptographically signed — non-repudiable"

---

## SLIDE 10 — RISK MANAGEMENT

Title: "Built-In Risk Controls"

Visual: Six cards/tiles in a 2x3 grid, each with an icon:

1. Wallet icon — "Daily Spend Cap" — "$200/day hard limit across all categories"
2. Pie chart icon — "Position Limits" — "Max $50 per market, 15 open positions"
3. Trending down icon — "Stop-Loss" — "Auto-hold if selling at >20% loss"
4. Speedometer icon — "Rate Limiting" — "Max 25 trades/day, 5-min cooldown per market"
5. Clock icon — "Time Windows" — "No trading outside 8am-11pm"
6. Ban icon — "Category Blocks" — "Entirely disable categories you're not comfortable with"

---

## SLIDE 11 — TECH STACK

Title: "Built With"

Visual: A horizontal row of technology logos with labels:

Row 1 (Core):
- ArmorIQ SDK / shield icon — "Policy Enforcement & Intent Verification"
- Polymarket logo — "Prediction Market (CLOB on Polygon)"
- Polygon/MATIC logo — "Blockchain Settlement"
- Python logo — "Agent Backend"

Row 2 (AI & Data):
- Brain icon — "LLM for Research & Decision Making"
- Newspaper icon — "Real-Time News Intelligence"
- Chart icon — "Sentiment Analysis & Confidence Scoring"

Row 3 (Crypto):
- Key icon — "Ed25519 Cryptographic Signatures"
- Tree icon — "Merkle Intent Verification Proofs"
- USDC logo — "Stablecoin Settlement"

---

## SLIDE 12 — MARKET OPPORTUNITY

Title: "Why Now?"

Three big stats with icons:

Stat 1 — Chart going up icon: "$3.5B+" — "Prediction market volume in 2025" — "Polymarket alone: 500K+ monthly active traders"

Stat 2 — Robot/AI icon: "73%" — "of crypto traders want AI-assisted trading" — "But 81% don't trust fully autonomous bots"

Stat 3 — Shield icon: "$0" — "Amount spent on AI trading guardrails today" — "No product exists that solves this"

Bottom text: "The intersection of AI agents + prediction markets + policy enforcement is wide open."

---

## SLIDE 13 — USE CASES BEYOND HACKATHON

Title: "Where This Goes Next"

Four quadrant layout with icons:

1. Building/office icon — "Enterprise Trading Desks" — "Hedge funds and prop shops using AI agents with compliance-grade audit trails"
2. People/group icon — "DAO Treasury Management" — "DAOs letting AI manage treasury with on-chain policy enforcement and member approval"
3. Person icon — "Retail Power Users" — "Individuals running personal AI traders with spending limits and category controls"
4. Shield + code icon — "Platform Integration" — "Any prediction market or exchange can embed ArmorIQ as their AI safety layer"

---

## SLIDE 14 — COMPETITIVE ADVANTAGE

Title: "Why ArmorIQ Predict Wins"

Visual: Comparison table

| Feature | Raw AI Bot | Basic Limits | ArmorIQ Predict |
|---|---|---|---|
| Autonomous Trading | Yes | Yes | Yes |
| Spending Limits | No | Yes | Yes |
| Category Policies | No | No | Yes |
| Human Approval Flow | No | No | Yes |
| Crypto Intent Proof | No | No | Yes |
| Research Audit Trail | No | No | Yes |
| Merkle Verification | No | No | Yes |
| Multi-Agent Delegation | No | No | Yes |

---

## SLIDE 15 — TEAM / THANK YOU

Title: "Built by [Team Name]"
Subtitle: "ArmorIQ Predict — Autonomous AI Trading You Can Actually Trust"
Center: Team member names/photos in a row
Bottom row of logos: ArmorIQ logo, Polymarket logo, Polygon logo, Hackathon logo
Tagline: "Your AI trades. Your policies decide. Cryptographic proof for every action."
QR code or link to demo/GitHub repo

---

## DESIGN NOTES

- Color palette: Primary #0A0E27 (deep navy), Accent #00D4FF (electric cyan), Secondary #7C3AED (purple), Success #10B981 (green), Warning #F59E0B (amber), Danger #EF4444 (red)
- Typography: Inter or DM Sans for headings, JetBrains Mono for any code/technical text
- Every slide should have at least 2-3 contextual icons from Lucide or Phosphor icon sets
- Use subtle gradient overlays and glassmorphism cards
- Transitions: smooth fade or slide
- Include Polymarket, Polygon/MATIC, USDC, Python, and ArmorIQ logos/icons where contextually relevant
- Make it look like a Series A pitch deck, not a hackathon slideshow
