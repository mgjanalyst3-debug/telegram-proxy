# Developer commands for telegram-proxy-bot

## Основные команды

### Перейти в проект
```bash
cd /opt/telegram-proxy-bot
```

### Обновить зависимости
```bash
python3 -m pip install -r requirements.txt
```

### Ручной запуск бота
```bash
BOT_ENV_FILE=/opt/telegram-proxy-bot/.env python3 -m telegram_proxy_bot
```

### Перезапуск systemd-сервиса
```bash
sudo systemctl restart telegram-proxy-bot
```

### Статус сервиса
```bash
sudo systemctl status telegram-proxy-bot --no-pager
```

### Следить за логами в реальном времени
```bash
sudo journalctl -u telegram-proxy-bot -f
```

### Последние 100 строк лога
```bash
sudo journalctl -u telegram-proxy-bot -n 100 --no-pager
```

### Включить автозапуск после перезагрузки сервера
```bash
sudo systemctl enable --now telegram-proxy-bot
```

### Проверить, что автозапуск включен
```bash
sudo systemctl is-enabled telegram-proxy-bot
```

### Проверить, что сервис сейчас живой
```bash
sudo systemctl is-active telegram-proxy-bot
```

### Быстрый healthcheck
```bash
PROJECT_DIR=/opt/telegram-proxy-bot ENV_FILE=/opt/telegram-proxy-bot/.env ./scripts/healthcheck.sh
```

### Локальный smoke-test без Telegram и без Linux-пользователей
```bash
python3 scripts/smoke_test.py
```

## Рекомендованный деплой

1. Скопировать проект в `/opt/telegram-proxy-bot`
2. Создать файл `/opt/telegram-proxy-bot/.env`
3. Установить зависимости `pip install -r requirements.txt`
4. Скопировать `systemd/telegram-proxy-bot.service` в `/etc/systemd/system/`
5. Выполнить:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now telegram-proxy-bot
sudo systemctl status telegram-proxy-bot --no-pager
```

## Как понять, что бот будет постоянно работать

Нужны **три условия одновременно**:

1. `systemctl is-enabled telegram-proxy-bot` возвращает `enabled`
2. `systemctl is-active telegram-proxy-bot` возвращает `active`
3. В unit-файле есть `Restart=always`

Если эти три пункта выполнены — после падения процесс будет перезапущен автоматически, а после ребута сервера бот снова поднимется.

## Ваши старые команды в новой структуре

Было:
```bash
cd ~/mtproto-bot
cp mtproto_proxy_bot.py mtproto_proxy_bot.py.bak
sudo systemctl restart mtproto-bot
sudo journalctl -u mtproto-bot -f
```

Стало:
```bash
cd /opt/telegram-proxy-bot
cp .env .env.bak
sudo systemctl restart telegram-proxy-bot
sudo journalctl -u telegram-proxy-bot -f
```
