from __future__ import annotations

from datetime import timedelta

from ..config import settings
from ..models import Subscription
from ..repositories import subscriptions as subs_repo
from ..repositories.users import reset_trial_used
from ..services.linux_users import disable_expired_subscription_in_linux, sync_active_subscription_to_linux
from ..utils import build_password, build_username, now_iso, now_utc, parse_dt



def create_personal_credentials(user_id: int) -> tuple[str, str]:
    return build_username(user_id), build_password()

def resolve_proxy_endpoint(proxy_type: str) -> tuple[str, int]:
    return settings.mtproto_host, settings.mtproto_port

def get_latest_subscription(user_id: int):
    return subs_repo.get_latest_subscription(user_id)

def get_active_subscription(user_id: int):
    sub = subs_repo.get_latest_active_subscription_raw(user_id)
    if not sub:
        return None
    if parse_dt(sub.expires_at) <= now_utc():
        expire_user_subscription(user_id, username=sub.username)
        return None
    return sub

def issue_or_extend_subscription(
    user_id: int,
    plan: str,
    *,
    days: int = 0,
    hours: int = 0,
    proxy_type: str = "mtproto",
) -> Subscription:
    current = get_active_subscription(user_id)
    start_from = now_utc()
    if current:
        current_exp = parse_dt(current.expires_at)
        if current_exp > start_from:
            start_from = current_exp
        username = current.username or build_username(user_id)
        password = current.password or build_password()
        connections_limit = current.connections_limit or settings.default_connections_limit
        devices_limit = current.devices_limit or settings.default_devices_limit
    else:
        username, password = create_personal_credentials(user_id)
        connections_limit = settings.default_connections_limit
        devices_limit = settings.default_devices_limit

    normalized_proxy_type = "mtproto"
    host, port = resolve_proxy_endpoint(normalized_proxy_type)
    expires = start_from + timedelta(days=days, hours=hours)
    draft = Subscription(
        row_id=0,
        user_id=user_id,
        plan=plan,
        proxy_type=normalized_proxy_type,
        host=host,
        port=port,
        username=username,
        password=password,
        secret=settings.mtproto_secret or password,
        status="active",
        issued_at=now_iso(),
        expires_at=expires.isoformat(),
        connections_limit=connections_limit,
        devices_limit=devices_limit,
    )
    sync_active_subscription_to_linux(draft)
    if current:
        subs_repo.expire_active_subscriptions(user_id)
    return subs_repo.insert_subscription(draft)



def reissue_subscription_credentials(user_id: int) -> Subscription | None:
    current = get_active_subscription(user_id)
    if not current:
        return None
    remaining_seconds = max(3600, int((parse_dt(current.expires_at) - now_utc()).total_seconds()))
    username = current.username or build_username(user_id)
    password = build_password()
    host, port = resolve_proxy_endpoint(current.proxy_type)
    new_sub = Subscription(
        row_id=0,
        user_id=user_id,
        plan=current.plan,
        proxy_type=current.proxy_type,
        host=host,
        port=port,
        username=username,
        password=password,
        secret=settings.mtproto_secret or password,
        status="active",
        issued_at=now_iso(),
        expires_at=(now_utc() + timedelta(seconds=remaining_seconds)).isoformat(),
        connections_limit=current.connections_limit,
        devices_limit=current.devices_limit,
    )
    sync_active_subscription_to_linux(new_sub)
    subs_repo.expire_active_subscriptions(user_id)
    return subs_repo.insert_subscription(new_sub)


def expire_user_subscription(user_id: int, username: str | None = None) -> None:
    active = subs_repo.get_latest_active_subscription_raw(user_id)
    subs_repo.expire_active_subscriptions(user_id)
    if username:
        disable_expired_subscription_in_linux(username)
    elif active:
        disable_expired_subscription_in_linux(active.username)


def reset_trial_for_user(user_id: int) -> None:
    reset_trial_used(user_id)


def list_active_subscriptions(limit: int = 15):
    return [subs_repo.normalize_legacy_subscription_row(row) for row in subs_repo.list_recent_latest_active_subscriptions(limit)]


def list_active_subscriptions_for_watch():
    return [subs_repo.normalize_legacy_subscription_row(row) for row in subs_repo.list_active_subscription_snapshots_for_watch()]


def list_latest_subscription_snapshots(limit: int = 15):
    return [subs_repo.normalize_legacy_subscription_row(row) for row in subs_repo.list_latest_subscription_snapshots(limit)]
