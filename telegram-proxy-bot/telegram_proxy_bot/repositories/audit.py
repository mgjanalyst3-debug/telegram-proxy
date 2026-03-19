from __future__ import annotations

from .base import db_context
from ..utils import now_iso



def write_audit(user_id: int, username: str, action: str, details: str = "") -> None:
    with db_context() as conn:
        conn.execute(
            "INSERT INTO audit_log (user_id, username, action, details, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, username, action, details, now_iso()),
        )
