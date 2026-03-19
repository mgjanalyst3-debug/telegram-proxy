from __future__ import annotations

from .base import db_context
from ..utils import now_iso



def create_payment_invoice(user_id: int, payload: str, amount: int, currency: str, status: str = "new") -> None:
    ts = now_iso()
    with db_context() as conn:
        conn.execute(
            """
            INSERT INTO payments (user_id, payload, amount, currency, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(payload) DO UPDATE SET
                user_id = excluded.user_id,
                amount = excluded.amount,
                currency = excluded.currency,
                status = excluded.status,
                updated_at = excluded.updated_at
            """,
            (user_id, payload, amount, currency, status, ts, ts),
        )



def get_payment_by_payload(payload: str):
    with db_context() as conn:
        return conn.execute("SELECT * FROM payments WHERE payload=?", (payload,)).fetchone()



def get_payment_by_charge_id(charge_id: str):
    with db_context() as conn:
        return conn.execute(
            "SELECT * FROM payments WHERE telegram_payment_charge_id=?",
            (charge_id,),
        ).fetchone()



def mark_payment_success(
    *,
    user_id: int,
    payload: str,
    amount: int,
    currency: str,
    telegram_payment_charge_id: str,
    provider_payment_charge_id: str,
    subscription_expiration_date: int | None,
    is_recurring: bool | None,
    is_first_recurring: bool | None,
) -> None:
    ts = now_iso()
    with db_context() as conn:
        conn.execute(
            """
            INSERT INTO payments (
                user_id, payload, amount, currency, status, telegram_payment_charge_id,
                provider_payment_charge_id, subscription_expiration_date, is_recurring,
                is_first_recurring, paid_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'paid', ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(payload) DO UPDATE SET
                user_id = excluded.user_id,
                amount = excluded.amount,
                currency = excluded.currency,
                status = 'paid',
                telegram_payment_charge_id = excluded.telegram_payment_charge_id,
                provider_payment_charge_id = excluded.provider_payment_charge_id,
                subscription_expiration_date = excluded.subscription_expiration_date,
                is_recurring = excluded.is_recurring,
                is_first_recurring = excluded.is_first_recurring,
                paid_at = excluded.paid_at,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                payload,
                amount,
                currency,
                telegram_payment_charge_id,
                provider_payment_charge_id,
                subscription_expiration_date or 0,
                1 if is_recurring else 0,
                1 if is_first_recurring else 0,
                ts,
                ts,
                ts,
            ),
        )



def mark_payment_fulfilled(payload: str) -> None:
    with db_context() as conn:
        conn.execute(
            "UPDATE payments SET fulfilled=1, updated_at=? WHERE payload=?",
            (now_iso(), payload),
        )



def update_payment_status(payload: str, status: str) -> None:
    with db_context() as conn:
        conn.execute(
            "UPDATE payments SET status=?, updated_at=? WHERE payload=?",
            (status, now_iso(), payload),
        )



def list_recent_payments(limit: int = 15):
    with db_context() as conn:
        return conn.execute(
            "SELECT * FROM payments ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
