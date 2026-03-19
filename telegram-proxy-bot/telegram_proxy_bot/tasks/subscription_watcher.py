from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from aiogram import Bot

from ..config import settings
from ..repositories.audit import write_audit
from ..repositories import subscriptions as subs_repo
from ..services.subscriptions import expire_user_subscription, list_active_subscriptions_for_watch
from ..ui.keyboards import buy_keyboard, menu_keyboard
from ..ui.texts import expired_text, expiring_soon_text
from ..utils import now_iso, now_utc, parse_dt

logger = logging.getLogger(__name__)


async def subscription_watch_loop(bot: Bot) -> None:
    while True:
        try:
            await _check_active_subscriptions(bot)
        except Exception as exc:  # pragma: no cover - background loop
            logger.exception("Ошибка фоновой проверки подписок: %s", exc)
        await asyncio.sleep(settings.subscription_check_interval_seconds)


async def _check_active_subscriptions(bot: Bot) -> None:
    now = now_utc()
    for sub in list_active_subscriptions_for_watch():
        expires_at = parse_dt(sub.expires_at)
        remaining = expires_at - now

        if remaining <= timedelta(seconds=0):
            expire_user_subscription(sub.user_id, username=sub.username)
            write_audit(
                sub.user_id,
                sub.username,
                "subscription_expired",
                "подписка истекла и Linux-учетка заблокирована",
            )
            if not sub.expired_notice_sent_at:
                try:
                    await bot.send_message(sub.user_id, expired_text(), reply_markup=buy_keyboard())
                except Exception as notify_error:
                    logger.warning("Не удалось уведомить user_id=%s: %s", sub.user_id, notify_error)
                subs_repo.set_expired_notice_sent(sub.row_id, now_iso())
            continue

        if remaining <= timedelta(hours=24) and not sub.remind_24_sent_at:
            await _send_expiring_reminder(bot, sub.user_id, sub.row_id, 24)
            continue

        if remaining <= timedelta(hours=72) and not sub.remind_72_sent_at:
            await _send_expiring_reminder(bot, sub.user_id, sub.row_id, 72)


async def _send_expiring_reminder(bot: Bot, user_id: int, subscription_id: int, hours: int) -> None:
    try:
        sub = next((item for item in list_active_subscriptions_for_watch() if item.row_id == subscription_id), None)
        if sub is None:
            return
        await bot.send_message(user_id, expiring_soon_text(sub, hours), reply_markup=buy_keyboard())
        subs_repo.set_reminder_sent(subscription_id, hours, now_iso())
    except Exception as exc:  # pragma: no cover - depends on telegram side behavior
        logger.warning("Не удалось отправить reminder %sh user_id=%s: %s", hours, user_id, exc)
