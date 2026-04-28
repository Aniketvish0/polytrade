# Polytrade — ArmorIQ Predict

AI-powered simulated prediction market trading agent with ArmorIQ policy enforcement.

## Architecture

- **Backend**: Python 3.11+ / FastAPI / SQLAlchemy async / PostgreSQL
- **Frontend**: React 18 / TypeScript / Vite / Tailwind / Zustand
- **LLM**: Multi-provider (Claude, GPT, Gemini) via `app/llm/` abstraction
- **Policy**: ArmorIQ SDK (`armoriq-sdk` pip package)
- **Market Data**: Polymarket Gamma API (REST polling every 30s)

## Quick Start

```bash
# Start PostgreSQL
cd backend && docker-compose up -d

# Backend
cd backend && pip install -e . && alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev
```

## Key Directories

- `backend/app/agent/` — Autonomous trading loop (scan → research → analyze → trade)
- `backend/app/armoriq/` — ArmorIQ SDK integration (enforcement, policy mapping)
- `backend/app/llm/` — Multi-LLM abstraction (providers/, prompts/, tools.py)
- `backend/app/trading/` — Simulated trading engine (buy/sell/P&L/settlement)
- `backend/app/nlp/` — NLP command parser (slash commands + natural language)
- `frontend/src/components/terminal/` — Bloomberg-style chat terminal
- `frontend/src/components/dashboard/` — Portfolio, trades, news panels
- `frontend/src/stores/` — Zustand state management (9 stores)

## ArmorIQ Integration

ArmorIQ is the core differentiator. Every trade flows through `app/armoriq/enforcement.py`:
- Auto-approve below threshold → immediate execution
- Hold above threshold → delegation to user for approval
- Deny above max → blocked completely

Uses ArmorIQ Session API: `start_plan()` → `check()` → `report()`

## Environment Variables

See `backend/.env.example` for all required variables.
At minimum: DATABASE_URL, at least one LLM API key, ARMORIQ_API_KEY.
