# AI Prompts — Homework 4

## Problem 1 — Vibe Coder Prompts

### Prompts used

1. > hi claude lets work on hw 4
   >
   > work in the homework 4 folder from here on out
2. > first lets make AI_prompts.md. look at how its structured for homework 2 and copy that. it should keep a log of all my prompts for this hw and include whats in the image. making this md file is problem 1: vibe coder prompts
   >
   > [Screenshot of assignment instructions]: "Put one section for each problem. Each section must include: the problem number and title; at least one prompt you typed, in your own words as much as possible; one follow-up prompt if needed (and one sentence on what was lacking after the first)."

### Follow-up summary

After the initial request to start Homework 4 and work in the Homework 4 folder, I was asked to create `AI_prompts.md`, modeled on the Homework 2 version, that logs prompts for this assignment and follows the formatting rules shown in the screenshot (problem number/title, at least one prompt in the student's own words, and a follow-up prompt plus one sentence on what was missing after the first). What was lacking after the first prompt was the specific file structure/format to use, which the screenshot and the Homework 2 example provided.

## Problem 2 — Analyze the Database

### Prompts used

1. > ok problem 2 is called analyze the database. tell me about the data/campus_customs.db - what are the fields? i specifically want to undersatnd catalogue, inventory, and users

### Follow-up summary

- "can you tell me about these fields in conversational terms" — needed because the first answer was a dry, technical schema listing rather than a plain-language explanation.
- "you can log it as a follow up" — needed to have the conversational-terms exchange captured in this log, since logging isn't automatic.
- "this is still part of problem 2. start the file output/harness.md. make a table of all the fields (column 1) and a one liner on why each fields matters (column 2). show me the table after you make it" — needed a written deliverable (not just chat output) summarizing why each field matters, saved to `output/harness.md`.
- "sorry not all the fields; do it for each table. and yes, for all prompts, log them in the ai_prompts.md file as either the original prompt or the follow-up prompts. the ai_prompts.md file should include my original prompt for each problem, a summary of all the followup prompts and why i needed them" — needed because the first harness.md draft merged all fields into one table instead of a separate table per database table, and clarified the ongoing logging format for this file going forward (original prompt + summary of all follow-ups and why each was needed).

## Problem 3 — Build the Campus Customs Website

### Prompts used

1. > called "build the campus customs website". i want to make a react + vite + typescript front end for campus customs (a shop that makes merch for yale). the end state we're making is a customer website with a helpful chatbot. not for this problem, but we'll make a python fastapi backend later that uses a pydantic ai agent brain. put a nav bar at the top that links to the main pages: home, products, about us, log in, and create account. look at the image for wording guidance
   >
   > [Screenshot]: "first. Pull Campus Customs–style wording from yalebulldogblue.com for Home and About Us, but write these pages in your own voice (do not copy the original site text)."

### Follow-up summary

No follow-ups were needed. The original prompt was specific enough to scaffold the React + Vite + TypeScript frontend in `frontend/`, pull tone/theme guidance from yalebulldogblue.com (without copying its text), write original Home and About Us copy, build a nav bar linking to Home/Products/About Us/Log In/Create Account, and add stub Products/Login/Create Account pages since those depend on the database and backend work planned for later problems.

### Follow-up: Products page + product detail page

1. > On the Products page, show product images from the catalogue (use the image paths in the database) with basic product info (name, price, short description). do the above + make each prod open a single-item page, large image on one side, full product text on the others - description, price, sizes/stock when you have them. clikgin a card on products will take the shopper there. feel free to take inspiration from here [Old Navy product page link]

What was lacking after the first prompt (which only asked for images + basic info in the grid) was a way to see full product detail — the follow-up added the requirement for a per-product detail page (large image, full description, price, colors, size/stock) reached by clicking a product card, modeled loosely on an Old Navy PDP layout. To serve the images/data without the backend (which comes later), I added `scripts/export_products.py` to export `catalogue` + `inventory` from `data/campus_customs.db` into `frontend/src/data/products.json` and copy the product images into `frontend/public/products/`.

### Follow-up: Chat widget stub + FastAPI backend

1. > Add a chat interface in the bottom right of the site (a floating chat panel is fine). It does not need to talk to an agent yet — a stub that will call your backend later is enough for this problem.
   >
   > You will need a small API soon to read the database. It is fine to start a simple FastAPI app in backend/main.py just to serve products and images, then grow it into the agent backend in Problem 5.
   >
   > do this too (still p3)

### Follow-up summary

This picked up directly from the previous follow-up (no gap/lacking info) — it asked for two more additions within Problem 3: a floating chat widget (bottom-right, UI-only stub that doesn't call an agent yet) and a real FastAPI backend (`backend/main.py`) to serve the catalogue/inventory data and product images over HTTP. Since the backend now serves this data directly from the database, I replaced the earlier static `products.json`/export-script approach with real `fetch` calls from the frontend (`frontend/src/lib/api.ts`) to `GET /api/products` and `GET /api/products/{id}`, and deleted `scripts/export_products.py`, `frontend/src/data/`, and the copied images in `frontend/public/products/` since they were now redundant. Verified end-to-end in the browser: product grid and detail pages load from `localhost:8000` (confirmed via network requests), and the chat widget opens, accepts a message, and returns its stub reply.
