from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ..config import settings
from ..models import Subscription
from ..utils import get_proxy_connect_url

TELEGRAPH_SETUP_URL = "https://telegra.ph/Premium-dostup-dlya-Telegram-03-20"


def access_keyboard(sub: Subscription) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    connect_url = get_proxy_connect_url(sub)
    if connect_url:
        rows.append([InlineKeyboardButton(text="🔗 Подключить прокси", url=connect_url)])
    rows.append([InlineKeyboardButton(text="🔑 Показать MTProto secret", callback_data="show_secret")])
    rows.append([InlineKeyboardButton(text="🔄 Перевыпустить токен", callback_data="reissue_token")])
    rows.append(
        [
            InlineKeyboardButton(text="🛠 Инструкция", url=TELEGRAPH_SETUP_URL),
            InlineKeyboardButton(text="🏠 В меню", callback_data="menu"),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)

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
                InlineKeyboardButton(text="📤 XLSX: пользователи", callback_data="export_users"),
                InlineKeyboardButton(text="📤 XLSX: подписки", callback_data="export_subs"),
            ],
            [
                InlineKeyboardButton(text="📤 XLSX: платежи", callback_data="export_payments"),
                InlineKeyboardButton(text="📤 XLSX: активные", callback_data="export_active_subs"),
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
            InlineKeyboardButton(text="🛠 Как подключить", url=TELEGRAPH_SETUP_URL),
        ],
        [InlineKeyboardButton(text="🟢 Статус сервера", callback_data="server_status")],
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

def support_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎫 Создать обращение в поддержку", callback_data="create_ticket")],
            [InlineKeyboardButton(text="🏠 Вернуться в меню", callback_data="menu")],
        ]
    )



def buy_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚙️ Протокол: MTProto (порт 443)", callback_data="noop")],
            [InlineKeyboardButton(text="⭐ Оплатить через Telegram Stars", callback_data="pay_stars")],
            [InlineKeyboardButton(text="🏠 Вернуться в меню", callback_data="menu")],
        ]
    )
