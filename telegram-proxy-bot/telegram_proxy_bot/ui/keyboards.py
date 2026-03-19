from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ..models import Subscription
from ..services.subscriptions import get_active_subscription
from ..ui.texts import support_text
from ..utils import get_socks5_url
from ..config import settings



def access_keyboard(sub: Subscription) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Подключить прокси", url=get_socks5_url(sub))],
            [
                InlineKeyboardButton(text="👤 Показать логин", callback_data="show_username"),
                InlineKeyboardButton(text="🔑 Показать пароль", callback_data="show_password"),
            ],
            [
                InlineKeyboardButton(text="🛠 Инструкция", callback_data="setup"),
                InlineKeyboardButton(text="🏠 В меню", callback_data="menu"),
            ],
        ]
    )



def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📈 Статистика", callback_data="admin_stats"),
                InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users"),
            ],
            [
                InlineKeyboardButton(text="📦 Актуальные подписки", callback_data="admin_subs"),
                InlineKeyboardButton(text="💳 Платежи", callback_data="admin_payments"),
            ],
            [
                InlineKeyboardButton(text="🖥 Linux-учетки", callback_data="admin_linux_users"),
                InlineKeyboardButton(text="🧾 Аудит", callback_data="admin_audit"),
            ],
            [
                InlineKeyboardButton(text="📤 CSV: пользователи", callback_data="export_users"),
                InlineKeyboardButton(text="📤 CSV: подписки", callback_data="export_subs"),
            ],
            [
                InlineKeyboardButton(text="📤 CSV: платежи", callback_data="export_payments"),
                InlineKeyboardButton(text="📤 CSV: активные", callback_data="export_active_subs"),
            ],
            [InlineKeyboardButton(text="🏠 В меню", callback_data="menu")],
        ]
    )



def menu_keyboard(user_id: int | None = None) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🎁 Пробная подписка", callback_data="trial")],
        [
            InlineKeyboardButton(text="💳 Купить доступ", callback_data="buy"),
            InlineKeyboardButton(text="📦 Мой доступ", callback_data="my_access"),
        ],
        [
            InlineKeyboardButton(text="📊 Статус подписки", callback_data="status"),
            InlineKeyboardButton(text="🛠 Как подключить", callback_data="setup"),
        ],
        [
            InlineKeyboardButton(text="🆘 Поддержка", callback_data="support"),
            InlineKeyboardButton(text="❓ Ответы на вопросы", callback_data="faq"),
        ],
    ]
    if user_id is not None and user_id in settings.admin_ids:
        rows.append(
            [
                InlineKeyboardButton(text="👑 Админ-панель", callback_data="admin_panel"),
                InlineKeyboardButton(text="⌨️ Команды", callback_data="admin_commands"),
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)



def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏠 Вернуться в меню", callback_data="menu")]]
    )



def buy_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐ Оплатить через Telegram Stars", callback_data="pay_stars")],
            [InlineKeyboardButton(text="🏠 Вернуться в меню", callback_data="menu")],
        ]
    )
