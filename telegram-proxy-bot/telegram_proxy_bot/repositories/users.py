from __future__ import annotations

from typing import Optional

from .base import db_context
from ..utils import now_iso



def upsert_user(user_id: int, username: Optional[str], first_name: Optional[str]) -> None:
    ts = now_iso()
    with db_context() as conn:
        conn.execute(
            """
            INSERT INTO users (user_id, username, first_name, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                updated_at = excluded.updated_at
            """,
            (user_id, username, first_name, ts, ts),
        )



def has_used_trial(user_id: int) -> bool:
    with db_context() as conn:
        row = conn.execute("SELECT trial_used FROM users WHERE user_id=?", (user_id,)).fetchone()
    return bool(row and row["trial_used"])



def mark_trial_used(user_id: int) -> None:
    with db_context() as conn:
        conn.execute("UPDATE users SET trial_used=1, updated_at=? WHERE user_id=?", (now_iso(), user_id))



def reset_trial_used(user_id: int) -> None:
    with db_context() as conn:
        conn.execute("UPDATE users SET trial_used=0, updated_at=? WHERE user_id=?", (now_iso(), user_id))



def list_recent_users(limit: int = 15):
    with db_context() as conn:
        return conn.execute(
            "SELECT user_id, username, first_name, trial_used, created_at FROM users ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
