from __future__ import annotations

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
    return f"{settings.socks5_username_prefix}{user_id}"



def build_password(length: int | None = None) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"
    real_length = length or settings.socks5_password_length
    return "".join(secrets.choice(alphabet) for _ in range(real_length))



def get_socks5_url(sub: Subscription) -> str:
    return (
        "https://t.me/socks?"
        f"server={sub.host}&port={sub.port}"
        f"&user={quote(sub.username, safe='')}&pass={quote(sub.password, safe='')}"
    )
