from __future__ import annotations

from sqlite3 import Row

from .base import db_context
from ..utils import now_iso


def create_ticket_draft(user_id: int) -> None:
    with db_context() as conn:
        conn.execute(
            """
            INSERT INTO ticket_drafts (user_id, created_at)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET created_at=excluded.created_at
            """,
            (user_id, now_iso()),
        )


def has_ticket_draft(user_id: int) -> bool:
    with db_context() as conn:
        row = conn.execute("SELECT user_id FROM ticket_drafts WHERE user_id=?", (user_id,)).fetchone()
    return row is not None


def clear_ticket_draft(user_id: int) -> None:
    with db_context() as conn:
        conn.execute("DELETE FROM ticket_drafts WHERE user_id=?", (user_id,))


def create_ticket(user_id: int, text: str) -> int:
    ts = now_iso()
    with db_context() as conn:
        row_id = conn.execute(
            "INSERT INTO tickets (user_id, status, created_at, closed_at) VALUES (?, 'open', ?, '')",
            (user_id, ts),
        ).lastrowid
        conn.execute(
            """
            INSERT INTO ticket_messages (ticket_id, author_role, author_id, text, created_at)
            VALUES (?, 'user', ?, ?, ?)
            """,
            (row_id, user_id, text, ts),
        )
    return int(row_id or 0)


def get_open_ticket(ticket_id: int) -> Row | None:
    with db_context() as conn:
        return conn.execute("SELECT id, user_id, status, created_at FROM tickets WHERE id=? AND status='open'", (ticket_id,)).fetchone()


def add_admin_reply(ticket_id: int, admin_id: int, text: str) -> None:
    with db_context() as conn:
        conn.execute(
            """
            INSERT INTO ticket_messages (ticket_id, author_role, author_id, text, created_at)
            VALUES (?, 'admin', ?, ?, ?)
            """,
            (ticket_id, admin_id, text, now_iso()),
        )


def close_ticket(ticket_id: int, admin_id: int) -> bool:
    ts = now_iso()
    with db_context() as conn:
        updated = conn.execute(
            "UPDATE tickets SET status='closed', closed_at=? WHERE id=? AND status='open'",
            (ts, ticket_id),
        ).rowcount
        if not updated:
            return False
        conn.execute(
            """
            INSERT INTO ticket_messages (ticket_id, author_role, author_id, text, created_at)
            VALUES (?, 'system', ?, 'Тикет закрыт администратором.', ?)
            """,
            (ticket_id, admin_id, ts),
        )
    return True
