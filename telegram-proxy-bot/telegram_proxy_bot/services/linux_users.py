from __future__ import annotations

import subprocess

from ..config import settings
from ..models import Subscription
from ..repositories.audit import write_audit



def run_cmd(cmd: list[str], input_text: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, input=input_text, text=True, capture_output=True, check=False)



def linux_user_exists(username: str) -> bool:
    return run_cmd(["id", username]).returncode == 0



def linux_user_locked(username: str) -> bool:
    if not linux_user_exists(username):
        return False
    result = run_cmd(["passwd", "-S", username])
    if result.returncode != 0:
        return False
    parts = (result.stdout or "").strip().split()
    return len(parts) >= 2 and parts[1] == "L"



def ensure_linux_proxy_user(username: str, password: str) -> None:
    if not settings.linux_proxy_users_enabled:
        return
    created = False
    if not linux_user_exists(username):
        result = run_cmd(["useradd", "-M", "-s", settings.linux_proxy_shell, username])
        if result.returncode != 0 and "already exists" not in (result.stderr or ""):
            raise RuntimeError(f"Не удалось создать Linux-пользователя {username}: {result.stderr.strip()}")
        created = True
    run_cmd(["passwd", "-u", username])
    pass_result = run_cmd(["chpasswd"], input_text=f"{username}:{password}\n")
    if pass_result.returncode != 0:
        raise RuntimeError(
            f"Не удалось установить пароль для {username}: {(pass_result.stderr or '').strip()}"
        )
    write_audit(0, username, "linux_user_sync", "создан" if created else "обновлен пароль")



def lock_linux_proxy_user(username: str) -> None:
    if not settings.linux_proxy_users_enabled or not linux_user_exists(username):
        return
    result = run_cmd(["passwd", "-l", username])
    if result.returncode == 0:
        write_audit(0, username, "linux_user_lock", "учетка заблокирована")



def sync_active_subscription_to_linux(sub: Subscription) -> None:
    ensure_linux_proxy_user(sub.username, sub.password)
    write_audit(sub.user_id, sub.username, "subscription_sync", f"активирована до {sub.expires_at}")



def disable_expired_subscription_in_linux(username: str) -> None:
    lock_linux_proxy_user(username)
