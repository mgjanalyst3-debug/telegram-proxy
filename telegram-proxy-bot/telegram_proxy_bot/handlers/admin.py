from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from ..config import settings
from ..db import db
from ..handlers.common import answer_screen
from ..repositories.audit import write_audit
from ..repositories.tickets import add_admin_reply, close_ticket, get_open_ticket
from ..services.payments import get_star_balance_text, get_star_transactions_text
from ..services.reports import (
    xlsx_file_from_query,
    format_active_subscriptions_text,
    format_audit_text,
    format_linux_users_text,
    format_recent_payments_text,
    format_recent_users_text,
    get_admin_stats_text,
)
from ..services.subscriptions import (
    expire_user_subscription,
    get_active_subscription,
    issue_or_extend_subscription,
    list_latest_subscription_snapshots,
    reissue_subscription_credentials,
    reset_trial_for_user,
)
from ..services.server_status import get_server_status
from ..ui.keyboards import admin_keyboard
from ..ui.texts import admin_commands_text, admin_panel_text, server_status_text
from ..utils import format_dt

router = Router(name="admin")


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids



def _parse_args(message: Message, expected: int) -> list[str] | None:
    parts = (message.text or "").strip().split()
    if len(parts) != expected:
        return None
    return parts[1:]


async def _admin_only(message_or_callback: Message | CallbackQuery) -> bool:
    user_id = message_or_callback.from_user.id
    if is_admin(user_id):
        return True
    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.answer("Недостаточно прав.", show_alert=True)
    else:
        await message_or_callback.answer("Недостаточно прав.")
    return False


def _parse_user_id_arg(message: Message) -> int | None:
    args = _parse_args(message, 2)
    if not args or not args[0].isdigit():
        return None
    return int(args[0])

def _parse_ticket_args(message: Message) -> tuple[int, str] | None:
    parts = (message.text or "").strip().split(maxsplit=2)
    if len(parts) < 3 or not parts[1].isdigit():
        return None
    return int(parts[1]), parts[2].strip()



@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    if not await _admin_only(message):
        return
    await message.answer(admin_panel_text(), reply_markup=admin_keyboard())


@router.message(Command("grant_30"))
async def cmd_grant_30(message: Message) -> None:
    if not await _admin_only(message):
        return
    args = _parse_args(message, 2)
    if not args or not args[0].isdigit():
        await message.answer("Использование: /grant_30 <user_id>")
        return
    target_user_id = int(args[0])
    sub = issue_or_extend_subscription(target_user_id, plan="30 дней", days=30)
    write_audit(target_user_id, sub.username, "grant_30", "выдано администратором бесплатно")
    await message.answer(f"Доступ продлен пользователю {target_user_id} до {format_dt(sub.expires_at)}")


@router.message(Command("grant_trial"))
async def cmd_grant_trial(message: Message) -> None:
    if not await _admin_only(message):
        return
    target_user_id = _parse_user_id_arg(message)
    if target_user_id is None:
        await message.answer("Использование: /grant_trial <user_id>")
        return
    sub = issue_or_extend_subscription(target_user_id, plan="пробная подписка (ручная)", hours=settings.trial_hours)
    write_audit(target_user_id, sub.username, "grant_trial", "выдан trial администратором")
    await message.answer(f"Пробный доступ выдан пользователю {target_user_id} до {format_dt(sub.expires_at)}")


@router.message(Command("extend"))
async def cmd_extend(message: Message) -> None:
    if not await _admin_only(message):
        return
    args = _parse_args(message, 3)
    if not args or not args[0].isdigit() or not args[1].isdigit():
        await message.answer("Использование: /extend <user_id> <days>")
        return
    target_user_id = int(args[0])
    days = int(args[1])
    sub = issue_or_extend_subscription(target_user_id, plan="30 дней", days=days)
    write_audit(target_user_id, sub.username, "extend", f"продлено администратором на {days} дней")
    await message.answer(f"Подписка пользователя {target_user_id} активна до {format_dt(sub.expires_at)}")


@router.message(Command("reset_trial"))
async def cmd_reset_trial(message: Message) -> None:
    if not await _admin_only(message):
        return
    args = _parse_args(message, 2)
    if not args or not args[0].isdigit():
        await message.answer("Использование: /reset_trial <user_id>")
        return
    target_user_id = int(args[0])
    reset_trial_for_user(target_user_id)
    write_audit(target_user_id, "-", "reset_trial", "сброшен пробный период")
    await message.answer(f"Пробный период для {target_user_id} сброшен.")


@router.message(Command("expire_sub"))
async def cmd_expire_sub(message: Message) -> None:
    if not await _admin_only(message):
        return
    args = _parse_args(message, 2)
    if not args or not args[0].isdigit():
        await message.answer("Использование: /expire_sub <user_id>")
        return
    target_user_id = int(args[0])
    sub = get_active_subscription(target_user_id)
    if not sub:
        await message.answer("У пользователя нет активной подписки.")
        return
    expire_user_subscription(target_user_id, username=sub.username)
    write_audit(target_user_id, sub.username, "expire_sub", "подписка завершена администратором")
    await message.answer(f"Подписка пользователя {target_user_id} завершена.")


@router.message(Command("expire"))
async def cmd_expire(message: Message) -> None:
    await cmd_expire_sub(message)


@router.message(Command("reissue"))
async def cmd_reissue(message: Message) -> None:
    if not await _admin_only(message):
        return
    args = _parse_args(message, 2)
    if not args or not args[0].isdigit():
        await message.answer("Использование: /reissue <user_id>")
        return
    target_user_id = int(args[0])
    sub = reissue_subscription_credentials(target_user_id)
    if not sub:
        await message.answer("У пользователя нет активной подписки.")
        return
    write_audit(target_user_id, sub.username, "reissue", "пароль перевыпущен администратором")
    await message.answer(f"Пользователю {target_user_id} перевыпущен новый персональный доступ.")


@router.message(Command("delete_sub"))
async def cmd_delete_sub(message: Message) -> None:
    if not await _admin_only(message):
        return
    target_user_id = _parse_user_id_arg(message)
    if target_user_id is None:
        await message.answer("Использование: /delete_sub <user_id>")
        return
    with db() as conn:
        deleted = conn.execute("DELETE FROM subscriptions WHERE user_id=?", (target_user_id,)).rowcount
    write_audit(target_user_id, "-", "delete_sub", f"удалено подписок: {deleted}")
    await message.answer(f"Подписки пользователя {target_user_id} удалены: <code>{deleted}</code>.")


@router.message(Command("set_limit"))
async def cmd_set_limit(message: Message) -> None:
    if not await _admin_only(message):
        return
    args = _parse_args(message, 3)
    if not args or not args[0].isdigit() or not args[1].isdigit():
        await message.answer("Использование: /set_limit <user_id> <n>")
        return
    target_user_id = int(args[0])
    new_limit = max(1, min(100, int(args[1])))
    with db() as conn:
        updated = conn.execute(
            "UPDATE subscriptions SET connections_limit=? WHERE user_id=? AND status='active'",
            (new_limit, target_user_id),
        ).rowcount
    write_audit(target_user_id, "-", "set_limit", f"connections_limit={new_limit}, обновлено={updated}")
    await message.answer(f"Лимит подключений обновлен до <code>{new_limit}</code>. Изменено записей: <code>{updated}</code>.")


@router.message(Command("set_devices"))
async def cmd_set_devices(message: Message) -> None:
    if not await _admin_only(message):
        return
    args = _parse_args(message, 3)
    if not args or not args[0].isdigit() or not args[1].isdigit():
        await message.answer("Использование: /set_devices <user_id> <n>")
        return
    target_user_id = int(args[0])
    new_limit = max(1, min(100, int(args[1])))
    with db() as conn:
        updated = conn.execute(
            "UPDATE subscriptions SET devices_limit=? WHERE user_id=? AND status='active'",
            (new_limit, target_user_id),
        ).rowcount
    write_audit(target_user_id, "-", "set_devices", f"devices_limit={new_limit}, обновлено={updated}")
    await message.answer(f"Лимит устройств обновлен до <code>{new_limit}</code>. Изменено записей: <code>{updated}</code>.")


@router.message(Command("payments"))
async def cmd_payments(message: Message) -> None:
    if not await _admin_only(message):
        return
    target_user_id = _parse_user_id_arg(message)
    if target_user_id is None:
        await message.answer("Использование: /payments <user_id>")
        return
    with db() as conn:
        rows = conn.execute(
            "SELECT id, amount, currency, status, payload, created_at FROM payments WHERE user_id=? ORDER BY id DESC LIMIT 20",
            (target_user_id,),
        ).fetchall()
    if not rows:
        await message.answer("У пользователя нет платежей.")
        return
    lines = ["<b>💳 История платежей</b>"]
    for row in rows:
        lines.append(
            f"#{row['id']} • <code>{row['amount']} {row['currency']}</code> • "
            f"<code>{row['status']}</code> • {format_dt(row['created_at'])} • <code>{row['payload']}</code>"
        )
    await message.answer("\n".join(lines))


@router.message(Command("mark_paid"))
async def cmd_mark_paid(message: Message) -> None:
    if not await _admin_only(message):
        return
    args = _parse_args(message, 3)
    if not args or not args[0].isdigit() or not args[1].isdigit():
        await message.answer("Использование: /mark_paid <user_id> <days>")
        return
    target_user_id = int(args[0])
    days = int(args[1])
    sub = issue_or_extend_subscription(target_user_id, plan="ручная активация", days=days)
    with db() as conn:
        conn.execute(
            """
            INSERT INTO payments (user_id, payload, amount, currency, status, fulfilled, paid_at, created_at, updated_at)
            VALUES (?, ?, 0, 'XTR', 'paid', 1, datetime('now'), datetime('now'), datetime('now'))
            """,
            (target_user_id, f"manual_paid_{target_user_id}_{sub.row_id}"),
        )
    write_audit(target_user_id, sub.username, "mark_paid", f"ручная активация на {days} дней")
    await message.answer(f"Подписка активирована вручную до {format_dt(sub.expires_at)}.")


@router.message(Command("refund"))
async def cmd_refund(message: Message) -> None:
    if not await _admin_only(message):
        return
    args = _parse_args(message, 3)
    if not args or not args[0].isdigit() or not args[1].isdigit():
        await message.answer("Использование: /refund <user_id> <payment_id>")
        return
    target_user_id = int(args[0])
    payment_id = int(args[1])
    with db() as conn:
        updated = conn.execute(
            "UPDATE payments SET status='refunded', refunded_at=datetime('now'), updated_at=datetime('now') WHERE id=? AND user_id=?",
            (payment_id, target_user_id),
        ).rowcount
    if not updated:
        await message.answer("Платеж не найден.")
        return
    write_audit(target_user_id, "-", "refund", f"payment_id={payment_id}")
    await message.answer(f"Платеж #{payment_id} отмечен как refunded.")
@router.message(Command("reply"))
async def cmd_reply(message: Message, bot: Bot) -> None:
    if not await _admin_only(message):
        return
    parsed = _parse_ticket_args(message)
    if not parsed:
        await message.answer("Использование: /reply <ticket_id> <text>")
        return
    ticket_id, reply_text = parsed
    ticket = get_open_ticket(ticket_id)
    if not ticket:
        await message.answer("Открытый тикет не найден.")
        return
    add_admin_reply(ticket_id, message.from_user.id, reply_text)
    write_audit(ticket["user_id"], "-", "ticket_reply", f"ticket_id={ticket_id}")
    await bot.send_message(
        ticket["user_id"],
        (
            f"<b>💬 Ответ по тикету #{ticket_id}</b>\n\n"
            f"{reply_text}\n\n"
            "Если вопрос решен — можете ничего не делать. Иначе создайте новый тикет через раздел поддержки."
        ),
    )
    await message.answer(f"Ответ по тикету <code>#{ticket_id}</code> отправлен пользователю.")


@router.message(Command("close"))
async def cmd_close_ticket(message: Message, bot: Bot) -> None:
    if not await _admin_only(message):
        return
    args = _parse_args(message, 2)
    if not args or not args[0].isdigit():
        await message.answer("Использование: /close <ticket_id>")
        return
    ticket_id = int(args[0])
    ticket = get_open_ticket(ticket_id)
    if not ticket:
        await message.answer("Открытый тикет не найден.")
        return
    if not close_ticket(ticket_id, message.from_user.id):
        await message.answer("Не удалось закрыть тикет.")
        return
    write_audit(ticket["user_id"], "-", "ticket_closed", f"ticket_id={ticket_id}")
    await bot.send_message(
        ticket["user_id"],
        f"✅ Тикет <code>#{ticket_id}</code> закрыт. Если понадобится помощь — создайте новый тикет в разделе поддержки.",
    )
    await message.answer(f"Тикет <code>#{ticket_id}</code> закрыт.")



@router.message(Command("user"))
async def cmd_user(message: Message) -> None:
    if not await _admin_only(message):
        return
    target_user_id = _parse_user_id_arg(message)
    if target_user_id is None:
        await message.answer("Использование: /user <user_id>")
        return
    with db() as conn:
        user = conn.execute("SELECT * FROM users WHERE user_id=?", (target_user_id,)).fetchone()
    sub = get_active_subscription(target_user_id)
    if not user:
        await message.answer("Пользователь не найден в БД.")
        return
    lines = [
        "<b>👤 Карточка пользователя</b>",
        f"ID: <code>{user['user_id']}</code>",
        f"Username: <code>{user['username'] or '-'}</code>",
        f"Имя: <code>{user['first_name'] or '-'}</code>",
        f"Trial used: <code>{'да' if user['trial_used'] else 'нет'}</code>",
        f"Бан: <code>{'да' if user['is_banned'] else 'нет'}</code>",
        f"Заметка: <code>{user['admin_note'] or '-'}</code>",
        f"Создан: <code>{format_dt(user['created_at'])}</code>",
    ]
    if sub:
        lines.extend(
            [
                "",
                "<b>Активная подписка</b>",
                f"Логин: <code>{sub.username}</code>",
                f"Доступ до: <code>{format_dt(sub.expires_at)}</code>",
                f"Лимиты: <code>{sub.connections_limit}</code>/<code>{sub.devices_limit}</code>",
            ]
        )
    await message.answer("\n".join(lines))


@router.message(Command("ban"))
async def cmd_ban(message: Message) -> None:
    if not await _admin_only(message):
        return
    target_user_id = _parse_user_id_arg(message)
    if target_user_id is None:
        await message.answer("Использование: /ban <user_id>")
        return
    with db() as conn:
        conn.execute("UPDATE users SET is_banned=1, updated_at=datetime('now') WHERE user_id=?", (target_user_id,))
    write_audit(target_user_id, "-", "ban", "пользователь заблокирован")
    await message.answer(f"Пользователь {target_user_id} заблокирован.")


@router.message(Command("unban"))
async def cmd_unban(message: Message) -> None:
    if not await _admin_only(message):
        return
    target_user_id = _parse_user_id_arg(message)
    if target_user_id is None:
        await message.answer("Использование: /unban <user_id>")
        return
    with db() as conn:
        conn.execute("UPDATE users SET is_banned=0, updated_at=datetime('now') WHERE user_id=?", (target_user_id,))
    write_audit(target_user_id, "-", "unban", "блокировка снята")
    await message.answer(f"Пользователь {target_user_id} разблокирован.")


@router.message(Command("note"))
async def cmd_note(message: Message) -> None:
    if not await _admin_only(message):
        return
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3 or not parts[1].isdigit():
        await message.answer("Использование: /note <user_id> <text>")
        return
    target_user_id = int(parts[1])
    note = parts[2].strip()
    with db() as conn:
        conn.execute("UPDATE users SET admin_note=?, updated_at=datetime('now') WHERE user_id=?", (note, target_user_id))
    write_audit(target_user_id, "-", "note", note)
    await message.answer(f"Заметка для {target_user_id} сохранена.")


@router.message(Command("users_active"))
async def cmd_users_active(message: Message) -> None:
    if not await _admin_only(message):
        return
    with db() as conn:
        rows = conn.execute(
            """
            SELECT user_id, username, expires_at FROM subscriptions
            WHERE status='active' AND id IN (
                SELECT MAX(id) FROM subscriptions WHERE status='active' GROUP BY user_id
            )
            ORDER BY expires_at ASC LIMIT 50
            """
        ).fetchall()
    if not rows:
        await message.answer("Активных пользователей нет.")
        return
    text = ["<b>✅ Активные пользователи</b>"]
    text.extend(
        f"<code>{row['user_id']}</code> • <code>{row['username']}</code> • до {format_dt(row['expires_at'])}" for row in rows
    )
    await message.answer("\n".join(text))


@router.message(Command("users_expired"))
async def cmd_users_expired(message: Message) -> None:
    if not await _admin_only(message):
        return
    with db() as conn:
        rows = conn.execute(
            """
            SELECT user_id, username, expires_at FROM subscriptions
            WHERE status='expired' AND id IN (
                SELECT MAX(id) FROM subscriptions GROUP BY user_id
            )
            ORDER BY expires_at DESC LIMIT 50
            """
        ).fetchall()
    if not rows:
        await message.answer("Истекших пользователей нет.")
        return
    text = ["<b>⌛ Истекшие пользователи</b>"]
    text.extend(
        f"<code>{row['user_id']}</code> • <code>{row['username']}</code> • истекла {format_dt(row['expires_at'])}" for row in rows
    )
    await message.answer("\n".join(text))


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, bot: Bot) -> None:
    if not await _admin_only(message):
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /broadcast <text>")
        return
    text = parts[1]
    with db() as conn:
        user_ids = [row["user_id"] for row in conn.execute("SELECT user_id FROM users").fetchall()]
    sent = 0
    for user_id in user_ids:
        try:
            await bot.send_message(user_id, text)
            sent += 1
        except Exception:
            continue
    await message.answer(f"Рассылка завершена. Успешно: <code>{sent}</code> / <code>{len(user_ids)}</code>.")


@router.message(Command("broadcast_active"))
async def cmd_broadcast_active(message: Message, bot: Bot) -> None:
    if not await _admin_only(message):
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /broadcast_active <text>")
        return
    text = parts[1]
    with db() as conn:
        user_ids = [row["user_id"] for row in conn.execute("SELECT DISTINCT user_id FROM subscriptions WHERE status='active'").fetchall()]
    sent = 0
    for user_id in user_ids:
        try:
            await bot.send_message(user_id, text)
            sent += 1
        except Exception:
            continue
    await message.answer(f"Рассылка по активным завершена. Успешно: <code>{sent}</code> / <code>{len(user_ids)}</code>.")


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if not await _admin_only(message):
        return
    await message.answer(get_admin_stats_text())


@router.message(Command("health"))
async def cmd_health(message: Message, bot: Bot) -> None:
    if not await _admin_only(message):
        return
    db_ok = True
    try:
        with db() as conn:
            conn.execute("SELECT 1").fetchone()
    except Exception:
        db_ok = False
    stars_ok = True
    try:
        await bot.get_my_star_balance()
    except Exception:
        stars_ok = False
    latest = list_latest_subscription_snapshots(1)
    proxy_line = "нет данных"
    if latest:
        status = await get_server_status(latest[0])
        proxy_line = server_status_text(status).splitlines()[2].replace("<b>Подключение:</b> ", "")
    await message.answer(
        "<b>🩺 Health-check</b>\n\n"
        f"Бот: <code>ok</code>\n"
        f"БД: <code>{'ok' if db_ok else 'fail'}</code>\n"
        f"Платежи (Stars API): <code>{'ok' if stars_ok else 'fail'}</code>\n"
        f"Прокси: <code>{proxy_line}</code>"
    )


@router.message(Command("whoami"))
async def cmd_whoami(message: Message) -> None:
    if not await _admin_only(message):
        return
    await message.answer(
        "<b>👤 Кто я</b>\n\n"
        f"Ваш ID: <code>{message.from_user.id}</code>\n"
        f"Username: <code>@{message.from_user.username or '-'}</code>\n"
        f"Админ: <code>{'да' if is_admin(message.from_user.id) else 'нет'}</code>"
    )


@router.message(Command("star_balance"))
async def cmd_star_balance(message: Message, bot: Bot) -> None:
    if not await _admin_only(message):
        return
    await message.answer(await get_star_balance_text(bot))


@router.message(Command("star_tx"))
async def cmd_star_tx(message: Message, bot: Bot) -> None:
    if not await _admin_only(message):
        return
    parts = (message.text or "").split()
    limit = 10
    if len(parts) >= 2 and parts[1].isdigit():
        limit = max(1, min(20, int(parts[1])))
    await message.answer(await get_star_transactions_text(bot, limit=limit))


@router.callback_query(F.data == "admin_panel")
async def on_admin_panel(callback: CallbackQuery) -> None:
    if not await _admin_only(callback):
        return
    await answer_screen(callback, admin_panel_text(), admin_keyboard())


@router.callback_query(F.data == "admin_commands")
async def on_admin_commands(callback: CallbackQuery) -> None:
    if not await _admin_only(callback):
        return
    await answer_screen(callback, admin_commands_text(), admin_keyboard())


@router.callback_query(F.data == "admin_stats")
async def on_admin_stats(callback: CallbackQuery) -> None:
    if not await _admin_only(callback):
        return
    await answer_screen(callback, get_admin_stats_text(), admin_keyboard())


@router.callback_query(F.data == "admin_users")
async def on_admin_users(callback: CallbackQuery) -> None:
    if not await _admin_only(callback):
        return
    await answer_screen(callback, format_recent_users_text(), admin_keyboard())


@router.callback_query(F.data == "admin_subs")
async def on_admin_subs(callback: CallbackQuery) -> None:
    if not await _admin_only(callback):
        return
    await answer_screen(callback, format_active_subscriptions_text(), admin_keyboard())

@router.callback_query(F.data == "admin_payments")
async def on_admin_payments(callback: CallbackQuery) -> None:
    if not await _admin_only(callback):
        return
    await answer_screen(callback, format_recent_payments_text(), admin_keyboard())


@router.callback_query(F.data == "admin_linux_users")
async def on_admin_linux_users(callback: CallbackQuery) -> None:
    if not await _admin_only(callback):
        return
    await answer_screen(callback, format_linux_users_text(), admin_keyboard())


@router.callback_query(F.data == "admin_audit")
async def on_admin_audit(callback: CallbackQuery) -> None:
    if not await _admin_only(callback):
        return
    await answer_screen(callback, format_audit_text(), admin_keyboard())


async def _send_xlsx(callback: CallbackQuery, filename: str, headers: list[str], query: str) -> None:
    if not await _admin_only(callback):
        return
    await callback.message.answer_document(xlsx_file_from_query(filename, headers, query), caption=f"Файл {filename} готов.")
    await callback.answer()


@router.callback_query(F.data == "export_users")
async def on_export_users(callback: CallbackQuery) -> None:
    await _send_xlsx(
        callback,
        "users.xlsx",
        ["user_id", "username", "first_name", "trial_used", "created_at", "updated_at"],
        "SELECT user_id, username, first_name, trial_used, created_at, updated_at FROM users ORDER BY user_id DESC",
    )


@router.callback_query(F.data == "export_subs")
async def on_export_subs(callback: CallbackQuery) -> None:
    await _send_xlsx(
        callback,
        "subscriptions.xlsx",
        [
            "id",
            "user_id",
            "plan",
            "proxy_type",
            "host",
            "port",
            "username",
            "password",
            "status",
            "issued_at",
            "expires_at",
            "connections_limit",
            "devices_limit",
        ],
        "SELECT id, user_id, plan, proxy_type, host, port, username, password, status, issued_at, expires_at, connections_limit, devices_limit FROM subscriptions ORDER BY id DESC",
    )


@router.callback_query(F.data == "export_payments")
async def on_export_payments(callback: CallbackQuery) -> None:
    await _send_xlsx(
        callback,
        "payments.xlsx",
        [
            "id",
            "user_id",
            "payload",
            "amount",
            "currency",
            "status",
            "telegram_payment_charge_id",
            "provider_payment_charge_id",
            "fulfilled",
            "created_at",
            "updated_at",
        ],
        "SELECT id, user_id, payload, amount, currency, status, telegram_payment_charge_id, provider_payment_charge_id, fulfilled, created_at, updated_at FROM payments ORDER BY id DESC",
    )


@router.callback_query(F.data == "export_active_subs")
async def on_export_active_subs(callback: CallbackQuery) -> None:
    await _send_xlsx(
        callback,
        "active_subscriptions.xlsx",
        [
            "id",
            "user_id",
            "plan",
            "host",
            "port",
            "username",
            "status",
            "issued_at",
            "expires_at",
            "connections_limit",
            "devices_limit",
        ],
        "SELECT id, user_id, plan, host, port, username, status, issued_at, expires_at, connections_limit, devices_limit FROM subscriptions WHERE status='active' ORDER BY id DESC",
    )
