# Campus Customs

A Yale-themed apparel storefront (React + FastAPI) with an AI shopping assistant: product browsing, accounts, and a chatbot that searches the real catalogue, checks live stock/price, and never invents data.

Built for AI Foundations for Managers, Homework 4. The full build log — every prompt, what was built, and how it was verified — is in [`AI_prompts.md`](AI_prompts.md). The complete technical reference (database, API contract, agent tools, safety rules, and specs) is in [`output/harness.md`](output/harness.md).

## Data not included

`data/campus_customs.db` and `data/products/` (the product photos) are **not** in this repo — gitignored on purpose, since the database contains seeded account data and the images are a lot of binary weight. **The app will not run without them.** If you need to run it rather than just read the code, ask for the data files separately (or see `output/app_check.html` for screenshotted proof the app runs correctly, and `output/harness.md`'s Database Field Reference for the exact schema if you're reconstructing the database yourself).

What's expected on disk if you do have the data files:
- `data/campus_customs.db` — SQLite, schema documented in `output/harness.md` (`catalogue`, `inventory`, `users`, `chat_messages`, `sessions`)
- `data/products/<product_id>.jpg` — one image per catalogue row, filename matching `catalogue.image_file_path`

## Setup

You'll need Python 3.11+, Node 18+, a [Portkey](https://portkey.ai) API key, and the data files above in place.

```bash
git clone <this-repo-url>
cd hw4   # or whatever you named it

# API key — needed by the backend
cp .env.example .env
# then edit .env and paste in a real PORTKEY_API_KEY

# Backend — venv + deps live at the repo root, alongside requirements.txt
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
# Terminal 1 — backend, from the repo root with its venv active
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2 — frontend, from frontend/
cd frontend
npm run dev
```

Open the URL Vite prints (`http://localhost:5173`).

## What's here

| Path | What it is |
|---|---|
| `backend/` | FastAPI app — `main.py` (routes), `agent.py`/`tools.py`/`models.py`/`prompts/` (the PydanticAI shopping assistant), `auth.py`/`sessions.py` (accounts) |
| `frontend/` | React + Vite + TypeScript storefront |
| `data/` | Where the SQLite database and product images go locally — not committed, see "Data not included" above |
| `output/harness.md` | The full technical reference — start here to understand how the system works |
| `output/usability.md` | Problem 9's usability-improvement menu and what was built |
| `output/design.md` | Problem 10's visual design system, sourced from Yale's official brand guidelines |
| `output/app_check.html` | Problem 11's screenshotted live-app verification — double-click to open |
| `output/audit_trail.json` | Append-only log of every agent turn (tool calls, stop reason, duration) |
| `AI_prompts.md` | The full prompt-by-prompt build log for this project |
