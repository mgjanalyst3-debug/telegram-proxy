from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message, User

from ..config import settings
from ..handlers.common import answer_screen, show_menu
from ..repositories.audit import count_recent_user_actions, write_audit
from ..repositories.tickets import clear_ticket_draft, create_ticket, create_ticket_draft, has_ticket_draft
from ..repositories.users import has_used_trial, is_user_banned, mark_trial_used, upsert_user
from ..services.payments import send_stars_invoice
from ..services.server_status import get_server_status
from ..services.subscriptions import (
    get_active_subscription,
    issue_or_extend_subscription,
    reissue_subscription_credentials,
)
from ..ui.keyboards import access_keyboard, back_keyboard, buy_keyboard, menu_keyboard, support_keyboard
from ..ui.texts import (
    access_text,
    buy_text,
    faq_text,
    paysupport_text,
    setup_text,
    start_text,
    server_status_text,
    status_text,
    support_screen_text,
    trial_activated_text,
)

logger = logging.getLogger(__name__)
router = Router(name="user")


async def _ensure_not_banned(target: Message | CallbackQuery, user: User) -> bool:
    if not is_user_banned(user.id):
        return True
    await answer_screen(
        target,
        "Р’Р°С€ Р°РєРєР°СѓРЅС‚ РІСЂРµРјРµРЅРЅРѕ Р·Р°Р±Р»РѕРєРёСЂРѕРІР°РЅ. Р”Р»СЏ СѓС‚РѕС‡РЅРµРЅРёСЏ РґРµС‚Р°Р»РµР№ РѕР±СЂР°С‚РёС‚РµСЃСЊ РІ РїРѕРґРґРµСЂР¶РєСѓ.",
        back_keyboard(),
    )
    return False


async def handle_trial(target: Message | CallbackQuery, user: User) -> None:
    upsert_user(user.id, user.username, user.first_name)
    if not await _ensure_not_banned(target, user):
        return
    current = get_active_subscription(user.id)
    if current:
        await answer_screen(
            target,
            "РЈ РІР°СЃ СѓР¶Рµ РµСЃС‚СЊ Р°РєС‚РёРІРЅС‹Р№ РґРѕСЃС‚СѓРї. РћС‚РєСЂРѕР№С‚Рµ СЂР°Р·РґРµР» В«рџ“¦ РњРѕР№ РґРѕСЃС‚СѓРїВ».",
            menu_keyboard(user.id),
        )
        return
    if has_used_trial(user.id):
        await answer_screen(
            target,
            "РџСЂРѕР±РЅР°СЏ РїРѕРґРїРёСЃРєР° СѓР¶Рµ Р±С‹Р»Р° РёСЃРїРѕР»СЊР·РѕРІР°РЅР°. Р’С‹ РјРѕР¶РµС‚Рµ РїРµСЂРµР№С‚Рё Рє РѕРїР»Р°С‚Рµ Рё СЃСЂР°Р·Сѓ Р°РєС‚РёРІРёСЂРѕРІР°С‚СЊ РїРѕРґРїРёСЃРєСѓ.",
            menu_keyboard(user.id),
        )
        return
    try:
        sub = issue_or_extend_subscription(user.id, plan="РїСЂРѕР±РЅР°СЏ РїРѕРґРїРёСЃРєР°", hours=settings.trial_hours)
    except Exception as exc:
        logger.exception("РќРµ СѓРґР°Р»РѕСЃСЊ РІС‹РґР°С‚СЊ trial: %s", exc)
        await answer_screen(
            target,
            "РќРµ СѓРґР°Р»РѕСЃСЊ Р°РєС‚РёРІРёСЂРѕРІР°С‚СЊ РїСЂРѕР±РЅС‹Р№ РґРѕСЃС‚СѓРї. РџРѕРїСЂРѕР±СѓР№С‚Рµ РµС‰Рµ СЂР°Р· РёР»Рё РЅР°РїРёС€РёС‚Рµ РІ РїРѕРґРґРµСЂР¶РєСѓ.",
            menu_keyboard(user.id),
        )
        return
    mark_trial_used(user.id)
    write_audit(user.id, sub.username, "trial_issued", f"РІС‹РґР°РЅ РїСЂРѕР±РЅС‹Р№ РґРѕСЃС‚СѓРї РЅР° {settings.trial_hours} С‡")
    await answer_screen(target, trial_activated_text(sub), access_keyboard(sub))


async def send_access(target: Message | CallbackQuery, user_id: int) -> None:
    sub = get_active_subscription(user_id)
    if not sub:
        await answer_screen(target, "РЎРµР№С‡Р°СЃ Сѓ РІР°СЃ РЅРµС‚ Р°РєС‚РёРІРЅРѕР№ РїРѕРґРїРёСЃРєРё.", back_keyboard())
        return
    await answer_screen(target, access_text(sub), access_keyboard(sub))


async def send_status(target: Message | CallbackQuery, user_id: int) -> None:
    sub = get_active_subscription(user_id)
    if not sub:
        await answer_screen(target, "РЎРµР№С‡Р°СЃ Сѓ РІР°СЃ РЅРµС‚ Р°РєС‚РёРІРЅРѕР№ РїРѕРґРїРёСЃРєРё.", back_keyboard())
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
    if not await _ensure_not_banned(message, message.from_user):
        return
    await message.answer(buy_text(), reply_markup=buy_keyboard("socks5"))


@router.message(Command("myproxy"))
async def cmd_myproxy(message: Message) -> None:
    upsert_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    if not await _ensure_not_banned(message, message.from_user):
        return
    await send_access(message, message.from_user.id)


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    upsert_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    if not await _ensure_not_banned(message, message.from_user):
        return
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
    if not await _ensure_not_banned(callback, callback.from_user):
        return
    await answer_screen(callback, buy_text(), buy_keyboard("socks5"))


@router.callback_query(F.data.startswith("buy_protocol:"))
async def on_buy_protocol(callback: CallbackQuery) -> None:
    if not await _ensure_not_banned(callback, callback.from_user):
        return
    selected = (callback.data or "").split(":", 1)[1]
    if selected not in {"socks5", "http"}:
        selected = "socks5"
    await answer_screen(callback, buy_text(selected), buy_keyboard(selected))


@router.callback_query(F.data.startswith("pay_stars"))
async def on_pay_stars(callback: CallbackQuery, bot: Bot) -> None:
    if not await _ensure_not_banned(callback, callback.from_user):
        return
    await callback.answer()
    selected = "socks5"
    if callback.data and ":" in callback.data:
        selected = callback.data.split(":", 1)[1]
    if selected not in {"socks5", "http"}:
        selected = "socks5"
    await send_stars_invoice(callback.message.chat.id, callback.from_user, bot, proxy_type=selected)


@router.callback_query(F.data == "my_access")
async def on_access(callback: CallbackQuery) -> None:
    if not await _ensure_not_banned(callback, callback.from_user):
        return
    await send_access(callback, callback.from_user.id)


@router.callback_query(F.data == "status")
async def on_status(callback: CallbackQuery) -> None:
    if not await _ensure_not_banned(callback, callback.from_user):
        return
    await send_status(callback, callback.from_user.id)


@router.callback_query(F.data == "setup")
async def on_setup(callback: CallbackQuery) -> None:
    await answer_screen(callback, setup_text(), back_keyboard())


@router.callback_query(F.data == "server_status")
async def on_server_status(callback: CallbackQuery) -> None:
    try:
        await callback.answer("РџСЂРѕРІРµСЂСЏСЋ СЃРµСЂРІРµСЂвЂ¦")
    except Exception:
        pass
    sub = get_active_subscription(callback.from_user.id)
    if not sub:
        await answer_screen(
            callback,
            "РЎРµР№С‡Р°СЃ Сѓ РІР°СЃ РЅРµС‚ Р°РєС‚РёРІРЅРѕРіРѕ РґРѕСЃС‚СѓРїР°. РђРєС‚РёРІРёСЂСѓР№С‚Рµ РїСЂРѕР±РЅСѓСЋ РїРѕРґРїРёСЃРєСѓ РёР»Рё РѕС„РѕСЂРјРёС‚Рµ РїРѕРґРїРёСЃРєСѓ, С‡С‚РѕР±С‹ РїСЂРѕРІРµСЂРёС‚СЊ РІР°С€ РєРѕРЅРєСЂРµС‚РЅС‹Р№ РїСЂРѕРєСЃРё.",
            back_keyboard(),
        )
        return
    status = await get_server_status(sub)
    await answer_screen(callback, server_status_text(status), back_keyboard())


@router.callback_query(F.data == "faq")
async def on_faq(callback: CallbackQuery) -> None:
    await answer_screen(callback, faq_text(), back_keyboard())

@router.callback_query(F.data == "support")
async def on_support(callback: CallbackQuery) -> None:
    await answer_screen(callback, support_screen_text(), support_keyboard())


@router.callback_query(F.data == "create_ticket")
async def on_create_ticket(callback: CallbackQuery) -> None:
    if not await _ensure_not_banned(callback, callback.from_user):
        return
    create_ticket_draft(callback.from_user.id)
    await answer_screen(
        callback,
        "<b>рџЋ« РќРѕРІС‹Р№ С‚РёРєРµС‚</b>\n\nРћРїРёС€РёС‚Рµ РїСЂРѕР±Р»РµРјСѓ РѕРґРЅРёРј СЃРѕРѕР±С‰РµРЅРёРµРј. РџРѕСЃР»Рµ РѕС‚РїСЂР°РІРєРё С‚РёРєРµС‚ Р±СѓРґРµС‚ СЃРѕР·РґР°РЅ Рё РїРµСЂРµРґР°РЅ Р°РґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂСѓ.",
        back_keyboard(),
    )


@router.message(F.text & ~F.text.startswith("/"))
async def on_ticket_message(message: Message, bot: Bot) -> None:
    if not has_ticket_draft(message.from_user.id):
        return
    if not await _ensure_not_banned(message, message.from_user):
        clear_ticket_draft(message.from_user.id)
        return

    text = (message.text or "").strip()
    if not text:
        await message.answer("РџРѕР¶Р°Р»СѓР№СЃС‚Р°, РѕС‚РїСЂР°РІСЊС‚Рµ С‚РµРєСЃС‚РѕРІРѕРµ РѕРїРёСЃР°РЅРёРµ РїСЂРѕР±Р»РµРјС‹ РѕРґРЅРёРј СЃРѕРѕР±С‰РµРЅРёРµРј.")
        return

    ticket_id = create_ticket(message.from_user.id, text)
    clear_ticket_draft(message.from_user.id)
    write_audit(message.from_user.id, message.from_user.username or "-", "ticket_created", f"ticket_id={ticket_id}")

    user_name = message.from_user.full_name or "-"
    username = f"@{message.from_user.username}" if message.from_user.username else "-"
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(
                admin_id,
                (
                    "<b>рџЋ« РќРѕРІС‹Р№ С‚РёРєРµС‚</b>\n\n"
                    f"<b>ID:</b> <code>{ticket_id}</code>\n"
                    f"<b>User ID:</b> <code>{message.from_user.id}</code>\n"
                    f"<b>РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ:</b> <code>{user_name}</code>\n"
                    f"<b>Username:</b> <code>{username}</code>\n\n"
                    f"<b>РЎРѕРѕР±С‰РµРЅРёРµ:</b>\n{text}\n\n"
                    f"РћС‚РІРµС‚: <code>/reply {ticket_id} С‚РµРєСЃС‚</code>\n"
                    f"Р—Р°РєСЂС‹С‚СЊ: <code>/close {ticket_id}</code>"
                ),
            )
        except Exception:
            logger.exception("РќРµ СѓРґР°Р»РѕСЃСЊ РѕС‚РїСЂР°РІРёС‚СЊ С‚РёРєРµС‚ %s Р°РґРјРёРЅСѓ %s", ticket_id, admin_id)

    await message.answer(
        f"вњ… РўРёРєРµС‚ <code>#{ticket_id}</code> СЃРѕР·РґР°РЅ. РњС‹ РѕС‚РІРµС‚РёРј РІ СЌС‚РѕРј С‡Р°С‚Рµ.",
        reply_markup=menu_keyboard(message.from_user.id),
    )


@router.callback_query(F.data == "noop")
async def on_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data == "show_username")
async def on_show_username(callback: CallbackQuery) -> None:
    sub = get_active_subscription(callback.from_user.id)
    if not sub:
        await callback.answer("РЈ РІР°СЃ РЅРµС‚ Р°РєС‚РёРІРЅРѕРіРѕ РґРѕСЃС‚СѓРїР°.", show_alert=True)
        return
    await callback.answer(f"Р›РѕРіРёРЅ: {sub.username}", show_alert=True)


@router.callback_query(F.data == "show_password")
async def on_show_password(callback: CallbackQuery) -> None:
    sub = get_active_subscription(callback.from_user.id)
    if not sub:
        await callback.answer("РЈ РІР°СЃ РЅРµС‚ Р°РєС‚РёРІРЅРѕРіРѕ РґРѕСЃС‚СѓРїР°.", show_alert=True)
        return
    await callback.answer(f"РџР°СЂРѕР»СЊ: {sub.password}", show_alert=True)


@router.callback_query(F.data == "reissue_token")
async def on_reissue_token(callback: CallbackQuery) -> None:
    sub = get_active_subscription(callback.from_user.id)
    if not sub:
        await callback.answer("РЈ РІР°СЃ РЅРµС‚ Р°РєС‚РёРІРЅРѕРіРѕ РґРѕСЃС‚СѓРїР°.", show_alert=True)
        return

    recent_reissues = count_recent_user_actions(callback.from_user.id, "user_token_reissue", hours=24)
    if recent_reissues >= 2:
        await callback.answer("Р›РёРјРёС‚ РїРµСЂРµРІС‹РїСѓСЃРєР° С‚РѕРєРµРЅР°: 2 СЂР°Р·Р° Р·Р° 24 С‡Р°СЃР°.", show_alert=True)
        return

    new_sub = reissue_subscription_credentials(callback.from_user.id)
    if not new_sub:
        await callback.answer("РќРµ СѓРґР°Р»РѕСЃСЊ РїРµСЂРµРІС‹РїСѓСЃС‚РёС‚СЊ С‚РѕРєРµРЅ. РџРѕРїСЂРѕР±СѓР№С‚Рµ РїРѕР·Р¶Рµ.", show_alert=True)
        return

    write_audit(callback.from_user.id, new_sub.username, "user_token_reissue", "РїРµСЂРµРІС‹РїСѓСЃРє РёР· СЂР°Р·РґРµР»Р° РњРѕР№ РґРѕСЃС‚СѓРї")
    await callback.answer("РўРѕРєРµРЅ РїРµСЂРµРІС‹РїСѓС‰РµРЅ. РЎС‚Р°СЂРѕРµ РїРѕРґРєР»СЋС‡РµРЅРёРµ РѕС‚РєР»СЋС‡РµРЅРѕ.", show_alert=True)
    await answer_screen(callback, access_text(new_sub), access_keyboard(new_sub))
