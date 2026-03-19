from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import Message, PreCheckoutQuery

from ..repositories.users import upsert_user
from ..services.payments import handle_successful_payment
from ..ui.keyboards import access_keyboard, menu_keyboard
from ..ui.texts import payment_duplicate_text, payment_success_text

logger = logging.getLogger(__name__)
router = Router(name="payments")


@router.pre_checkout_query()
async def pre_checkout_handler(query: PreCheckoutQuery) -> None:
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment_handler(message: Message) -> None:
    upsert_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    try:
        result = await handle_successful_payment(message)
    except Exception as exc:
        logger.exception("Ошибка обработки платежа: %s", exc)
        await message.answer(
            "Платеж получен, но при выдаче доступа произошла ошибка. Напишите в поддержку, платеж не потеряется.",
            reply_markup=menu_keyboard(message.from_user.id),
        )
        return
    if result.subscription:
        text = payment_success_text(result.subscription) if result.is_new else payment_duplicate_text(result.subscription)
        await message.answer(text, reply_markup=access_keyboard(result.subscription), disable_web_page_preview=True)
        return
    await message.answer(payment_duplicate_text(None), reply_markup=menu_keyboard(message.from_user.id))
