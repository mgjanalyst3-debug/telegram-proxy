# telegram-proxy-bot

Рефакторинг вашего monolith-файла `mtproto_proxy_bot.py` в более профессиональную структуру проекта.

## Что уже улучшено

- проект переименован в `telegram-proxy-bot`
- код разбит на handlers / services / repositories / tasks / ui
- админ-панель показывает **актуальные подписки**, а не все подряд
- добавлена поддержка `/paysupport`
- добавлены напоминания за 72 и 24 часа до окончания подписки
- платежи хранят `telegram_payment_charge_id`, `provider_payment_charge_id`, `fulfilled`
- добавлена защита от повторной выдачи доступа при дубликате `successful_payment`
- добавлены systemd unit, healthcheck и smoke-test

## Запуск

```bash
python3 -m pip install -r requirements.txt
BOT_ENV_FILE=.env python3 -m telegram_proxy_bot
```

#Перезагрзка бота
sudo systemctl restart telegram-proxy-bot