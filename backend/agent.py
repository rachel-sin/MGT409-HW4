"""Campus Customs shopping assistant — a PydanticAI agent with product-lookup tools.

The chat route in backend/main.py imports run_chat() and handles persistence
(chat_messages table) and auth context; this file only knows how to answer
one turn of conversation.
"""

import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.messages import ModelMessage, RetryPromptPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from models import ChatReply, ProductSearchResult, ProductStock, ShopperContext, SizeAvailability
from tools import (
    get_product_stock,
    get_size_availability,
    get_stock_for_products,
    list_garment_types,
    search_products,
)

# backend/agent.py -> backend -> 4 -> Homework -> course root (.env lives here)
ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(ENV_PATH)

PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY")
if not PORTKEY_API_KEY:
    raise RuntimeError(f"PORTKEY_API_KEY not found — expected it in {ENV_PATH}")

# Built as an explicit client (not os.environ) so the key only ever flows
# into this one client, never the wider process environment, and is never
# printed or persisted anywhere. A request timeout + capped retries stop a
# slow or flaky upstream from hanging a chat request indefinitely or
# silently burning retried calls.
openai_client = AsyncOpenAI(
    api_key=PORTKEY_API_KEY,
    base_url="https://api.portkey.ai/v1",
    timeout=20.0,
    max_retries=1,
)
model = OpenAIChatModel("gpt-5.6-luna", provider=OpenAIProvider(openai_client=openai_client))

SYSTEM_PROMPT = (Path(__file__).resolve().parent / "prompts" / "prompt.md").read_text()


@dataclass
class ChatDeps:
    """Per-turn state, reset at the start of every run_chat() call — NOT
    shared across requests, and NOT sent to the model as text. This is
    PydanticAI's mechanism for giving tools access to request-scoped data
    (who's asking, what page they're on) without it ever passing through the
    conversation history or the LLM's own context as a plain message — a tool
    reads it directly off `ctx.deps`. Used here for two things: (1) the
    structural stock-lookup cap (see MAX_STOCK_LOOKUPS_PER_TURN), and (2) the
    shopper's identity/page, exposed read-only via get_shopper_context_tool."""

    stock_lookups: int = 0
    first_name: str | None = None
    page: str = "unknown"
    viewing_product_id: str | None = None
    viewing_product_name: str | None = None


MAX_STOCK_LOOKUPS_PER_TURN = 2

agent = Agent(
    model,
    output_type=ChatReply,
    system_prompt=SYSTEM_PROMPT,
    deps_type=ChatDeps,
)

AUDIT_LOG_PATH = Path(__file__).resolve().parents[1] / "output" / "audit_trail.json"


def _check_stock_lookup_budget(ctx: RunContext[ChatDeps]) -> None:
    """Structural guard against looping stock lookups across an entire
    category instead of asking which specific product the shopper means.
    Raising ModelRetry here — instead of just hoping the prompt discourages
    it — means the model CANNOT check more than MAX_STOCK_LOOKUPS_PER_TURN
    distinct products in one reply, no matter how it reasons about it."""
    if ctx.deps.stock_lookups >= MAX_STOCK_LOOKUPS_PER_TURN:
        raise ModelRetry(
            f"You've already checked stock for {MAX_STOCK_LOOKUPS_PER_TURN} different products this turn. "
            "That's the limit — if the shopper's request could mean several different products "
            "(e.g. several sport-specific variants of the same style), STOP checking more of them "
            "and instead ask the shopper which specific one they mean."
        )
    ctx.deps.stock_lookups += 1


@agent.tool
def get_shopper_context_tool(ctx: RunContext[ChatDeps]) -> ShopperContext:
    """Find out who you're talking to and what page they're currently on.
    Call this whenever a shopper uses a vague reference ("this", "it", "do
    you have this in pink") and no specific product has already come up
    earlier in THIS conversation — if they're on a product detail page,
    `viewing_product_id`/`viewing_product_name` tells you which product "this"
    almost certainly means, so you can act without asking them to repeat it.
    Not subject to the stock-lookup cap — this reads request state, it
    doesn't touch the database."""
    return ShopperContext(
        logged_in=ctx.deps.first_name is not None,
        first_name=ctx.deps.first_name,
        page=ctx.deps.page,
        viewing_product_id=ctx.deps.viewing_product_id,
        viewing_product_name=ctx.deps.viewing_product_name,
    )


@agent.tool_plain
def search_products_tool(
    color: str | None = None,
    garment_type: str | None = None,
    keywords: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
) -> list[ProductSearchResult]:
    """Search the catalogue. `color`, `garment_type`, `min_price`, and
    `max_price` are all EXACT filters — every result is guaranteed to match
    every one given (never a partial or "close enough" match). Get a valid
    `garment_type` value from list_garment_types_tool first. Use `min_price`/
    `max_price` whenever a shopper mentions a budget ("under $50", "between
    $30 and $60", "cheapest options") — the filter runs before any result cap,
    so it won't miss real matches the way eyeballing a capped list might.
    `keywords` is for anything without its own column — team names, graphics,
    occasions — and is a loose text match layered on top of the other filters,
    not a replacement for them. Always pass color/garment_type/price bounds as
    their own arguments when the shopper mentioned them — never fold them into
    `keywords` as a single string, since `keywords` alone does not guarantee
    an exact match."""
    return search_products(
        color=color, garment_type=garment_type, keywords=keywords, min_price=min_price, max_price=max_price
    )


@agent.tool_plain
def list_garment_types_tool(color: str | None = None, keywords: str | None = None) -> list[str]:
    """List every distinct garment type (already consolidated into shopper-
    friendly categories, e.g. "hoodie" covers every hoodie-like product)
    among ALL products matching the given filters — not a capped sample.
    Use this before asking a shopper which type they want for a broad
    filter like a color alone."""
    return list_garment_types(color=color, keywords=keywords)


@agent.tool
def get_product_stock_tool(ctx: RunContext[ChatDeps], product_id: str) -> ProductStock:
    """Get price and the full per-size stock breakdown for a specific product by its catalogue ID.
    Limited to a small number of distinct products per turn — if a shopper's
    reference could mean several different products, ask which one instead
    of checking every candidate."""
    _check_stock_lookup_budget(ctx)
    return get_product_stock(product_id)


@agent.tool
def check_size_availability_tool(ctx: RunContext[ChatDeps], product_id: str, size: str) -> SizeAvailability:
    """Check stock for ONE specific size of a product (e.g. shopper asks "do you have this in Large?").
    Limited to a small number of distinct products per turn — if a shopper's
    reference could mean several different products, ask which one instead
    of checking every candidate."""
    _check_stock_lookup_budget(ctx)
    return get_size_availability(product_id, size)


@agent.tool_plain
def get_stock_for_products_tool(product_ids: list[str]) -> list[ProductStock]:
    """Get full per-size stock + price for MULTIPLE products in ONE call — use
    this for a deliberate bulk/plural request about a set of products the
    shopper has already identified as a group (e.g. "what's the stock on all
    of them", or "the sports hoodies" plural after you showed a list of
    sport-specific variants). NOT subject to the single-product lookup cap,
    since this is one intentional call, not a loop.

    Do NOT use this to dodge asking which product a shopper means when their
    reference is singular and ambiguous ("the sports hoodie") — that case
    should still get a clarifying question. Use this tool only when the
    shopper's own wording indicates they want info on the whole set (plural,
    "all of them", "each one", etc.), and pass the product_ids from an
    earlier search_products_tool result in this conversation."""
    return get_stock_for_products(product_ids)


def _plain(value: object) -> object:
    """Convert a tool result to plain JSON-able data for the audit log —
    tool returns are now typed Pydantic models (ProductStock, etc.), not raw
    dicts, so this unwraps them instead of falling back to str()."""
    if isinstance(value, BaseModel):
        return value.model_dump()
    if isinstance(value, list):
        return [_plain(v) for v in value]
    return value


def _extract_tool_calls(messages: list[ModelMessage]) -> list[dict]:
    """Pull a flat, readable list of {tool_name, args, result} out of the
    raw PydanticAI message history for one run, for audit logging."""
    calls: dict[str, dict] = {}
    order: list[str] = []
    for message in messages:
        for part in getattr(message, "parts", []):
            if isinstance(part, ToolCallPart):
                calls[part.tool_call_id] = {"tool_name": part.tool_name, "args": part.args}
                order.append(part.tool_call_id)
            elif isinstance(part, ToolReturnPart) and part.tool_call_id in calls:
                calls[part.tool_call_id]["result"] = _plain(part.content)
            elif isinstance(part, RetryPromptPart) and part.tool_call_id in calls:
                calls[part.tool_call_id]["result"] = f"RETRY: {part.content}"
    return [calls[call_id] for call_id in order]


def _append_audit_entry(entry: dict) -> None:
    """Appends to output/audit_trail.json. Deliberately append-only and
    NEVER truncated or reset — this is the permanent record of every agent
    turn across the life of the project, not a rolling debug log. (An
    earlier version capped this file at 2000 entries and dropped the
    oldest; that cap has been removed on purpose — unbounded growth is the
    correct tradeoff for a real audit trail, not a bug to fix.)"""
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entries = []
    if AUDIT_LOG_PATH.exists():
        try:
            entries = json.loads(AUDIT_LOG_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            entries = []
    entries.append(entry)
    AUDIT_LOG_PATH.write_text(json.dumps(entries, indent=2, default=str))


def _normalize_spelling(message: str) -> str:
    """The catalogue only ever spells it "gray" (never "grey"), so a shopper
    typing the British spelling can make literal substring matching in
    search_products_tool fail. Normalize before the model ever sees the
    message, so this doesn't depend on the model remembering to translate it
    itself when it writes a tool call."""
    return re.sub(r"\bgrey\b", "gray", message, flags=re.IGNORECASE)


def run_chat(
    message: str,
    history: list[ModelMessage] | None = None,
    user_id: int | None = None,
    first_name: str | None = None,
    page: str = "unknown",
    viewing_product_id: str | None = None,
    viewing_product_name: str | None = None,
) -> ChatReply:
    """Run one turn of the shopping assistant, log the turn to output/audit_trail.json
    (timestamp, user, tool calls, stop reason, duration), and return the reply."""
    start = time.monotonic()
    stop_reason = "completed"
    tool_calls: list[dict] = []
    try:
        model_input = _normalize_spelling(message)
        deps = ChatDeps(
            first_name=first_name,
            page=page,
            viewing_product_id=viewing_product_id,
            viewing_product_name=viewing_product_name,
        )
        result = agent.run_sync(model_input, message_history=history or [], deps=deps)
        tool_calls = _extract_tool_calls(result.all_messages())
        return result.output
    except Exception:
        stop_reason = "error"
        raise
    finally:
        duration_ms = int((time.monotonic() - start) * 1000)
        _append_audit_entry(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": user_id,
                "message": message,
                "tool_calls": tool_calls,
                "stop_reason": stop_reason,
                "duration_ms": duration_ms,
            }
        )
