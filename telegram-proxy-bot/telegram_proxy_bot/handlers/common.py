from __future__ import annotations

import logging

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from ..ui.keyboards import menu_keyboard
from ..ui.texts import welcome_text

logger = logging.getLogger(__name__)

async def safe_callback_answer(callback: CallbackQuery, *args, **kwargs) -> None:
    try:
        await callback.answer(*args, **kwargs)
    except TelegramBadRequest as exc:  # pragma: no cover - telegram side behavior
        logger.debug("callback answer skipped: %s", exc)


async def answer_screen(target: Message | CallbackQuery, text: str, keyboard) -> None:
    if isinstance(target, CallbackQuery):
        try:
            await target.message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
        except Exception as exc:  # pragma: no cover - telegram side behavior
            logger.debug("edit_text fallback to answer: %s", exc)
            await target.message.answer(text, reply_markup=keyboard, disable_web_page_preview=True)
        await safe_callback_answer(target)
    else:
        await target.answer(text, reply_markup=keyboard, disable_web_page_preview=True)


async def show_menu(target: Message | CallbackQuery) -> None:
    uid = target.from_user.id
    await answer_screen(target, welcome_text(), menu_keyboard(uid))
