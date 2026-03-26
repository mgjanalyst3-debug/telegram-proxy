from __future__ import annotations

from dataclasses import dataclass

@dataclass(slots=True)
class Subscription:
    row_id: int
    user_id: int
    plan: str
    proxy_type: str
    host: str
    port: int
    username: str
    password: str
    secret: str
    status: str
    issued_at: str
    expires_at: str
    connections_limit: int = 2
    devices_limit: int = 2
    remind_24_sent_at: str = ""
    remind_1_sent_at: str = ""
    expired_notice_sent_at: str = ""


@dataclass(slots=True)
class PaymentRecord:
    row_id: int
    user_id: int
    payload: str
    amount: int
    currency: str
    status: str
    telegram_payment_charge_id: str = ""
    provider_payment_charge_id: str = ""
    fulfilled: bool = False
    created_at: str = ""
    updated_at: str = ""
