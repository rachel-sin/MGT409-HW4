"""Campus Customs API.

Serves the catalogue/inventory tables and product images, handles
signup/login, and exposes the PydanticAI shopping assistant (see agent/) as
a chat endpoint for the frontend's chat widget.
"""

import json
import sqlite3
import time
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart

from auth import hash_password, verify_password
from agent import run_chat
from models import (
    AuthResponse,
    ChatHistoryMessage,
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
    LoginRequest,
    Product,
    ProductSize,
    SignupRequest,
    User,
)
from sessions import create_session, delete_session, ensure_sessions_table, resolve_session

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "campus_customs.db"
IMAGES_DIR = ROOT / "data" / "products"

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def size_sort_key(size: str) -> int:
    return SIZE_ORDER.index(size) if size in SIZE_ORDER else len(SIZE_ORDER)


def row_to_product(conn: sqlite3.Connection, row: sqlite3.Row) -> Product:
    size_rows = conn.execute(
        "SELECT size, quantity FROM inventory WHERE product_id = ?",
        (row["product_id"],),
    ).fetchall()
    sizes = sorted(
        (ProductSize(size=r["size"], quantity=r["quantity"]) for r in size_rows),
        key=lambda s: size_sort_key(s.size),
    )
    return Product(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        description=row["description"],
        colors=json.loads(row["colors"]),
        search_tags=json.loads(row["search_tags"]),
        image=f"/images/{Path(row['image_file_path']).name}",
        price=row["price"],
        sizes=sizes,
    )


app = FastAPI(title="Campus Customs API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")


@app.on_event("startup")
def _ensure_tables() -> None:
    conn = get_connection()
    try:
        ensure_sessions_table(conn)
    finally:
        conn.close()


def get_bearer_token(request: Request) -> str | None:
    header = request.headers.get("authorization")
    if not header or not header.startswith("Bearer "):
        return None
    return header[len("Bearer ") :].strip() or None


def get_authenticated_user_id(request: Request, conn: sqlite3.Connection) -> int | None:
    """The ONLY place a request's identity is allowed to come from — never a
    user_id the client merely asserts in a body or query param. Returns None
    for guests (no token) and for an invalid/expired token alike, since
    either way there's no verified user to attach the request to."""
    token = get_bearer_token(request)
    if token is None:
        return None
    return resolve_session(conn, token)


@app.get("/api/products", response_model=list[Product])
def list_products() -> list[Product]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
        return [row_to_product(conn, row) for row in rows]
    finally:
        conn.close()


@app.get("/api/products/{product_id}", response_model=Product)
def get_product(product_id: str) -> Product:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        return row_to_product(conn, row)
    finally:
        conn.close()


@app.post("/api/auth/signup", response_model=AuthResponse, status_code=201)
def signup(payload: SignupRequest) -> AuthResponse:
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    if len(payload.password) < 8:
        raise HTTPException(
            status_code=400, detail="Password must be at least 8 characters"
        )

    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE email = ?", (payload.email,)
        ).fetchone()
        if existing is not None:
            raise HTTPException(status_code=400, detail="Email is already registered")

        password_hash = hash_password(payload.password)
        full_name = f"{payload.first_name} {payload.last_name}"
        cursor = conn.execute(
            """
            INSERT INTO users (name, email, password_hash, first_name, last_name)
            VALUES (?, ?, ?, ?, ?)
            """,
            (full_name, payload.email, password_hash, payload.first_name, payload.last_name),
        )
        conn.commit()
        user_id = cursor.lastrowid
        token = create_session(conn, user_id)
        return AuthResponse(
            id=user_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            session_token=token,
        )
    finally:
        conn.close()


@app.post("/api/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (payload.email,)
        ).fetchone()
        if row is None or not verify_password(payload.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        token = create_session(conn, row["id"])
        return AuthResponse(
            id=row["id"],
            first_name=row["first_name"] or "",
            last_name=row["last_name"] or "",
            email=row["email"],
            session_token=token,
        )
    finally:
        conn.close()


@app.post("/api/auth/logout", status_code=204)
def logout(request: Request) -> None:
    token = get_bearer_token(request)
    if token is None:
        return
    conn = get_connection()
    try:
        delete_session(conn, token)
    finally:
        conn.close()


def load_chat_history(conn: sqlite3.Connection, user_id: int, limit: int = 20) -> list[ModelMessage]:
    """Reconstruct PydanticAI message history from this user's past chat_messages rows."""
    rows = conn.execute(
        "SELECT role, content FROM chat_messages WHERE user_id = ? ORDER BY id ASC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    history: list[ModelMessage] = []
    for row in rows:
        if row["role"] == "user":
            history.append(ModelRequest(parts=[UserPromptPart(content=row["content"])]))
        else:
            history.append(ModelResponse(parts=[TextPart(content=row["content"])]))
    return history


def save_chat_message(
    conn: sqlite3.Connection, user_id: int, role: str, content: str, product_ids: list[str]
) -> None:
    conn.execute(
        "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, ?, ?, ?)",
        (user_id, role, content, json.dumps(product_ids)),
    )
    conn.commit()


MAX_CHAT_HISTORY_PER_USER = 200


def prune_chat_history(conn: sqlite3.Connection, user_id: int) -> None:
    """Keep chat_messages from growing without bound — a shopper's history
    is only ever used to restore the widget and feed the agent's own
    short-term memory (capped at 20 turns, see load_chat_history), so there's
    no reason to keep more than this many rows around per user."""
    conn.execute(
        """
        DELETE FROM chat_messages
        WHERE user_id = ? AND id NOT IN (
            SELECT id FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT ?
        )
        """,
        (user_id, user_id, MAX_CHAT_HISTORY_PER_USER),
    )
    conn.commit()


@app.get("/api/chat/history", response_model=ChatHistoryResponse)
def chat_history(request: Request) -> ChatHistoryResponse:
    """Repopulate the chat widget for a returning, logged-in shopper. Guests
    get a 401 (there's no history to reload — see /api/chat), and the user
    whose history comes back is whoever the bearer token resolves to, never
    a user_id a request could just claim."""
    conn = get_connection()
    try:
        user_id = get_authenticated_user_id(request, conn)
        if user_id is None:
            raise HTTPException(status_code=401, detail="Login required to view chat history")
        enforce_rate_limit(f"history:user:{user_id}", HISTORY_RATE_LIMIT, RATE_WINDOW_SECONDS)

        rows = conn.execute(
            "SELECT role, content, products_json FROM chat_messages WHERE user_id = ? ORDER BY id ASC LIMIT ?",
            (user_id, MAX_CHAT_HISTORY_PER_USER),
        ).fetchall()
        messages: list[ChatHistoryMessage] = []
        for row in rows:
            product_ids: list[str] = json.loads(row["products_json"]) if row["products_json"] else []
            products: list[Product] = []
            for product_id in product_ids:
                product_row = conn.execute(
                    "SELECT * FROM catalogue WHERE product_id = ?", (product_id,)
                ).fetchone()
                if product_row is not None:
                    products.append(row_to_product(conn, product_row))
            messages.append(ChatHistoryMessage(role=row["role"], content=row["content"], products=products))
        return ChatHistoryResponse(messages=messages)
    finally:
        conn.close()


@app.delete("/api/chat/history", status_code=204)
def clear_chat_history(request: Request) -> None:
    """Lets a shopper erase their own saved conversation. Scoped to whatever
    user the bearer token resolves to — there's no way to pass someone
    else's id and clear their history instead of your own."""
    conn = get_connection()
    try:
        user_id = get_authenticated_user_id(request, conn)
        if user_id is None:
            raise HTTPException(status_code=401, detail="Login required to clear chat history")
        enforce_rate_limit(f"history-clear:user:{user_id}", HISTORY_RATE_LIMIT, RATE_WINDOW_SECONDS)
        conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()


# Simple in-memory sliding-window limiter so one shopper (or a script) can't
# hammer an endpoint and run up real model-provider cost or just read load.
# Keyed by caller + endpoint (via the key prefix each call site passes) so a
# shopper's /api/chat budget and their /api/chat/history budget don't share
# one counter. Good enough for a single-process dev app; a real deployment
# would use a shared store (e.g. Redis) across workers.
RATE_WINDOW_SECONDS = 60.0
CHAT_RATE_LIMIT = 10
HISTORY_RATE_LIMIT = 30
_request_times: dict[str, list[float]] = defaultdict(list)


def enforce_rate_limit(key: str, limit: int, window_seconds: float) -> None:
    now = time.monotonic()
    window_start = now - window_seconds
    timestamps = _request_times[key]
    while timestamps and timestamps[0] < window_start:
        timestamps.pop(0)
    if len(timestamps) >= limit:
        raise HTTPException(
            status_code=429,
            detail="You're sending requests too quickly — please wait a moment and try again.",
        )
    timestamps.append(now)


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    conn = get_connection()
    try:
        # The ONLY source of truth for who's chatting — never anything the
        # request body claims. No/invalid/expired token just means "guest",
        # which is a normal, fully-supported way to use the chat.
        user_id = get_authenticated_user_id(request, conn)

        rate_limit_key = (
            f"chat:user:{user_id}"
            if user_id is not None
            else f"chat:ip:{request.client.host if request.client else 'unknown'}"
        )
        enforce_rate_limit(rate_limit_key, CHAT_RATE_LIMIT, RATE_WINDOW_SECONDS)

        history = load_chat_history(conn, user_id) if user_id else []
        if user_id is not None:
            save_chat_message(conn, user_id, "user", payload.message, [])
            prune_chat_history(conn, user_id)

        first_name: str | None = None
        email: str | None = None
        if user_id is not None:
            user_row = conn.execute(
                "SELECT first_name, email FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            if user_row is not None:
                first_name = user_row["first_name"]
                email = user_row["email"]

        # viewing_product_name is resolved from the catalogue here, server-
        # side, by the client-supplied product_id — never taken from
        # anything else the client sends. A product_id that doesn't actually
        # exist (spoofed or stale) is silently dropped rather than handed to
        # the agent, since there's nothing real for it to describe.
        page_context = payload.page_context
        viewing_product_id: str | None = None
        viewing_product_name: str | None = None
        if page_context and page_context.page == "product_detail" and page_context.product_id:
            product_row = conn.execute(
                "SELECT name FROM catalogue WHERE product_id = ?", (page_context.product_id,)
            ).fetchone()
            if product_row is not None:
                viewing_product_id = page_context.product_id
                viewing_product_name = product_row["name"]

        try:
            reply = run_chat(
                payload.message,
                history=history,
                user_id=user_id,
                first_name=first_name,
                email=email,
                page=page_context.page if page_context else "unknown",
                viewing_product_id=viewing_product_id,
                viewing_product_name=viewing_product_name,
            )
        except Exception:
            # Covers upstream model errors (rate limits, content-filter rejections
            # from a malicious/adversarial message, timeouts, etc.) so a model
            # provider hiccup degrades to a polite reply instead of a 500.
            fallback = "Sorry, I'm having trouble answering that right now. Could you rephrase, or ask about a specific product?"
            if user_id is not None:
                save_chat_message(conn, user_id, "assistant", fallback, [])
                prune_chat_history(conn, user_id)
            return ChatResponse(message=fallback, products=[])

        enriched: list[Product] = []
        for ref in reply.products:
            row = conn.execute(
                "SELECT * FROM catalogue WHERE product_id = ?", (ref.product_id,)
            ).fetchone()
            if row is not None:
                enriched.append(row_to_product(conn, row))

        if user_id is not None:
            save_chat_message(conn, user_id, "assistant", reply.message, [p.product_id for p in enriched])
            prune_chat_history(conn, user_id)

        return ChatResponse(message=reply.message, products=enriched)
    finally:
        conn.close()
