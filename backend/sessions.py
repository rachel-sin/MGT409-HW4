"""Login session tokens — closes the gap where /api/chat trusted whatever
user_id a request claimed, with nothing proving the caller actually is that
user. Login/signup now hand back an opaque bearer token; every authenticated
request must present it, and the user_id for that request comes ONLY from
resolving the token server-side, never from anything the client asserts.

Tokens are stored as a SHA-256 hash, not in plaintext, same principle as
backend/auth.py not storing plaintext passwords — a stolen copy of this
table shouldn't hand over everyone's live sessions.
"""

import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

SESSION_TTL = timedelta(days=7)


def ensure_sessions_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )
    conn.commit()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(conn: sqlite3.Connection, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    conn.execute(
        "INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (_hash_token(token), user_id, now.isoformat(), (now + SESSION_TTL).isoformat()),
    )
    conn.commit()
    return token


def resolve_session(conn: sqlite3.Connection, token: str) -> int | None:
    """Return the user_id for a valid, unexpired session token, or None —
    the only place in the app a request's identity is allowed to come from."""
    row = conn.execute(
        "SELECT user_id, expires_at FROM sessions WHERE token_hash = ?",
        (_hash_token(token),),
    ).fetchone()
    if row is None:
        return None
    if datetime.fromisoformat(row["expires_at"]) < datetime.now(timezone.utc):
        return None
    return row["user_id"]


def delete_session(conn: sqlite3.Connection, token: str) -> None:
    conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_hash_token(token),))
    conn.commit()
