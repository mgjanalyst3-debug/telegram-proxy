#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="${SERVICE_NAME:-telegram-proxy-bot}"
PROJECT_DIR="${PROJECT_DIR:-/opt/telegram-proxy-bot}"
ENV_FILE="${ENV_FILE:-$PROJECT_DIR/.env}"

if ! systemctl is-active --quiet "$SERVICE_NAME"; then
  echo "[FAIL] service $SERVICE_NAME is not active"
  exit 1
fi

echo "[OK] service is active"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[FAIL] env file not found: $ENV_FILE"
  exit 1
fi

# shellcheck disable=SC1090
set -a
source "$ENV_FILE"
set +a

if [[ -z "${BOT_TOKEN:-}" ]]; then
  echo "[FAIL] BOT_TOKEN is empty"
  exit 1
fi

curl -fsS "https://api.telegram.org/bot${BOT_TOKEN}/getMe" >/tmp/telegram_proxy_bot_getme.json

echo "[OK] Telegram API getMe succeeded"

if [[ -n "${DB_PATH:-}" && -f "$DB_PATH" ]]; then
  echo "[OK] database exists: $DB_PATH"
else
  echo "[WARN] DB_PATH file not found yet: ${DB_PATH:-unset}"
fi
