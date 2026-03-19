from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message, User

from ..config import settings
from ..handlers.common import answer_screen, show_menu
from ..repositories.audit import write_audit
from ..repositories.users import has_used_trial, mark_trial_used, upsert_user
from ..services.payments import send_stars_invoice
from ..services.subscriptions import get_active_subscription, issue_or_extend_subscription
from ..ui.keyboards import access_keyboard, back_keyboard, buy_keyboard, menu_keyboard
from ..ui.texts import (
    access_text,
    buy_text,
    faq_text,
    paysupport_text,
    setup_text,
    start_text,
    status_text,
    support_screen_text,
    trial_activated_text,
)

logger = logging.getLogger(__name__)
router = Router(name="user")


async def handle_trial(target: Message | CallbackQuery, user: User) -> None:
    upsert_user(user.id, user.username, user.first_name)
    current = get_active_subscription(user.id)
    if current:
        await answer_screen(
            target,
            "У вас уже есть активный доступ. Откройте раздел «📦 Мой доступ».",
            menu_keyboard(user.id),
        )
        return
    if has_used_trial(user.id):
        await answer_screen(
            target,
            "Пробная подписка уже была использована. Вы можете перейти к оплате и сразу активировать подписку.",
            menu_keyboard(user.id),
        )
        return
    try:
        sub = issue_or_extend_subscription(user.id, plan="пробная подписка", hours=settings.trial_hours)
    except Exception as exc:
        logger.exception("Не удалось выдать trial: %s", exc)
        await answer_screen(
            target,
            "Не удалось активировать пробный доступ. Попробуйте еще раз или напишите в поддержку.",
            menu_keyboard(user.id),
        )
        return
    mark_trial_used(user.id)
    write_audit(user.id, sub.username, "trial_issued", f"пробная подписка до {sub.expires_at}")
    await answer_screen(target, trial_activated_text(sub), access_keyboard(sub))


async def send_access(target: Message | CallbackQuery, user_id: int) -> None:
    sub = get_active_subscription(user_id)
    if not sub:
        await answer_screen(
            target,
            "Сейчас у вас нет активного доступа. Вы можете активировать пробную подписку или оформить подписку на 30 дней.",
            back_keyboard(),
        )
        return
    await answer_screen(target, access_text(sub), access_keyboard(sub))


async def send_status(target: Message | CallbackQuery, user_id: int) -> None:
    sub = get_active_subscription(user_id)
    if not sub:
        await answer_screen(target, "Сейчас у вас нет активной подписки.", back_keyboard())
        return
    await answer_screen(target, status_text(sub), back_keyboard())


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    upsert_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await message.answer(start_text(), reply_markup=menu_keyboard(message.from_user.id), disable_web_page_preview=True)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    upsert_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await message.answer(faq_text(), reply_markup=menu_keyboard(message.from_user.id), disable_web_page_preview=True)


@router.message(Command("trial"))
async def cmd_trial(message: Message) -> None:
    await handle_trial(message, message.from_user)


@router.message(Command("buy"))
async def cmd_buy(message: Message) -> None:
    upsert_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await message.answer(buy_text(), reply_markup=buy_keyboard())


@router.message(Command("myproxy"))
async def cmd_myproxy(message: Message) -> None:
    upsert_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await send_access(message, message.from_user.id)


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    upsert_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await send_status(message, message.from_user.id)


@router.message(Command("paysupport"))
async def cmd_paysupport(message: Message) -> None:
    upsert_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await message.answer(paysupport_text(), reply_markup=menu_keyboard(message.from_user.id))


@router.callback_query(F.data == "menu")
async def on_menu(callback: CallbackQuery) -> None:
    await show_menu(callback)


@router.callback_query(F.data == "trial")
async def on_trial(callback: CallbackQuery) -> None:
    await callback.answer()
    await handle_trial(callback, callback.from_user)


@router.callback_query(F.data == "buy")
async def on_buy(callback: CallbackQuery) -> None:
    await answer_screen(callback, buy_text(), buy_keyboard())


@router.callback_query(F.data == "pay_stars")
async def on_pay_stars(callback: CallbackQuery, bot: Bot) -> None:
    await callback.answer()
    await send_stars_invoice(callback.message.chat.id, callback.from_user, bot)


@router.callback_query(F.data == "my_access")
async def on_access(callback: CallbackQuery) -> None:
    await send_access(callback, callback.from_user.id)


@router.callback_query(F.data == "status")
async def on_status(callback: CallbackQuery) -> None:
    await send_status(callback, callback.from_user.id)


@router.callback_query(F.data == "setup")
async def on_setup(callback: CallbackQuery) -> None:
    await answer_screen(callback, setup_text(), back_keyboard())


@router.callback_query(F.data == "faq")
async def on_faq(callback: CallbackQuery) -> None:
    await answer_screen(callback, faq_text(), back_keyboard())


@router.callback_query(F.data == "support")
async def on_support(callback: CallbackQuery) -> None:
    await answer_screen(callback, support_screen_text(), back_keyboard())


@router.callback_query(F.data == "show_username")
async def on_show_username(callback: CallbackQuery) -> None:
    sub = get_active_subscription(callback.from_user.id)
    if not sub:
        await callback.answer("У вас нет активного доступа.", show_alert=True)
        return
    await callback.answer(f"Логин: {sub.username}", show_alert=True)


@router.callback_query(F.data == "show_password")
async def on_show_password(callback: CallbackQuery) -> None:
    sub = get_active_subscription(callback.from_user.id)
    if not sub:
        await callback.answer("У вас нет активного доступа.", show_alert=True)
        return
    await callback.answer(f"Пароль: {sub.password}", show_alert=True)
