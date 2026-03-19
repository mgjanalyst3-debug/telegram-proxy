from __future__ import annotations

from ..config import settings
from ..models import Subscription
from ..utils import format_dt, get_socks5_url



def support_text() -> str:
    return f"@{settings.support_username}" if settings.support_username else "администратору бота"



def welcome_text() -> str:
    return (
        f"<b>{settings.bot_brand}</b>\n\n"
        "⚡ Подключите стабильный доступ к Telegram всего за пару минут.\n\n"
        "Внутри бота вы сможете:\n"
        "• получить личные данные для подключения\n"
        f"• попробовать сервис бесплатно {settings.trial_hours // 24} дня\n"
        f"• оформить подписку на {settings.paid_days} дней\n"
        "• быстро продлить доступ\n"
        "• получить помощь по подключению\n\n"
        "Нажмите <b>Start</b>, чтобы начать."
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
        "Вы получаете персональный SOCKS5-доступ: сервер, порт, логин, пароль и быструю ссылку для добавления прокси в Telegram.\n\n"
        "<b>🎁 Как работает пробная подписка?</b>\n"
        f"Пробная подписка выдается один раз на пользователя и действует {settings.trial_hours} часов. Если доступ уже был активирован ранее, бот предложит оформить платную подписку.\n\n"
        "<b>💳 Как проходит оплата?</b>\n"
        "Оплата проходит прямо внутри Telegram через Telegram Stars. После успешной оплаты срок доступа активируется или продлевается автоматически.\n\n"
        "<b>🔐 Можно ли делиться доступом?</b>\n"
        "Доступ персональный. Один аккаунт должен использоваться только владельцем подписки. Для рынка лучше сразу вводить лимит одновременных подключений и отслеживание подозрительных IP.\n\n"
        "<b>📱 Где подключать прокси?</b>\n"
        "В Telegram откройте настройки прокси, выберите SOCKS5 и введите данные из раздела «Мой доступ», либо используйте кнопку «Подключить прокси».\n\n"
        f"<b>🆘 Куда обращаться?</b>\n{support_text()}"
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
        "3. Выберите протокол SOCKS5.\n"
        "4. Укажите сервер, порт, логин и пароль из раздела «Мой доступ».\n"
        "5. Сохраните настройки и включите прокси.\n\n"
        "<b>Совет</b>\n"
        "Если вы меняли устройство или перевыпускали доступ, заново откройте бот и используйте актуальные данные."
    )



def buy_text() -> str:
    return (
        f"<b>{settings.bot_brand}</b>\n\n"
        "<b>💎 Тариф:</b> 30 дней\n"
        f"<b>⭐ Стоимость:</b> <code>{settings.price_xtr} XTR</code>\n"
        "<b>💳 Способ оплаты:</b> Telegram Stars\n\n"
        "После оплаты доступ активируется автоматически. Если подписка уже действует, срок будет продлен."
    )



def subscription_text(sub: Subscription) -> str:
    return (
        f"<b>{settings.bot_brand}</b>\n\n"
        "Ваш персональный доступ готов.\n\n"
        "<b>Протокол:</b> SOCKS5\n"
        f"<b>Сервер:</b> <code>{sub.host}</code>\n"
        f"<b>Порт:</b> <code>{sub.port}</code>\n"
        f"<b>Логин:</b> <code>{sub.username}</code>\n"
        f"<b>Пароль:</b> <code>{sub.password}</code>\n"
        f"<b>Тариф:</b> <code>{sub.plan}</code>\n"
        f"<b>Доступ до:</b> <code>{format_dt(sub.expires_at)}</code>\n"
        f"<b>Лимит подключений:</b> <code>{sub.connections_limit}</code>\n"
        f"<b>Лимит устройств:</b> <code>{sub.devices_limit}</code>\n\n"
        f"<b>Быстрая ссылка:</b>\n{get_socks5_url(sub)}\n\n"
        "Это персональный конфиг. Не передавайте его другим людям."
    )



def access_text(sub: Subscription) -> str:
    return (
        f"<b>{settings.bot_brand}</b>\n\n"
        "<b>📦 Ваш персональный доступ</b>\n\n"
        "<b>Протокол:</b> SOCKS5\n"
        f"<b>Сервер:</b> <code>{sub.host}</code>\n"
        f"<b>Порт:</b> <code>{sub.port}</code>\n"
        f"<b>Тариф:</b> <code>{sub.plan}</code>\n"
        f"<b>Доступ до:</b> <code>{format_dt(sub.expires_at)}</code>\n"
        f"<b>Лимит подключений:</b> <code>{sub.connections_limit}</code>\n"
        f"<b>Лимит устройств:</b> <code>{sub.devices_limit}</code>\n\n"
        f"<b>Быстрая ссылка:</b>\n{get_socks5_url(sub)}\n\n"
        "Чтобы не светить данные в сообщении, логин и пароль можно открыть отдельными кнопками ниже."
    )



def status_text(sub: Subscription) -> str:
    return (
        f"<b>{settings.bot_brand}</b>\n\n"
        "<b>📊 Статус подписки:</b> активна\n"
        f"<b>Тариф:</b> <code>{sub.plan}</code>\n"
        f"<b>Доступ до:</b> <code>{format_dt(sub.expires_at)}</code>\n"
        f"<b>Протокол:</b> <code>{sub.proxy_type}</code>\n"
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
        f"🆘 Если вам нужна помощь, напишите {support_text()}.\n\n"
        "Чем подробнее вы опишете проблему, тем быстрее получится помочь."
    )



def paysupport_text() -> str:
    return (
        f"<b>{settings.bot_brand}</b>\n\n"
        "<b>💳 Поддержка по оплате</b>\n\n"
        f"По вопросам оплаты, возвратов и зачисления Stars напишите {support_text()}.\n"
        "В сообщении укажите дату платежа, сумму и ваш user_id — это ускорит проверку."
    )



def admin_panel_text() -> str:
    return (
        f"<b>{settings.bot_brand}</b>\n\n"
        "<b>👑 Админ-панель</b>\n\n"
        "Отсюда можно смотреть статистику, актуальные подписки, платежи, состояние Linux-учеток и выгружать CSV-файлы."
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
        "Через кнопку «👑 Админ-панель» доступны статистика, таблицы, аудит и выгрузки CSV."
    )



def expiring_soon_text(sub: Subscription, hours_left: int) -> str:
    return (
        f"<b>{settings.bot_brand}</b>\n\n"
        f"⏳ До окончания подписки осталось менее {hours_left} ч.\n\n"
        f"<b>Доступ до:</b> <code>{format_dt(sub.expires_at)}</code>\n"
        "Чтобы не потерять доступ, продлите подписку заранее."
    )



def expired_text() -> str:
    return (
        f"<b>{settings.bot_brand}</b>\n\n"
        "⏳ Срок действия подписки истек. Ваш доступ был автоматически остановлен.\n\n"
        "Оформите продление в главном меню, чтобы снова получить рабочий доступ."
    )


BOTFATHER_DESCRIPTION = (
    "Персональный SOCKS5-прокси для Telegram: пробный доступ, оплата Stars, быстрый запуск и управление подпиской в одном боте."
)
