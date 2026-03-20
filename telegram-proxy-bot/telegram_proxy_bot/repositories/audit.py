from __future__ import annotations

from datetime import timedelta

from .base import db_context
from ..utils import now_iso, now_utc



def write_audit(user_id: int, username: str, action: str, details: str = "") -> None:
    with db_context() as conn:
        conn.execute(
            "INSERT INTO audit_log (user_id, username, action, details, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, username, action, details, now_iso()),
        )


def count_recent_user_actions(user_id: int, action: str, hours: int) -> int:
    window_start = (now_utc() - timedelta(hours=hours)).isoformat()
    with db_context() as conn:
        row = conn.execute(
            "SELECT COUNT(1) AS cnt FROM audit_log WHERE user_id=? AND action=? AND created_at>=?",
            (user_id, action, window_start),
        ).fetchone()
    return int(row["cnt"] if row else 0)
