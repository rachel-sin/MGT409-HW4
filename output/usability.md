# Problem 9 — Usability Improvements

This file tracks Problem 9 end to end: the proposed menu of improvements below, then — as each one gets picked and built — an entry recording what was actually added and why it helps the Campus Customs shopper and/or the business. Entries move from "Proposed" to filled-in as the work happens, so this stays accurate rather than a plan written once and left stale.

## Menu (proposed — pick what to build)

### Front-end

| # | Improvement | Why it helps the shopper | Why it helps the business |
|---|---|---|---|
| F1 | **Render chat replies as formatted text, not raw markdown.** The agent already writes `**bold**` product names and `-` bulleted stock lists (confirmed in the audit log), but the chat panel renders them as a flat string — a shopper sees literal asterisks and dashes instead of a readable list. | Stock/price breakdowns for multiple products are actually legible instead of a wall of symbols. | Fewer "this looks broken" moments → more trust in the assistant, more completed chat-driven searches. |
| F2 | **Add a visible search bar + sort/filter controls to the Products page itself** (category, color, price low↔high), not chat-only. | Shoppers who don't want to type into a chatbot can still filter/search the normal way — chat stops being the only path to a smaller result set. | Lower friction for the majority of shoppers who expect a normal storefront filter bar; likely more browsing → more product page views. |
| F3 | **Show stock-level badges on product cards in the grid** ("Only 2 left", "Out of stock"), not just on the detail page. | Saves a click into a product that turns out to be sold out or almost gone. | Low-stock urgency shown earlier in the funnel nudges faster decisions (standard retail conversion lever). |
| F4 | **Real typing indicator + inline retry on chat failure**, replacing the plain "…" bubble and the dead-end "please try again" text. | Clearer feedback that the assistant is working, and a one-click way to resend instead of retyping the whole message. | Fewer abandoned chats on a transient network/model hiccup. |
| F5 | **Clickable quick-reply chips when the agent asks a clarifying question** (e.g. it lists "t-shirts, crewnecks, hoodies" — render each as a tappable chip instead of requiring the shopper to type it back). | Faster on mobile especially; zero chance of a typo breaking the agent's parsing of the answer. | Shorter path from "browsing" to "seeing relevant product cards" → fewer drop-offs mid-conversation. |

### Agent / back-end

| # | Improvement | Why it helps the shopper | Why it helps the business |
|---|---|---|---|
| B1 | **Add `min_price`/`max_price` to `search_products_tool`**, filtered at the database level. Today there's no price filter at all, and results are capped at 10 *before* any price reasoning — so "hoodies under $50" could silently miss real matches past the cap. | "Show me hoodies under $50" gets a correct, complete answer instead of an incomplete or hand-wavy one. | Budget-constrained shoppers get an answer that actually keeps them shopping, rather than one that might be wrong. |
| B2 | **Proactive low-stock callouts.** When a looked-up size has low quantity (e.g. ≤3), the prompt instructs the agent to mention it unprompted ("only 2 left in size M") instead of only answering if directly asked. | Shoppers find out about scarcity before it's too late, instead of discovering "sold out" after they decide. | Classic urgency lever, applied automatically instead of relying on the shopper to ask the right question. |
| B3 | **Zero-result / unmet-demand logging.** Capture searches that come back empty (category/color combo with no matches) into a simple aggregate, separate from the full audit log. | Indirect: a catalogue that evolves toward what people actually ask for. | Direct visibility into demand the catalogue doesn't currently serve (e.g. "40 people asked for joggers, we don't sell any") — a concrete merchandising signal, not a guess. |
| B4 | **Thumbs up/down on each assistant reply**, stored server-side with the message it rated. | Low-effort way to flag a bad/confusing answer in the moment. | Direct, structured feedback signal for iterating on the prompt/tools — far cheaper than guessing what's not working. |
| B5 | **"Welcome back" context opener for returning shoppers.** On a fresh visit (not mid-conversation), if their last session ended while browsing a product/category, the agent's first reply can reference it ("Last time you were looking at hoodies — want me to pick up there?") using data already stored in `chat_messages`/page context — no new infrastructure needed. | Picks up where they left off instead of starting cold every visit. | Lightweight re-engagement nudge that reuses existing data instead of needing a recommendation engine. |

## Implemented

Picked, with reasoning: **F1 + F3** on the front end, **B1 + B2** on the back end — chosen over the others because they were the highest payoff-to-effort items (F1 fixes an already-shipping bug, B2 is a prompt-only change with real conversion value) and because F3+B2 and B1 reinforce each other (consistent stock-urgency story end to end; B1 is reusable infrastructure if F2's filter bar gets built later). F2, B3, B4, B5 remain on the menu above for a future round.

### F1 — Render chat replies as formatted text, not raw markdown

**What I added:** `frontend/src/lib/formatChatText.tsx`, a small renderer (no new dependency, no `dangerouslySetInnerHTML`) that turns the specific markdown subset the agent actually writes — `**bold**` and `-`/`*`/`•` bullet lines — into real `<strong>`/`<ul><li>` elements, wired into `ChatWidget.tsx` in place of dumping `message.text` into a plain `<div>`. Verified live: a stock breakdown across 8 sports hoodies rendered as an actual bulleted list instead of literal `- ` characters, and the bold-parsing logic was confirmed directly against the exact regex used.

**Why it helps the shopper:** multi-product stock/price answers (the chatbot's single most information-dense reply type) are now actually readable instead of a wall of raw symbols.

**Why it helps the business:** a shopper who sees garbled-looking text reads it as "this is broken," which erodes trust in the assistant and makes them less likely to complete a chat-driven search — a cheap fix removes that friction entirely.

### F3 — Stock-level badges on grid cards

**What I added:** `ProductCard.tsx` now computes total stock across all sizes (already present in the `/api/products` response, no new API call) and shows an "Only N left" or "Out of stock" badge over the product image when total ≤ 10 or = 0, styled with the existing Yale-accent color for low-stock and a dark overlay for out-of-stock. Verified live in the browser against the real catalogue.

**Why it helps the shopper:** avoids the wasted click of opening a product that turns out to be sold out, and surfaces scarcity before they've invested any time in a product page.

**Why it helps the business:** a classic, low-effort urgency/conversion lever shown earlier in the funnel (the grid) instead of only on the detail page.

### B1 — Price filtering in `search_products_tool`

**What I added:** `min_price`/`max_price` params threaded through `tools.search_products()` → `_filter_rows()` → `search_products_tool` in `agent.py`, applied as a hard filter alongside color/garment_type — critically, *before* the `max_results` cap, not after. Before this, there was no price filter at all, and results were capped at 10 before any price reasoning could happen, so a true match past the cap could be silently missed. Verified directly: 25 t-shirts actually exist under $35, and with the real `max_results=10` the agent uses, all 10 returned are now guaranteed to satisfy the price bound (none excluded by chance, none incorrectly included). Verified end-to-end via chat: "do you have any hoodies under $60?" correctly returned only the two $45 hoodies.

**Why it helps the shopper:** budget-constrained questions ("under $50", "between $30 and $60") now get a correct, complete answer instead of one that might silently miss real matches.

**Why it helps the business:** keeps a price-sensitive shopper in the conversation with an answer they can actually trust, instead of risking an incomplete list that makes them think there's nothing in their range when there is.

### B2 — Proactive low-stock urgency phrasing

**What I added:** a new "Low-stock urgency" section in `prompts/prompt.md` instructing the agent to phrase any size with ≤3 units as urgency ("only 2 left") rather than a neutral count, whenever a stock tool already returns that figure — no new tool or schema change, prompt-only. Had to iterate once: my first draft only said to "mention" low stock, which produced no observable difference from the pre-existing grounding rule that already states exact counts ("2 in stock" read the same as "5 in stock"). Rewrote it to require urgency *phrasing*, not just disclosure, and re-verified: XL (2 left) now reads "only 2 left" while S (5) reads a plain "5 in stock," including correctly inline within a full multi-size breakdown ("XL: only 2 left, XXL: 25") and across an 8-product bulk stock answer.

**Why it helps the shopper:** scarcity is now something they'd actually notice mid-sentence, not a number they'd have to consciously compare against other sizes to realize is low.

**Why it helps the business:** applies urgency messaging automatically and consistently, rather than relying on the shopper to ask the specific question that happens to surface it.
