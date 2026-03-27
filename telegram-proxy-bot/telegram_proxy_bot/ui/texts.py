from __future__ import annotations

from html import escape

from ..config import settings
from ..models import Subscription
from ..services.server_status import ServerStatus
from ..utils import format_dt, get_proxy_connect_url, proxy_type_label


def welcome_text() -> str:
    return (
        f"<b>{settings.bot_brand}</b>\n\n"
        "⚡ Подключите стабильный доступ к Telegram всего за пару минут.\n\n"
        "Внутри бота вы сможете:\n"
        "• получить личные данные для подключения\n"
        f"• попробовать сервис бесплатно {settings.trial_hours // 24} дней\n"
        f"• оформить подписку на {settings.paid_days} дней\n"
        "• быстро продлить доступ\n"
        "• получить помощь по подключению\n\n"
        "Получите постоянный доступ уже сейчас."
    )


def start_text() -> str:
    return (
        f"<b>{settings.bot_brand}</b>\n\n"
        "👋 Добро пожаловать.\n\n"
        "Этот бот поможет вам:\n"
        "• получить пробную подписку\n"
        "• оплатить доступ через Telegram Stars\n"
        "• открыть персональный конфиг\n"
        "• быстро подключить прокси по ссылке\n"
        "• получить напоминание перед окончанием доступа\n\n"
        "Для начала выберите один из разделов ниже."
    )



def faq_text() -> str:
    return (
        f"<b>{settings.bot_brand}</b>\n\n"
        "<b>❓ Что входит в подписку?</b>\n"
        "Вы получаете персональный MTProto-доступ: сервер, порт 443, токен и быструю ссылку для добавления прокси в Telegram.\n\n"
        "<b>🎁 Как работает пробная подписка?</b>\n"
        f"Пробная подписка выдается один раз на пользователя и действует {settings.trial_hours} часов (7 дней). Если доступ уже был активирован ранее, бот предложит оформить платную подписку.\n\n"
        "<b>💳 Как проходит оплата?</b>\n"
        "Оплата проходит прямо внутри Telegram через Telegram Stars. После успешной оплаты срок доступа активируется или продлевается автоматически.\n\n"
        "<b>🔐 Можно ли делиться доступом?</b>\n"
        "Доступ персональный. Один аккаунт должен использоваться только владельцем подписки.\n\n"
        "<b>📱 Где подключать прокси?</b>\n"
        "В Telegram откройте настройки прокси, выберите MTProto и введите данные из раздела «Мой доступ», либо используйте кнопку «Подключить прокси».\n\n"
        "<b>🆘 Куда обращаться?</b>\nОткройте раздел «Поддержка» и создайте обращение."
    )



def setup_text() -> str:
    return (
        f"<b>{settings.bot_brand}</b>\n\n"
        "<b>🛠 Как быстро подключить прокси</b>\n\n"
        "<b>Способ 1 — в один клик</b>\n"
        "Откройте раздел «Мой доступ» и нажмите кнопку «Подключить прокси». Telegram сам предложит сохранить настройки.\n\n"
        "<b>Способ 2 — вручную</b>\n"
        "1. Откройте настройки Telegram.\n"
        "2. Перейдите в раздел прокси.\n"
        "3. Выберите протокол MTProto.\n"
        "4. Укажите сервер, порт и токен из раздела «Мой доступ».\n"
        "5. Сохраните настройки и включите прокси.\n\n"
        "<b>Совет</b>\n"
        "Если вы меняли устройство или перевыпускали доступ, заново откройте бот и используйте актуальные данные."
    )


def buy_text(selected_protocol: str = "mtproto") -> str:
    return (
        f"<b>{settings.bot_brand}</b>\n\n"
        "<b>💎 Тариф:</b> 30 дней\n"
        f"<b>⭐ Стоимость:</b> <code>{settings.price_xtr} XTR</code>\n"
        "<b>💳 Способ оплаты:</b> Telegram Stars\n\n"
        f"<b>⚙️ Протокол по умолчанию:</b> <code>{proxy_type_label(selected_protocol)}</code>\n\n"
        "После оплаты доступ активируется автоматически. Если подписка уже действует, срок будет продлен."
    )


def subscription_text(sub: Subscription) -> str:
    connect_url = get_proxy_connect_url(sub)
    quick_link = (
        f"<b>Быстрая ссылка:</b>\n<code>{escape(connect_url)}</code>\n\n"
        if connect_url
        else "<b>Быстрая ссылка:</b> временно недоступна. Нажмите «🔄 Перевыпустить токен».\n\n"
    )
    secret = sub.secret or sub.password
    return (
        f"<b>{settings.bot_brand}</b>\n\n"
        "Ваш персональный доступ готов.\n\n"
        "👉 Если не удалось подключиться — нажмите «Подключить прокси» ещё раз.\n\n"
        f"<b>Протокол:</b> {proxy_type_label(sub.proxy_type)}\n"
        f"<b>Сервер:</b> <code>{sub.host}</code>\n"
        f"<b>Порт:</b> <code>{sub.port}</code>\n"
        f"<b>Secret (токен):</b> <code>{secret}</code>\n"
        f"<b>Тариф:</b> <code>{sub.plan}</code>\n"
        f"<b>Доступ до:</b> <code>{format_dt(sub.expires_at)}</code>\n"
        f"<b>Лимит подключений:</b> <code>{sub.connections_limit}</code>\n"
        f"<b>Лимит устройств:</b> <code>{sub.devices_limit}</code>\n\n"
        f"{quick_link}"
        "Это персональный доступ. Пожалуйста, не передавайте его другим людям."
    )


def access_text(sub: Subscription) -> str:
    connect_url = get_proxy_connect_url(sub)
    quick_link = (
        f"<b>Быстрая ссылка:</b>\n<code>{escape(connect_url)}</code>\n\n"
        if connect_url
        else "<b>Быстрая ссылка:</b> временно недоступна. Нажмите «🔄 Перевыпустить токен».\n\n"
    )
    return (
        f"<b>{settings.bot_brand}</b>\n\n"
        "<b>📦 Ваш персональный доступ</b>\n\n"
        "👉 Если подключение не работает — нажмите кнопку «Подключить прокси» ещё раз.\n\n"
        f"<b>Протокол:</b> {proxy_type_label(sub.proxy_type)}\n"
        f"<b>Сервер:</b> <code>{sub.host}</code>\n"
        f"<b>Порт:</b> <code>{sub.port}</code>\n"
        f"<b>Тариф:</b> <code>{sub.plan}</code>\n"
        f"<b>Доступ до:</b> <code>{format_dt(sub.expires_at)}</code>\n"
        f"<b>Лимит подключений:</b> <code>{sub.connections_limit}</code>\n"
        f"<b>Лимит устройств:</b> <code>{sub.devices_limit}</code>\n\n"
        f"{quick_link}"
        ""
    )

def _format_ms(value: float | None) -> str:
    if value is None:
        return "нет данных"
    if 0 < value < 1:
        return "&lt;1 мс"
    return f"{int(round(value))} мс"


def server_status_text(status: ServerStatus) -> str:
    latency = status.tcp_latency_ms if status.tcp_latency_ms is not None else status.ping_ms
    if not status.tcp_available or status.auth_available is False:
        header = "🔴 <b>Статус сервера</b>"
        comment = (
            "Сейчас есть временные проблемы с подключением.\n"
            "Мы уже проверяем сервер. Попробуйте чуть позже."
        )
        server_line = "офлайн"
        conn_line = "недоступно"
    elif latency is not None and latency > 150:
        header = "🟠 <b>Статус сервера</b>"
        comment = (
            "Сервер отвечает, но есть повышенная задержка.\n"
            "Подключение может работать медленнее обычного."
        )
        server_line = "онлайн"
        conn_line = "доступно"
    else:
        header = "🟢 <b>Статус сервера</b>"
        comment = "Сейчас сервис работает нормально."
        server_line = "онлайн"
        conn_line = "доступно"

    checked_at = status.checked_at.astimezone(settings.display_tz).strftime("%d.%m.%Y %H:%M")
    return (
        f"{header}\n\n"
        f"<b>Сервер:</b> {server_line}\n"
        f"<b>Подключение:</b> {conn_line}\n"
        f"<b>Авторизация:</b> {'успешно' if status.auth_available else ('ошибка' if status.auth_available is False else 'нет данных')}\n"
        f"<b>Ping:</b> {_format_ms(status.ping_ms)}\n"
        f"<b>Задержка (TCP):</b> {_format_ms(status.tcp_latency_ms)}\n"
        f"<b>Порт MTProto:</b> <code>{status.host}:{status.port}</code>\n"
        f"<b>Последняя проверка:</b> <code>{checked_at}</code>\n\n"
        f"{comment}"
    )

    
def status_text(sub: Subscription) -> str:
    return (
        f"<b>{settings.bot_brand}</b>\n\n"
        "<b>📊 Статус подписки:</b> активна\n"
        f"<b>Тариф:</b> <code>{sub.plan}</code>\n"
        f"<b>Доступ до:</b> <code>{format_dt(sub.expires_at)}</code>\n"
        f"<b>Протокол:</b> <code>{proxy_type_label(sub.proxy_type)}</code>\n"
        f"<b>Лимит подключений:</b> <code>{sub.connections_limit}</code>\n"
        f"<b>Лимит устройств:</b> <code>{sub.devices_limit}</code>"
    )



def trial_activated_text(sub: Subscription) -> str:
    return (
        "<b>🎉 Пробная подписка активирована</b>\n\n"
        "Ниже — ваши персональные данные для подключения. Сохраните их и не передавайте другим людям.\n\n"
        + subscription_text(sub)
    )



def payment_success_text(sub: Subscription) -> str:
    return (
        "<b>✅ Оплата получена</b>\n\n"
        "Подписка успешно активирована. Ниже — актуальные данные для подключения.\n\n"
        + subscription_text(sub)
    )



def payment_duplicate_text(sub: Subscription | None) -> str:
    if sub:
        return (
            "<b>ℹ️ Платеж уже был обработан</b>\n\n"
            "Показываю ваш текущий доступ еще раз.\n\n"
            + subscription_text(sub)
        )
    return "<b>ℹ️ Платеж уже был обработан</b>\n\nЕсли доступ не появился, напишите в поддержку."



def support_screen_text() -> str:
    return (
        f"<b>{settings.bot_brand}</b>\n\n"
        "🆘 Поддержка работает через обращения внутри бота.\n\n"
        "Нажмите «Создать обращение» и отправьте одним сообщением описание проблемы."
    )



def paysupport_text() -> str:
    return (
        f"<b>{settings.bot_brand}</b>\n\n"
        "<b>💳 Поддержка по оплате</b>\n\n"
        "По вопросам оплаты, возвратов и зачисления Stars создайте обращение в боте.\n"
        "В сообщении укажите дату платежа, сумму и ваш user_id — это ускорит проверку."
    )



def admin_panel_text() -> str:
    return (
        f"<b>{settings.bot_brand}</b>\n\n"
        "<b>👑 Админ-панель</b>\n\n"
        "Отсюда можно смотреть статистику, актуальные подписки, платежи, состояние Linux-учеток и выгружать XLSX-файлы."
    )



def admin_commands_text() -> str:
    return (
        f"<b>{settings.bot_brand}</b>\n\n"
        "<b>⌨️ Команды администратора</b>\n\n"
        "<code>/grant_30 USER_ID</code> — выдать или продлить подписку на 30 дней.\n"
        "<code>/extend USER_ID DAYS</code> — продлить подписку на N дней.\n"
        "<code>/reissue USER_ID</code> — перевыпустить пароль и синхронизировать Linux-учетку.\n"
        "<code>/reset_trial USER_ID</code> — сбросить пробный период пользователю.\n"
        "<code>/expire_sub USER_ID</code> — завершить подписку пользователя.\n"
        "<code>/star_balance</code> — показать текущий баланс Telegram Stars.\n"
        "<code>/star_tx [LIMIT]</code> — показать последние Star-транзакции.\n\n"
        "Через кнопку «👑 Админ-панель» доступны статистика, таблицы, аудит и выгрузки XLSX."
    )



def expiring_soon_text(sub: Subscription, hours_left: int) -> str:
    return (
        f"<b>{settings.bot_brand}</b>\n\n"
        f"⏳ До окончания подписки осталось менее {hours_left} ч.\n\n"
        f"<b>Доступ до:</b> <code>{format_dt(sub.expires_at)}</code>\n"
        "Вы можете потерять доступ к Telegram и не сможете продлить услугу после отключения. Продлите подписку заранее."
    )



def expired_text() -> str:
    return (
        f"<b>{settings.bot_brand}</b>\n\n"
        "⏳ Срок действия подписки истек. Ваш доступ был автоматически остановлен.\n\n"
        "Оформите продление в главном меню, чтобы снова получить рабочий доступ."
    )

def admin_commands_text() -> str:
    return (
        f"<b>{settings.bot_brand}</b>\n\n"
        "<b>⌨️ Команды администратора</b>\n\n"
        "<b>Подписки</b>\n"
        "<code>/grant_trial USER_ID</code> — выдать пробный период вручную.\n"
        "<code>/reset_trial USER_ID</code> — сбросить trial.\n"
        "<code>/extend USER_ID DAYS</code> — продлить подписку на N дней.\n"
        "<code>/expire USER_ID</code> — завершить подписку прямо сейчас.\n"
        "<code>/delete_sub USER_ID</code> — удалить подписки пользователя.\n"
        "<code>/reissue USER_ID</code> — перевыпустить пароль и синхронизировать Linux-учетку.\n"
        "<code>/set_limit USER_ID N</code> — лимит подключений.\n"
        "<code>/set_devices USER_ID N</code> — лимит устройств.\n\n"
        "<b>Платежи</b>\n"
        "<code>/payments USER_ID</code> — история платежей.\n"
        "<code>/mark_paid USER_ID DAYS</code> — вручную активировать подписку.\n"
        "<code>/refund USER_ID PAYMENT_ID</code> — возврат платежа.\n"
        "<code>/star_balance</code> — показать текущий баланс Telegram Stars.\n"
        "<code>/star_tx [LIMIT]</code> — показать последние Star-транзакции.\n\n"
        "<b>Пользователи и сервис</b>\n"
        "<code>/reply TICKET_ID TEXT</code> — ответить пользователю по тикету.\n"
        "<code>/close TICKET_ID</code> — закрыть тикет.\n"
        "<code>/user USER_ID</code> — карточка пользователя.\n"
        "<code>/ban USER_ID</code> / <code>/unban USER_ID</code> — блокировка.\n"
        "<code>/note USER_ID TEXT</code> — заметка админа.\n"
        "<code>/users_active</code> / <code>/users_expired</code> — списки пользователей.\n"
        "<code>/broadcast TEXT</code> / <code>/broadcast_active TEXT</code> — рассылки.\n"
        "<code>/stats</code>, <code>/health</code>, <code>/whoami</code> — диагностика.\n\n"
        "Также доступны статистика, таблицы, аудит и выгрузки XLSX через кнопки админ-панели."
    )




BOTFATHER_DESCRIPTION = (
    ""
)
