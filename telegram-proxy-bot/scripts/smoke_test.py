from __future__ import annotations

import importlib
import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "smoke.sqlite3"
        os.environ["BOT_TOKEN"] = "123:test"
        os.environ["ADMIN_IDS"] = "1"
        os.environ["DB_PATH"] = str(db_path)
        os.environ["LINUX_PROXY_USERS_ENABLED"] = "0"
        os.environ["MTPROTO_HOST"] = "127.0.0.1"
        os.environ["MTPROTO_PORT"] = "443"
        os.environ["DISPLAY_TZ"] = "Europe/Moscow"

        config = importlib.import_module("telegram_proxy_bot.config")
        importlib.reload(config)

        db = importlib.import_module("telegram_proxy_bot.db")
        importlib.reload(db)

        users_repo = importlib.import_module("telegram_proxy_bot.repositories.users")
        importlib.reload(users_repo)

        subs_service = importlib.import_module("telegram_proxy_bot.services.subscriptions")
        importlib.reload(subs_service)

        payments_service = importlib.import_module("telegram_proxy_bot.services.payments")
        importlib.reload(payments_service)

        db.init_db()
        users_repo.upsert_user(1001, "tester", "Smoke")

        sub = subs_service.issue_or_extend_subscription(1001, plan="пробная подписка", hours=168)
        assert sub.user_id == 1001
        assert sub.username.startswith("px")
        assert sub.port == 443

        extended = subs_service.issue_or_extend_subscription(1001, plan="30 дней", days=30)
        assert extended.user_id == 1001
        assert extended.username == sub.username

        payload = payments_service.create_invoice_payload(1001)
        assert payload.startswith("sub30_mtproto_1001_")

        print("[OK] smoke test passed")


if __name__ == "__main__":
    main()
