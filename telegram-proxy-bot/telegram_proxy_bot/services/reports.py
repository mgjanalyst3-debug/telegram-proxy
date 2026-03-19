from __future__ import annotations

import io
from html import escape
from zipfile import ZIP_DEFLATED, ZipFile

from aiogram.types import BufferedInputFile

from ..config import settings
from ..repositories import payments as payments_repo
from ..repositories import users as users_repo
from ..repositories.audit import write_audit
from ..services import linux_users
from ..services.subscriptions import list_active_subscriptions, list_latest_subscription_snapshots
from ..utils import format_dt
from ..db import db



def get_admin_stats_text() -> str:
    with db() as conn:
        users_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        trial_count = conn.execute("SELECT COUNT(*) FROM users WHERE trial_used = 1").fetchone()[0]
        active_subs = conn.execute("SELECT COUNT(*) FROM subscriptions WHERE status='active'").fetchone()[0]
        paid_count = conn.execute("SELECT COUNT(*) FROM payments WHERE status='paid'").fetchone()[0]
        revenue_xtr = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='paid' AND currency='XTR'"
        ).fetchone()[0]
    return (
        f"<b>{settings.bot_brand}</b>\n\n<b>📈 Статистика</b>\n\n"
        f"👥 Пользователей: <code>{users_count}</code>\n"
        f"🎁 Использовали пробную подписку: <code>{trial_count}</code>\n"
        f"📦 Активных подписок: <code>{active_subs}</code>\n"
        f"💳 Успешных платежей: <code>{paid_count}</code>\n"
        f"⭐ Выручка, XTR: <code>{revenue_xtr}</code>"
    )



def format_recent_users_text(limit: int = 15) -> str:
    rows = users_repo.list_recent_users(limit)
    if not rows:
        return "<b>👥 Пользователи</b>\n\nДанных пока нет."
    chunks = []
    for row in rows:
        chunks.append(
            "\n".join(
                [
                    f"ID: <code>{row['user_id']}</code>",
                    f"Username: <code>{row['username'] or '-'}</code>",
                    f"Имя: <code>{row['first_name'] or '-'}</code>",
                    f"Пробная подписка: <code>{'да' if row['trial_used'] else 'нет'}</code>",
                    f"Создан: <code>{format_dt(row['created_at'])}</code>",
                ]
            )
        )
    return "<b>👥 Последние пользователи</b>\n\n" + "\n\n".join(chunks)



def format_active_subscriptions_text(limit: int = 15) -> str:
    rows = list_active_subscriptions(limit)
    if not rows:
        return "<b>📦 Актуальные подписки</b>\n\nАктивных подписок пока нет."
    chunks = []
    for sub in rows:
        chunks.append(
            "\n".join(
                [
                    f"Подписка: <code>{sub.row_id}</code>",
                    f"Пользователь: <code>{sub.user_id}</code>",
                    f"Тариф: <code>{sub.plan}</code>",
                    f"Статус: <code>{sub.status}</code>",
                    f"Логин: <code>{sub.username}</code>",
                    f"Порт: <code>{sub.port}</code>",
                    f"Лимит подключений: <code>{sub.connections_limit}</code>",
                    f"Лимит устройств: <code>{sub.devices_limit}</code>",
                    f"Доступ до: <code>{format_dt(sub.expires_at)}</code>",
                ]
            )
        )
    return "<b>📦 Актуальные подписки</b>\n\n" + "\n\n".join(chunks)



def format_recent_payments_text(limit: int = 15) -> str:
    rows = payments_repo.list_recent_payments(limit)
    if not rows:
        return "<b>💳 Платежи</b>\n\nДанных пока нет."
    chunks = []
    for row in rows:
        charge_id = row["telegram_payment_charge_id"] or "-"
        chunks.append(
            "\n".join(
                [
                    f"Платеж: <code>{row['id']}</code>",
                    f"Пользователь: <code>{row['user_id']}</code>",
                    f"Сумма: <code>{row['amount']} {row['currency']}</code>",
                    f"Статус: <code>{row['status']}</code>",
                    f"Payload: <code>{row['payload']}</code>",
                    f"Charge ID: <code>{charge_id}</code>",
                    f"Выдан доступ: <code>{'да' if row['fulfilled'] else 'нет'}</code>",
                    f"Создан: <code>{format_dt(row['created_at'])}</code>",
                ]
            )
        )
    return "<b>💳 Последние платежи</b>\n\n" + "\n\n".join(chunks)



def format_linux_users_text(limit: int = 15) -> str:
    rows = list_latest_subscription_snapshots(limit)
    if not rows:
        return "<b>🖥 Linux-учетки</b>\n\nДанных пока нет."
    chunks = []
    for sub in rows:
        exists = linux_users.linux_user_exists(sub.username)
        locked = linux_users.linux_user_locked(sub.username) if exists else False
        chunks.append(
            "\n".join(
                [
                    f"Пользователь: <code>{sub.user_id}</code>",
                    f"Linux-логин: <code>{sub.username}</code>",
                    f"Есть в системе: <code>{'да' if exists else 'нет'}</code>",
                    f"Заблокирован: <code>{'да' if locked else 'нет'}</code>",
                    f"Статус подписки: <code>{sub.status}</code>",
                    f"Доступ до: <code>{format_dt(sub.expires_at)}</code>",
                ]
            )
        )
    return "<b>🖥 Linux-учетки</b>\n\n" + "\n\n".join(chunks)



def format_audit_text(limit: int = 20) -> str:
    with db() as conn:
        rows = conn.execute(
            "SELECT id, user_id, username, action, details, created_at FROM audit_log ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    if not rows:
        return "<b>🧾 Аудит</b>\n\nДанных пока нет."
    chunks = []
    for row in rows:
        chunks.append(
            "\n".join(
                [
                    f"Событие: <code>{row['id']}</code>",
                    f"User ID: <code>{row['user_id']}</code>",
                    f"Логин: <code>{row['username'] or '-'}</code>",
                    f"Действие: <code>{row['action']}</code>",
                    f"Подробности: <code>{row['details'] or '-'}</code>",
                    f"Время: <code>{format_dt(row['created_at'])}</code>",
                ]
            )
        )
    return "<b>🧾 Последние действия</b>\n\n" + "\n\n".join(chunks)



def xlsx_file_from_query(filename: str, headers: list[str], query: str) -> BufferedInputFile:
    with db() as conn:
        rows = conn.execute(query).fetchall()
    table_rows = [headers]
    for row in rows:
        table_rows.append([row[h] for h in headers])

    def _column_name(col_index: int) -> str:
        name = ""
        idx = col_index
        while idx > 0:
            idx, rem = divmod(idx - 1, 26)
            name = chr(65 + rem) + name
        return name

    def _cell_xml(row_idx: int, col_idx: int, value: object) -> str:
        cell_ref = f"{_column_name(col_idx)}{row_idx}"
        if value is None:
            return f'<c r="{cell_ref}"/>'
        text = escape(str(value))
        return f'<c r="{cell_ref}" t="inlineStr"><is><t>{text}</t></is></c>'

    sheet_rows_xml = []
    for row_idx, values in enumerate(table_rows, start=1):
        cells_xml = "".join(_cell_xml(row_idx, col_idx, value) for col_idx, value in enumerate(values, start=1))
        sheet_rows_xml.append(f'<row r="{row_idx}">{cells_xml}</row>')

    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{''.join(sheet_rows_xml)}</sheetData>"
        "</worksheet>"
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Report" sheetId="1" r:id="rId1"/></sheets>'
        "</workbook>"
    )
    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )
    workbook_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        "</Relationships>"
    )
    content_types_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>"
    )

    output = io.BytesIO()
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as xlsx:
        xlsx.writestr("[Content_Types].xml", content_types_xml)
        xlsx.writestr("_rels/.rels", rels_xml)
        xlsx.writestr("xl/workbook.xml", workbook_xml)
        xlsx.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        xlsx.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    output.seek(0)
    return BufferedInputFile(output.getvalue(), filename=filename)
