from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo



def load_env_file(path: str | Path = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_env_file(os.getenv("BOT_ENV_FILE", ".env"))


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: set[int]
    db_path: Path
    socks5_host: str
    socks5_port: int
    http_host: str
    http_port: int
    socks5_username_prefix: str
    socks5_password_length: int
    linux_proxy_users_enabled: bool
    linux_proxy_shell: str
    trial_hours: int
    paid_days: int
    price_xtr: int
    bot_brand: str
    support_username: str
    display_tz_name: str
    display_tz: ZoneInfo
    log_level: str
    subscription_check_interval_seconds: int
    reminder_hours: tuple[int, int]
    default_connections_limit: int
    default_devices_limit: int



def _parse_admin_ids(raw: str) -> set[int]:
    result: set[int] = set()
    for value in raw.split(","):
        value = value.strip()
        if value.isdigit():
            result.add(int(value))
    return result



def load_settings() -> Settings:
    tz_name = os.getenv("DISPLAY_TZ", "Europe/Moscow")
    return Settings(
        bot_token=os.getenv("BOT_TOKEN", ""),
        admin_ids=_parse_admin_ids(os.getenv("ADMIN_IDS", "")),
        db_path=Path(os.getenv("DB_PATH", "proxy_bot.sqlite3")),
        socks5_host=os.getenv("SOCKS5_HOST", "127.0.0.1"),
        socks5_port=int(os.getenv("SOCKS5_PORT", "1080")),
        http_host=os.getenv("HTTP_PROXY_HOST", os.getenv("SOCKS5_HOST", "127.0.0.1")),
        http_port=int(os.getenv("HTTP_PROXY_PORT", os.getenv("SOCKS5_PORT", "1080"))),
        socks5_username_prefix=os.getenv("SOCKS5_USERNAME_PREFIX", "px"),
        socks5_password_length=int(os.getenv("SOCKS5_PASSWORD_LENGTH", "14")),
        linux_proxy_users_enabled=os.getenv("LINUX_PROXY_USERS_ENABLED", "1") == "1",
        linux_proxy_shell=os.getenv("LINUX_PROXY_SHELL", "/usr/sbin/nologin"),
        trial_hours=int(os.getenv("TRIAL_HOURS", "168")),
        paid_days=int(os.getenv("PAID_DAYS", "30")),
        price_xtr=int(os.getenv("PRICE_XTR", "50")),
        bot_brand=os.getenv("BOT_BRAND", "Премиум прокси"),
        support_username=os.getenv("SUPPORT_USERNAME", ""),
        display_tz_name=tz_name,
        display_tz=ZoneInfo(tz_name),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        subscription_check_interval_seconds=int(os.getenv("SUBSCRIPTION_CHECK_INTERVAL_SECONDS", "300")),
        reminder_hours=(24, 1),
        default_connections_limit=int(os.getenv("DEFAULT_CONNECTIONS_LIMIT", "2")),
        default_devices_limit=int(os.getenv("DEFAULT_DEVICES_LIMIT", "2")),
    )

settings = load_settings()
