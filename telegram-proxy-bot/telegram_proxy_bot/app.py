from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from .config import settings
from .db import init_db
from .handlers.admin import router as admin_router
from .handlers.payments import router as payments_router
from .handlers.user import router as user_router
from .logging_setup import setup_logging
from .tasks.subscription_watcher import subscription_watch_loop


async def run_polling() -> None:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN не задан")

    setup_logging()
    init_db()

    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_router(user_router)
    dp.include_router(admin_router)
    dp.include_router(payments_router)

    await bot.delete_webhook(drop_pending_updates=False)
    asyncio.create_task(subscription_watch_loop(bot))
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
