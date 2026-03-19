from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from ..config import settings
from ..handlers.common import answer_screen
from ..repositories.audit import write_audit
from ..repositories.users import upsert_user
from ..services.payments import get_star_balance_text, get_star_transactions_text
from ..services.reports import (
    csv_file_from_query,
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
    reissue_subscription_credentials,
    reset_trial_for_user,
)
from ..ui.keyboards import admin_keyboard
from ..ui.texts import admin_commands_text, admin_panel_text
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


async def _send_csv(callback: CallbackQuery, filename: str, headers: list[str], query: str) -> None:
    if not await _admin_only(callback):
        return
    await callback.message.answer_document(csv_file_from_query(filename, headers, query), caption=f"Файл {filename} готов.")
    await callback.answer()


@router.callback_query(F.data == "export_users")
async def on_export_users(callback: CallbackQuery) -> None:
    await _send_csv(
        callback,
        "users.csv",
        ["user_id", "username", "first_name", "trial_used", "created_at", "updated_at"],
        "SELECT user_id, username, first_name, trial_used, created_at, updated_at FROM users ORDER BY user_id DESC",
    )


@router.callback_query(F.data == "export_subs")
async def on_export_subs(callback: CallbackQuery) -> None:
    await _send_csv(
        callback,
        "subscriptions.csv",
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
    await _send_csv(
        callback,
        "payments.csv",
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
    await _send_csv(
        callback,
        "active_subscriptions.csv",
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
