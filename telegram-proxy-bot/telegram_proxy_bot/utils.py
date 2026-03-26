from __future__ import annotations

import re
import secrets
from datetime import datetime, timezone
from urllib.parse import quote

from .config import settings
from .models import Subscription

UTC = timezone.utc



def now_utc() -> datetime:
    return datetime.now(UTC)



def now_iso() -> str:
    return now_utc().isoformat()


def parse_dt(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def format_dt(value: str) -> str:
    return parse_dt(value).astimezone(settings.display_tz).strftime("%d.%m.%Y %H:%M")


def build_username(user_id: int) -> str:
    return f"{settings.mtproto_username_prefix}{user_id}"



def build_password(length: int | None = None) -> str:
    # Для MTProto в ссылке нужен hex-secret, а пароль также используется для Linux-учетки.
    # Выдаем hex-строку: она валидна для MTProto и безопасна для chpasswd.
    real_length = length or settings.mtproto_token_length
    real_length = max(16, real_length)
    if real_length % 2 != 0:
        real_length += 1
    return secrets.token_hex(real_length // 2)


_MT_SECRET_RE = re.compile(r"^[0-9a-fA-F]{32,}$")


def _normalize_mtproto_secret(raw_secret: str) -> str:
    candidate = (raw_secret or "").strip()
    if _MT_SECRET_RE.fullmatch(candidate) and len(candidate) % 2 == 0:
        return candidate.lower()
    return ""


def get_mtproto_url(sub: Subscription) -> str | None:
    secret_source = sub.secret or settings.mtproto_secret or sub.password
    secret = _normalize_mtproto_secret(secret_source)
    if not secret:
        return None
    return (
        "https://t.me/proxy?"
        f"server={sub.host}&port={sub.port}"
        f"&secret={quote(secret, safe='')}"
    )


def get_proxy_connect_url(sub: Subscription) -> str | None:
    return get_mtproto_url(sub)


def proxy_type_label(proxy_type: str) -> str:
    return "MTProto"
