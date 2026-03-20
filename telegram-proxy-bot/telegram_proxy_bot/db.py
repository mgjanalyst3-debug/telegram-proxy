from __future__ import annotations

import sqlite3
from pathlib import Path

from .config import settings



def db() -> sqlite3.Connection:
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn



def table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}



def add_column_if_missing(conn: sqlite3.Connection, table_name: str, column_sql: str, column_name: str) -> None:
    if column_name not in table_columns(conn, table_name):
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}")



def init_db() -> None:
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                trial_used INTEGER NOT NULL DEFAULT 0,
                is_banned INTEGER NOT NULL DEFAULT 0,
                admin_note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan TEXT NOT NULL,
                proxy_type TEXT NOT NULL DEFAULT 'socks5',
                host TEXT NOT NULL DEFAULT '',
                port INTEGER NOT NULL DEFAULT 0,
                username TEXT NOT NULL DEFAULT '',
                password TEXT NOT NULL DEFAULT '',
                secret TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL,
                issued_at TEXT NOT NULL DEFAULT '',
                expires_at TEXT NOT NULL,
                connections_limit INTEGER NOT NULL DEFAULT 2,
                devices_limit INTEGER NOT NULL DEFAULT 2,
                remind_24_sent_at TEXT NOT NULL DEFAULT '',
                expired_notice_sent_at TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                payload TEXT NOT NULL,
                amount INTEGER NOT NULL,
                currency TEXT NOT NULL,
                status TEXT NOT NULL,
                telegram_payment_charge_id TEXT NOT NULL DEFAULT '',
                provider_payment_charge_id TEXT NOT NULL DEFAULT '',
                subscription_expiration_date INTEGER NOT NULL DEFAULT 0,
                is_recurring INTEGER NOT NULL DEFAULT 0,
                is_first_recurring INTEGER NOT NULL DEFAULT 0,
                fulfilled INTEGER NOT NULL DEFAULT 0,
                paid_at TEXT NOT NULL DEFAULT '',
                refunded_at TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 0,
                username TEXT NOT NULL DEFAULT '',
                action TEXT NOT NULL,
                details TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL,
                closed_at TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS ticket_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                author_role TEXT NOT NULL,
                author_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS ticket_drafts (
                user_id INTEGER PRIMARY KEY,
                created_at TEXT NOT NULL
            );


            CREATE INDEX IF NOT EXISTS idx_subscriptions_user_status ON subscriptions(user_id, status);
            CREATE INDEX IF NOT EXISTS idx_subscriptions_expires_at ON subscriptions(expires_at);
            CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
            CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_payments_payload ON payments(payload);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_payments_charge_id ON payments(telegram_payment_charge_id) WHERE telegram_payment_charge_id != '';
            CREATE INDEX IF NOT EXISTS idx_tickets_user_status ON tickets(user_id, status);
            CREATE INDEX IF NOT EXISTS idx_ticket_messages_ticket_id ON ticket_messages(ticket_id);
            """
        )

        add_column_if_missing(conn, "users", "trial_used INTEGER NOT NULL DEFAULT 0", "trial_used")
        add_column_if_missing(conn, "users", "is_banned INTEGER NOT NULL DEFAULT 0", "is_banned")
        add_column_if_missing(conn, "users", "admin_note TEXT NOT NULL DEFAULT ''", "admin_note")

        add_column_if_missing(conn, "subscriptions", "proxy_type TEXT NOT NULL DEFAULT 'socks5'", "proxy_type")
        add_column_if_missing(conn, "subscriptions", "host TEXT NOT NULL DEFAULT ''", "host")
        add_column_if_missing(conn, "subscriptions", "port INTEGER NOT NULL DEFAULT 0", "port")
        add_column_if_missing(conn, "subscriptions", "username TEXT NOT NULL DEFAULT ''", "username")
        add_column_if_missing(conn, "subscriptions", "password TEXT NOT NULL DEFAULT ''", "password")
        add_column_if_missing(conn, "subscriptions", "secret TEXT NOT NULL DEFAULT ''", "secret")
        add_column_if_missing(conn, "subscriptions", "issued_at TEXT NOT NULL DEFAULT ''", "issued_at")
        add_column_if_missing(conn, "subscriptions", "connections_limit INTEGER NOT NULL DEFAULT 2", "connections_limit")
        add_column_if_missing(conn, "subscriptions", "devices_limit INTEGER NOT NULL DEFAULT 2", "devices_limit")

        add_column_if_missing(conn, "subscriptions", "remind_24_sent_at TEXT NOT NULL DEFAULT ''", "remind_24_sent_at")
        add_column_if_missing(conn, "subscriptions", "remind_1_sent_at TEXT NOT NULL DEFAULT ''", "remind_1_sent_at")
        add_column_if_missing(conn, "subscriptions", "expired_notice_sent_at TEXT NOT NULL DEFAULT ''", "expired_notice_sent_at")

        add_column_if_missing(conn, "payments", "payload TEXT NOT NULL DEFAULT ''", "payload")
        add_column_if_missing(conn, "payments", "telegram_payment_charge_id TEXT NOT NULL DEFAULT ''", "telegram_payment_charge_id")
        add_column_if_missing(conn, "payments", "provider_payment_charge_id TEXT NOT NULL DEFAULT ''", "provider_payment_charge_id")
        add_column_if_missing(conn, "payments", "subscription_expiration_date INTEGER NOT NULL DEFAULT 0", "subscription_expiration_date")
        add_column_if_missing(conn, "payments", "is_recurring INTEGER NOT NULL DEFAULT 0", "is_recurring")
        add_column_if_missing(conn, "payments", "is_first_recurring INTEGER NOT NULL DEFAULT 0", "is_first_recurring")
        add_column_if_missing(conn, "payments", "fulfilled INTEGER NOT NULL DEFAULT 0", "fulfilled")
        add_column_if_missing(conn, "payments", "paid_at TEXT NOT NULL DEFAULT ''", "paid_at")
        add_column_if_missing(conn, "payments", "refunded_at TEXT NOT NULL DEFAULT ''", "refunded_at")

        conn.execute(
            "UPDATE subscriptions SET proxy_type='socks5' WHERE proxy_type IS NULL OR proxy_type=''"
        )
        conn.execute(
            "UPDATE subscriptions SET host=? WHERE host IS NULL OR host=''",
            (settings.socks5_host,),
        )
        conn.execute(
            "UPDATE subscriptions SET port=? WHERE port IS NULL OR port=0",
            (settings.socks5_port,),
        )
        conn.execute("UPDATE subscriptions SET secret='' WHERE secret IS NULL")
        conn.execute(
            "UPDATE subscriptions SET issued_at=expires_at WHERE issued_at IS NULL OR issued_at=''"
        )
        conn.execute(
            "UPDATE subscriptions SET connections_limit=? WHERE connections_limit IS NULL OR connections_limit=0",
            (settings.default_connections_limit,),
        )
        conn.execute(
            "UPDATE subscriptions SET devices_limit=? WHERE devices_limit IS NULL OR devices_limit=0",
            (settings.default_devices_limit,),
        )
