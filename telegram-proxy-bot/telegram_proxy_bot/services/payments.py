from __future__ import annotations

from dataclasses import dataclass
from secrets import token_urlsafe
from typing import Any

from aiogram import Bot
from aiogram.types import LabeledPrice, Message, User

from ..config import settings
from ..repositories.audit import write_audit
from ..repositories import payments as payments_repo
from ..services.subscriptions import get_active_subscription, issue_or_extend_subscription


@dataclass(slots=True)
class PaymentHandlingResult:
    is_new: bool
    subscription: Any



def create_invoice_payload(user_id: int, proxy_type: str = "mtproto", prefix: str = "sub30") -> str:
    return f"{prefix}_{proxy_type}_{user_id}_{token_urlsafe(8)}"


def extract_proxy_type_from_payload(payload: str) -> str:
    parts = (payload or "").split("_")
    if len(parts) >= 4 and parts[1] == "mtproto":
        return parts[1]
    return "mtproto"


async def send_stars_invoice(chat_id: int, user: User, bot: Bot, proxy_type: str = "mtproto") -> None:
    payload = create_invoice_payload(user.id, proxy_type=proxy_type)
    payments_repo.create_payment_invoice(user.id, payload, settings.price_xtr, "XTR", "new")
    await bot.send_invoice(
        chat_id=chat_id,
        title=f"{settings.bot_brand} — 30 дней доступа",
        description="Персональный MTProto-доступ на 30 дней (порт 443).",
        payload=payload,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Подписка на 30 дней", amount=settings.price_xtr)],
    )


async def handle_successful_payment(message: Message) -> PaymentHandlingResult:
    payment = message.successful_payment
    if payment is None:
        raise RuntimeError("В сообщении нет successful_payment")

    already_by_charge = payments_repo.get_payment_by_charge_id(payment.telegram_payment_charge_id)
    if already_by_charge and already_by_charge["fulfilled"]:
        return PaymentHandlingResult(is_new=False, subscription=get_active_subscription(message.from_user.id))

    existing_by_payload = payments_repo.get_payment_by_payload(payment.invoice_payload)
    if existing_by_payload and existing_by_payload["fulfilled"]:
        return PaymentHandlingResult(is_new=False, subscription=get_active_subscription(message.from_user.id))

    payments_repo.mark_payment_success(
        user_id=message.from_user.id,
        payload=payment.invoice_payload,
        amount=payment.total_amount,
        currency=payment.currency,
        telegram_payment_charge_id=payment.telegram_payment_charge_id,
        provider_payment_charge_id=payment.provider_payment_charge_id,
        subscription_expiration_date=getattr(payment, "subscription_expiration_date", 0),
        is_recurring=getattr(payment, "is_recurring", False),
        is_first_recurring=getattr(payment, "is_first_recurring", False),
    )

    selected_proxy_type = extract_proxy_type_from_payload(payment.invoice_payload)
    sub = issue_or_extend_subscription(
        message.from_user.id,
        plan="30 дней",
        days=settings.paid_days,
        proxy_type=selected_proxy_type,
    )
    payments_repo.mark_payment_fulfilled(payment.invoice_payload)
    write_audit(
        message.from_user.id,
        sub.username,
        "payment_paid",
        f"оплата {payment.total_amount} {payment.currency}; charge={payment.telegram_payment_charge_id}",
    )
    return PaymentHandlingResult(is_new=True, subscription=sub)


async def get_star_balance_text(bot: Bot) -> str:
    balance = await bot.get_my_star_balance()
    stars = getattr(balance, "amount", 0)
    nano = getattr(balance, "nanostar_amount", 0)
    return (
        f"<b>{settings.bot_brand}</b>\n\n"
        f"<b>⭐ Баланс Stars бота</b>\n\n"
        f"Stars: <code>{stars}</code>\n"
        f"NanoStars: <code>{nano}</code>"
    )


async def get_star_transactions_text(bot: Bot, limit: int = 10) -> str:
    txs = await bot.get_star_transactions(limit=limit)
    items = getattr(txs, "transactions", []) or []
    if not items:
        return f"<b>{settings.bot_brand}</b>\n\nТранзакций Stars пока нет."
    parts: list[str] = []
    for tx in items[:limit]:
        source = getattr(tx, "source", None)
        receiver = getattr(tx, "receiver", None)
        partner = source or receiver
        partner_type = getattr(partner, "type", "-") if partner else "-"
        parts.append(
            "\n".join(
                [
                    f"ID: <code>{getattr(tx, 'id', '-')}</code>",
                    f"Сумма: <code>{getattr(tx, 'amount', 0)}</code>",
                    f"Unix time: <code>{getattr(tx, 'date', 0)}</code>",
                    f"Партнер: <code>{partner_type}</code>",
                ]
            )
        )
    return f"<b>{settings.bot_brand}</b>\n\n<b>⭐ Последние транзакции Stars</b>\n\n" + "\n\n".join(parts)
