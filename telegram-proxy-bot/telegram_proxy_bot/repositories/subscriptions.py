from __future__ import annotations

import re
from typing import Optional

from .base import db_context
from ..config import settings
from ..models import Subscription
from ..utils import build_password, build_username


SUBSCRIPTION_SELECT = (
    "SELECT id, user_id, plan, proxy_type, host, port, username, password, secret, status, issued_at, expires_at, "
    "connections_limit, devices_limit, remind_24_sent_at, remind_1_sent_at, expired_notice_sent_at "
    "FROM subscriptions"
)

_MT_SECRET_RE = re.compile(r"^[0-9a-fA-F]{32,}$")

def _is_valid_mtproto_secret(value: str) -> bool:
    secret = (value or "").strip()
    return bool(secret) and len(secret) % 2 == 0 and _MT_SECRET_RE.fullmatch(secret) is not None


def _row_value(row, key: str, default=""):
    return row[key] if key in row.keys() else default


def _row_to_subscription(row) -> Subscription:
    return Subscription(
        row_id=row["id"],
        user_id=row["user_id"],
        plan=row["plan"],
        proxy_type=row["proxy_type"],
        host=row["host"],
        port=row["port"],
        username=row["username"],
        password=row["password"],
        secret=_row_value(row, "secret"),
        status=row["status"],
        issued_at=row["issued_at"],
        expires_at=row["expires_at"],
        connections_limit=row["connections_limit"],
        devices_limit=row["devices_limit"],
        remind_24_sent_at=_row_value(row, "remind_24_sent_at"),
        remind_1_sent_at=_row_value(row, "remind_1_sent_at", _row_value(row, "remind_72_sent_at")),
        expired_notice_sent_at=row["expired_notice_sent_at"],
    )


def normalize_legacy_subscription_row(row) -> Subscription:
    needs_update = False
    username = row["username"] or build_username(row["user_id"])
    password = row["password"] or build_password()
    secret = _row_value(row, "secret") or settings.mtproto_secret or password
    if not _is_valid_mtproto_secret(secret):
        secret = build_password()
        needs_update = True

    host = row["host"] or settings.mtproto_host
    port = row["port"] or settings.mtproto_port
    proxy_type = "mtproto"
    issued_at = row["issued_at"] or row["expires_at"]
    plan = row["plan"]
    connections_limit = row["connections_limit"] or settings.default_connections_limit
    devices_limit = row["devices_limit"] or settings.default_devices_limit

    if plan == "paid_30d":
        plan = "30 дней"
        needs_update = True

    if (
        not row["username"]
        or not row["password"]
        or not row["host"]
        or not row["port"]
        or row["proxy_type"] != "mtproto"
        or not row["issued_at"]
        or not row["connections_limit"]
        or not row["devices_limit"]
        or row["port"] != settings.mtproto_port
    ):
        needs_update = True

    if needs_update:
        with db_context() as conn:
            conn.execute(
                """
                UPDATE subscriptions
                SET plan=?, proxy_type=?, host=?, port=?, username=?, password=?, issued_at=?,
                    secret=?, connections_limit=?, devices_limit=?
                WHERE id=?
                """,
                (
                    plan,
                    proxy_type,
                    host,
                    port,
                    username,
                    password,
                    issued_at,
                    secret,
                    connections_limit,
                    devices_limit,
                    row["id"],
                ),
            )
            row = conn.execute(f"{SUBSCRIPTION_SELECT} WHERE id=?", (row["id"],)).fetchone()
    return _row_to_subscription(row)


def get_latest_subscription(user_id: int) -> Optional[Subscription]:
    with db_context() as conn:
        row = conn.execute(
            f"{SUBSCRIPTION_SELECT} WHERE user_id=? ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    if not row:
        return None
    return normalize_legacy_subscription_row(row)


def get_latest_active_subscription_raw(user_id: int) -> Optional[Subscription]:
    with db_context() as conn:
        row = conn.execute(
            f"{SUBSCRIPTION_SELECT} WHERE user_id=? AND status='active' ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    if not row:
        return None
    return normalize_legacy_subscription_row(row)


def insert_subscription(sub: Subscription) -> Subscription:
    with db_context() as conn:
        cursor = conn.execute(
            """
            INSERT INTO subscriptions (
                user_id, plan, proxy_type, host, port, username, password, secret, status, issued_at, expires_at,
                connections_limit, devices_limit, remind_24_sent_at, remind_1_sent_at, expired_notice_sent_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sub.user_id,
                sub.plan,
                sub.proxy_type,
                sub.host,
                sub.port,
                sub.username,
                sub.password,
                sub.secret,
                sub.status,
                sub.issued_at,
                sub.expires_at,
                sub.connections_limit,
                sub.devices_limit,
                sub.remind_24_sent_at,
                sub.remind_1_sent_at,
                sub.expired_notice_sent_at,
            ),
        )
        row_id = cursor.lastrowid
        row = conn.execute(f"{SUBSCRIPTION_SELECT} WHERE id=?", (row_id,)).fetchone()
    return _row_to_subscription(row)


def expire_active_subscriptions(user_id: int) -> None:
    with db_context() as conn:
        conn.execute(
            "UPDATE subscriptions SET status='expired' WHERE user_id=? AND status='active'",
            (user_id,),
        )


def set_reminder_sent(subscription_id: int, hours_before: int, timestamp: str) -> None:
    column = "remind_24_sent_at" if hours_before >= 24 else "remind_1_sent_at"
    with db_context() as conn:
        conn.execute(f"UPDATE subscriptions SET {column}=? WHERE id=?", (timestamp, subscription_id))


def set_expired_notice_sent(subscription_id: int, timestamp: str) -> None:
    with db_context() as conn:
        conn.execute(
            "UPDATE subscriptions SET expired_notice_sent_at=? WHERE id=?",
            (timestamp, subscription_id),
        )


def list_recent_latest_active_subscriptions(limit: int = 15):
    with db_context() as conn:
        return conn.execute(
            f"""
            {SUBSCRIPTION_SELECT}
            WHERE status='active'
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()


def list_active_subscription_snapshots_for_watch():
    with db_context() as conn:
        return conn.execute(
            f"{SUBSCRIPTION_SELECT} WHERE status='active' ORDER BY id DESC"
        ).fetchall()


def list_latest_subscription_snapshots(limit: int = 15):
    with db_context() as conn:
        return conn.execute(
            f"""
            {SUBSCRIPTION_SELECT}
            WHERE id IN (SELECT MAX(id) FROM subscriptions GROUP BY user_id)
            ORDER BY user_id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
