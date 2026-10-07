# Campus Customs

A Yale-themed apparel storefront (React + FastAPI) with an AI shopping assistant: product browsing, accounts, and a chatbot that searches the real catalogue, checks live stock/price, and never invents data.

Built for AI Foundations for Managers, Homework 4. The full build log — every prompt, what was built, and how it was verified — is in [`AI_prompts.md`](AI_prompts.md). The complete technical reference (database, API contract, agent tools, safety rules, and specs) is in [`output/harness.md`](output/harness.md).

## Setup

You'll need Python 3.11+, Node 18+, and a [Portkey](https://portkey.ai) API key.

```bash
git clone <this-repo-url>
cd campus-customs   # or whatever you named it

# API key — needed by the backend
cp .env.example .env
# then edit .env and paste in a real PORTKEY_API_KEY

# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend (separate terminal)
cd frontend
cp .env.example .env
npm install
```

## Running it

```bash
# Terminal 1 — backend, from backend/ with its venv active
uvicorn main:app --reload --port 8000

# Terminal 2 — frontend, from frontend/
npm run dev
```

Open the URL Vite prints (`http://localhost:5173`). The seeded database (`data/campus_customs.db`) already has products, inventory, and a few user accounts, so there's nothing else to set up — sign up for a new account or chat as a guest right away.

## What's here

| Path | What it is |
|---|---|
| `backend/` | FastAPI app — `main.py` (routes), `agent.py`/`tools.py`/`models.py`/`prompts/` (the PydanticAI shopping assistant), `auth.py`/`sessions.py` (accounts) |
| `frontend/` | React + Vite + TypeScript storefront |
| `data/` | The seed SQLite database and product images |
| `output/harness.md` | The full technical reference — start here to understand how the system works |
| `output/usability.md` | Problem 9's usability-improvement menu and what was built |
| `output/design.md` | Problem 10's visual design system, sourced from Yale's official brand guidelines |
| `output/app_check.html` | Problem 11's screenshotted live-app verification — double-click to open |
| `output/audit_trail.json` | Append-only log of every agent turn (tool calls, stop reason, duration) |
| `AI_prompts.md` | The full prompt-by-prompt build log for this project |
