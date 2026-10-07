"""Database lookup tools the shopping assistant agent (agent.py) can call.

Kept self-contained (own sqlite connection, no imports from main.py) so the
agent's tools can be read and reasoned about on their own, same as HW3's
tools.py.

Intentionally only ever queries `catalogue` and `inventory`. The agent has no
tool that touches `users` or `chat_messages`, so it has no way to look up or
leak another shopper's password hash, email, or conversation history even if
asked — that boundary is structural, not just a prompt instruction.

Every tool here returns a typed model from models.py (not a raw dict), so the
agent always gets the same predictable shape back, and "not found" cases
raise ModelRetry — PydanticAI's way of telling the agent "that didn't work,
here's why" so it can react gracefully instead of silently failing or
inventing an answer.

IMPORTANT architecture note: color and garment_type are HARD filters, not
ranked/fuzzy text. An earlier version matched everything with one OR-ranked
free-text search, which meant a query like "gray hoodie" could silently
backfill with non-gray hoodies once genuine gray-hoodie matches ran out
(ranking degrades gracefully into wrong answers instead of failing loudly).
Now: if a shopper specified a color or type, every result is GUARANTEED to
match it — no partial-match fallback. Only `keywords` (team names, graphics,
occasions — things with no dedicated column) uses loose/ranked text matching.
"""

import sqlite3
from pathlib import Path

from pydantic_ai import ModelRetry

from models import ProductSearchResult, ProductStock, SizeAvailability, SizeStock

# backend/tools.py -> backend -> 4 (Homework/4, where data/ lives)
DB_PATH = Path(__file__).resolve().parents[1] / "data" / "campus_customs.db"

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

# Maps every raw catalogue.garment_type string to one shopper-facing category.
# Built from the actual distinct values in the catalogue (see AI_prompts.md) —
# update this if new garment types are added to the seed data.
CANONICAL_CATEGORY = {
    "bomber jacket": "jacket",
    "jacket": "jacket",
    "crewneck": "crewneck",
    "crewneck sweatshirt": "crewneck",
    "raglan crewneck sweatshirt": "crewneck",
    "fleece jacket": "fleece jacket",
    "full-zip fleece jacket": "fleece jacket",
    "full-zip hooded sweatshirt": "hoodie",
    "hooded pullover sweatshirt": "hoodie",
    "hooded sweatshirt": "hoodie",
    "hoodie": "hoodie",
    "pullover hoodie": "hoodie",
    "long-sleeve performance shirt": "performance shirt",
    "men's long-sleeve performance shirt": "performance shirt",
    "mockneck sweatshirt": "mockneck",
    "quarter-zip pullover": "quarter-zip",
    "quarter-zip pullover sweatshirt": "quarter-zip",
    "heavyweight short-sleeve t-shirt": "t-shirt",
    "short-sleeve crew-neck t-shirt": "t-shirt",
    "short-sleeve t-shirt": "t-shirt",
    "t-shirt": "t-shirt",
}


def _size_sort_key(size: str) -> int:
    return SIZE_ORDER.index(size) if size in SIZE_ORDER else len(SIZE_ORDER)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _normalize_text(value: str) -> str:
    """Lowercase and fold the British "grey" spelling to the catalogue's
    "gray", so matching works regardless of which spelling a shopper or the
    model uses."""
    return value.lower().replace("grey", "gray")


def canonical_category(garment_type: str) -> str:
    """Map a raw catalogue.garment_type string (or a shopper/agent-provided
    guess at one) to one shopper-facing category. Falls back to the
    normalized input itself if it's not a known raw value, so an unexpected
    string never crashes — it just won't be deduplicated with its synonyms."""
    normalized = _normalize_text(garment_type).rstrip("s")  # crude plural tolerance
    if normalized in CANONICAL_CATEGORY:
        return CANONICAL_CATEGORY[normalized]
    # maybe it's already a canonical name (e.g. "hoodie" was passed directly)
    if normalized in CANONICAL_CATEGORY.values():
        return normalized
    return normalized


def _color_matches(color_filter: str, row_colors: str) -> bool:
    return _normalize_text(color_filter) in _normalize_text(row_colors)


def _word_matches(word: str, haystack: str) -> bool:
    if word in haystack:
        return True
    if word.endswith("s") and word[:-1] in haystack:  # crude plural tolerance
        return True
    return False


def _keyword_score(keywords: str, row: sqlite3.Row) -> int:
    words = [w for w in _normalize_text(keywords).split() if w]
    haystack = " ".join(
        [row["name"].lower(), row["description"].lower(), row["search_tags"].lower()]
    )
    return sum(1 for word in words if _word_matches(word, haystack))


def _filter_rows(
    rows: list[sqlite3.Row],
    color: str | None,
    garment_type: str | None,
    min_price: float | None = None,
    max_price: float | None = None,
) -> list[sqlite3.Row]:
    """Apply the hard filters. Every row returned is GUARANTEED to match
    every filter given — no partial matches. Price bounds are applied here,
    at the same step as color/garment_type, specifically so they run BEFORE
    `search_products`'s `max_results` cap — a budget filter applied after
    truncating to 10 results could silently miss real matches past the cap."""
    result = rows
    if color:
        result = [r for r in result if _color_matches(color, r["colors"])]
    if garment_type:
        target = canonical_category(garment_type)
        result = [r for r in result if canonical_category(r["garment_type"]) == target]
    if min_price is not None:
        result = [r for r in result if r["price"] >= min_price]
    if max_price is not None:
        result = [r for r in result if r["price"] <= max_price]
    return result


def search_products(
    color: str | None = None,
    garment_type: str | None = None,
    keywords: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    max_results: int = 10,
) -> list[ProductSearchResult]:
    """Search the catalogue. `color`, `garment_type`, `min_price`, and
    `max_price` are all hard filters — every result matches every one given,
    exactly, with no partial matches. `keywords` is an optional loose text
    search (team name, graphic, occasion) layered on top, used only to
    rank/narrow within whatever the hard filters already matched.
    """
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT product_id, name, garment_type, description, colors, search_tags, price FROM catalogue"
        ).fetchall()

        matches = _filter_rows(rows, color, garment_type, min_price, max_price)

        if keywords:
            scored = [(_keyword_score(keywords, r), r) for r in matches]
            scored = [(score, r) for score, r in scored if score > 0]
            scored.sort(key=lambda pair: pair[0], reverse=True)
            matches = [r for _, r in scored]

        return [
            ProductSearchResult(
                product_id=row["product_id"],
                name=row["name"],
                garment_type=canonical_category(row["garment_type"]),
                description=row["description"],
                price=row["price"],
            )
            for row in matches[:max_results]
        ]
    finally:
        conn.close()


def list_garment_types(color: str | None = None, keywords: str | None = None) -> list[str]:
    """Return every distinct shopper-facing category among ALL products
    matching the given filters (not a capped sample). `color` is a hard
    filter; `keywords` narrows further by loose text match. Use this — not
    search_products_tool — to find out what types exist before asking a
    shopper which type they want.
    """
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT garment_type, name, description, colors, search_tags FROM catalogue"
        ).fetchall()

        matches = _filter_rows(rows, color, garment_type=None)
        if keywords:
            matches = [r for r in matches if _keyword_score(keywords, r) > 0]

        return sorted({canonical_category(r["garment_type"]) for r in matches})
    finally:
        conn.close()


def _get_product_stock(conn: sqlite3.Connection, product_id: str) -> ProductStock:
    product = conn.execute(
        "SELECT product_id, name, price FROM catalogue WHERE product_id = ?",
        (product_id,),
    ).fetchone()
    if product is None:
        raise ModelRetry(
            f"No product found with id '{product_id}'. Call search_products_tool first to find the correct product_id."
        )
    size_rows = sorted(
        conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?",
            (product_id,),
        ).fetchall(),
        key=lambda r: _size_sort_key(r["size"]),
    )
    return ProductStock(
        product_id=product["product_id"],
        name=product["name"],
        price=product["price"],
        sizes=[
            SizeStock(size=r["size"], quantity=r["quantity"], in_stock=r["quantity"] > 0)
            for r in size_rows
        ],
    )


def get_product_stock(product_id: str) -> ProductStock:
    """Look up price and the full per-size stock breakdown for one product by
    its exact catalogue ID (get this ID from search_products first)."""
    conn = _connect()
    try:
        return _get_product_stock(conn, product_id)
    finally:
        conn.close()


def get_stock_for_products(product_ids: list[str], max_products: int = 10) -> list[ProductStock]:
    """Look up full per-size stock + price for MULTIPLE products in one call —
    for a deliberate bulk request about a set of products the shopper has
    already identified as a group (e.g. "what's the stock on all of them" or
    "the sports hoodies" after seeing a list), not for resolving which ONE
    product an ambiguous singular reference means (ask the shopper for that
    instead). Unlike get_product_stock_tool, this is not subject to the
    per-turn single-product lookup cap, since it's one intentional call, not
    a loop. `product_ids` must come from an earlier search_products_tool
    result in this conversation — never invent one.
    """
    conn = _connect()
    try:
        return [_get_product_stock(conn, pid) for pid in product_ids[:max_products]]
    finally:
        conn.close()


def get_size_availability(product_id: str, size: str) -> SizeAvailability:
    """Check stock for ONE specific size of one product (e.g. "do you have
    this in Large?"). Use this when the shopper names a specific size;
    otherwise use get_product_stock_tool for the full breakdown."""
    conn = _connect()
    try:
        product = conn.execute(
            "SELECT product_id, name FROM catalogue WHERE product_id = ?",
            (product_id,),
        ).fetchone()
        if product is None:
            raise ModelRetry(
                f"No product found with id '{product_id}'. Call search_products_tool first to find the correct product_id."
            )
        size_row = conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ? AND size = ?",
            (product_id, size),
        ).fetchone()
        if size_row is None:
            raise ModelRetry(
                f"'{product_id}' has no size option called '{size}'. Call get_product_stock_tool to see which sizes exist."
            )
        return SizeAvailability(
            product_id=product["product_id"],
            name=product["name"],
            size=size_row["size"],
            quantity=size_row["quantity"],
            in_stock=size_row["quantity"] > 0,
        )
    finally:
        conn.close()
