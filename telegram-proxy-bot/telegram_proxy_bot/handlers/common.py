from __future__ import annotations

import logging

from aiogram.types import CallbackQuery, Message

from ..ui.keyboards import menu_keyboard
from ..ui.texts import welcome_text

logger = logging.getLogger(__name__)


async def answer_screen(target: Message | CallbackQuery, text: str, keyboard) -> None:
    if isinstance(target, CallbackQuery):
        try:
            await target.answer()
        except Exception as exc:  # pragma: no cover - telegram side behavior
            logger.debug("callback answer pre-edit skipped: %s", exc)
        try:
            await target.message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
        except Exception as exc:  # pragma: no cover - telegram side behavior
            logger.debug("edit_text fallback to answer: %s", exc)
            await target.message.answer(text, reply_markup=keyboard, disable_web_page_preview=True)
    else:
        await target.answer(text, reply_markup=keyboard, disable_web_page_preview=True)


async def show_menu(target: Message | CallbackQuery) -> None:
    uid = target.from_user.id
    await answer_screen(target, welcome_text(), menu_keyboard(uid))
