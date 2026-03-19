#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="telegram-proxy-bot"
PROJECT_DIR="${1:-/opt/telegram-proxy-bot}"

cd "$PROJECT_DIR"
sudo systemctl restart "$SERVICE_NAME"
sudo systemctl status "$SERVICE_NAME" --no-pager
