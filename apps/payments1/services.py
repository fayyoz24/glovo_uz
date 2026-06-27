import hashlib
import hmac
import secrets
import logging
from decimal import Decimal
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import Wallet, SavedCard, Payment, Refund, WalletTransaction, PaymentSession
from .constants import (
    PaymentStatus,
    PaymentMethod,
    TransactionType,
    WalletTransactionStatus,
    CardType,
    UZCARD_PREFIX,
    HUMO_PREFIX,
    WALLET_MAX_BALANCE,
    MIN_TOP_UP_AMOUNT,
    MAX_TOP_UP_AMOUNT,
    MIN_WITHDRAWAL_AMOUNT,
    MAX_WITHDRAWAL_AMOUNT,
    PAYMENT_SESSION_EXPIRY_MINUTES,
)
from .exceptions import (
    InsufficientWalletBalance,
    WalletMaxBalanceExceeded,
    InvalidCardNumber,
    PaymentAlreadyCompleted,
    PaymentAlreadyCancelled,
    RefundNotAllowed,
    RefundAmountExceeded,
    DuplicateTransaction,
    TopUpAmountInvalid,
    WithdrawalAmountInvalid,
    PaymentSessionExpired,
)
from .selectors import (
    get_wallet_for_update,
    get_total_refunded_amount,
    get_payment_session_by_token,
    card_exists_by_token,
)

logger = logging.getLogger(__name__)


# ─── Utilities ────────────────────────────────────────────────────────────────

def luhn_check(card_number: str) -> bool:
    """Luhn algoritmi bilan karta raqamini tekshirish."""
    digits = [int(d) for d in card_number if d.isdigit()]
    if len(digits) != 16:
        return False
    total = 0
    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def detect_card_type(card_number: str) -> str:
    """Karta prefiksi asosida turini aniqlash."""
    clean = card_number.replace(" ", "").replace("-", "")
    if clean.startswith(UZCARD_PREFIX):
        return CardType.UZCARD
    if clean.startswith(HUMO_PREFIX):
        return CardType.HUMO
    if clean.startswith("4"):
        return CardType.VISA
    if clean.startswith(("51", "52", "53", "54", "55")):
        return CardType.MASTERCARD
    return CardType.UZCARD  # default Uzbekistan


def mask_card_number(card_number: str) -> str:
    """8600 **** **** 1234 formatida qaytaradi."""
    clean = card_number.replace(" ", "")
    return f"{clean[:4]} **** **** {clean[-4:]}"


# ─── Wallet Services ──────────────────────────────────────────────────────────

@transaction.atomic
def credit_wallet(wallet: Wallet, amount: Decimal, transaction_type: str,
                  description: str = "", payment=None, reference_id: str = "") -> WalletTransaction:
    """
    Hamyonga pul qo'shish (select_for_update bilan).
    """
    locked_wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)

    new_balance = locked_wallet.balance + amount
    if new_balance > WALLET_MAX_BALANCE:
        raise WalletMaxBalanceExceeded()

    balance_before = locked_wallet.balance
    locked_wallet.balance = new_balance
    locked_wallet.save(update_fields=["balance", "updated_at"])

    txn = WalletTransaction.objects.create(
        wallet=locked_wallet,
        transaction_type=transaction_type,
        amount=amount,
        balance_before=balance_before,
        balance_after=new_balance,
        status=WalletTransactionStatus.COMPLETED,
        payment=payment,
        description=description,
        reference_id=reference_id,
    )
    logger.info(
        "Wallet credited: user=%s amount=%s balance_after=%s",
        locked_wallet.user_id, amount, new_balance,
    )
    return txn


@transaction.atomic
def debit_wallet(wallet: Wallet, amount: Decimal, transaction_type: str,
                 description: str = "", payment=None) -> WalletTransaction:
    """
    Hamyondan pul yechish.
    """
    locked_wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)

    if locked_wallet.balance < amount:
        raise InsufficientWalletBalance()

    balance_before = locked_wallet.balance
    locked_wallet.balance -= amount
    locked_wallet.save(update_fields=["balance", "updated_at"])

    txn = WalletTransaction.objects.create(
        wallet=locked_wallet,
        transaction_type=transaction_type,
        amount=amount,
        balance_before=balance_before,
        balance_after=locked_wallet.balance,
        status=WalletTransactionStatus.COMPLETED,
        payment=payment,
        description=description,
    )
    logger.info(
        "Wallet debited: user=%s amount=%s balance_after=%s",
        locked_wallet.user_id, amount, locked_wallet.balance,
    )
    return txn


def top_up_wallet(wallet: Wallet, amount: Decimal, reference_id: str = "") -> WalletTransaction:
    """Hamyonga tashqi to'lov orqali pul qo'shish."""
    if not (MIN_TOP_UP_AMOUNT <= amount <= MAX_TOP_UP_AMOUNT):
        raise TopUpAmountInvalid()

    return credit_wallet(
        wallet=wallet,
        amount=amount,
        transaction_type=TransactionType.TOP_UP,
        description=f"Hamyon to'ldirildi (+{amount} UZS)",
        reference_id=reference_id,
    )


def withdraw_from_wallet(wallet: Wallet, amount: Decimal) -> WalletTransaction:
    """Hamyondan pul chiqarish."""
    if not (MIN_WITHDRAWAL_AMOUNT <= amount <= MAX_WITHDRAWAL_AMOUNT):
        raise WithdrawalAmountInvalid()

    return debit_wallet(
        wallet=wallet,
        amount=amount,
        transaction_type=TransactionType.WITHDRAWAL,
        description=f"Hamyondan yechildi (-{amount} UZS)",
    )


# ─── Saved Card Services ──────────────────────────────────────────────────────

def add_saved_card(user, card_number: str, expire_month: int, expire_year: int,
                   gateway: str, token: str, is_default: bool = False) -> SavedCard:
    """Kartani tekshirib saqlash."""
    clean = card_number.replace(" ", "").replace("-", "")

    if not luhn_check(clean):
        raise InvalidCardNumber()

    if card_exists_by_token(token):
        raise DuplicateTransaction()

    card_type = detect_card_type(clean)

    if is_default:
        # Eski default kartani olib tashlash
        SavedCard.objects.filter(user=user, is_default=True).update(is_default=False)

    card = SavedCard.objects.create(
        user=user,
        card_type=card_type,
        masked_number=mask_card_number(clean),
        token=token,
        expire_month=expire_month,
        expire_year=expire_year,
        is_default=is_default,
        gateway=gateway,
    )
    return card


def remove_saved_card(card: SavedCard) -> None:
    card.delete()


def set_default_card(user, card: SavedCard) -> SavedCard:
    SavedCard.objects.filter(user=user, is_default=True).update(is_default=False)
    card.is_default = True
    card.save(update_fields=["is_default"])
    return card


# ─── Payment Services ─────────────────────────────────────────────────────────

def create_payment(order, user, method: str, amount: Decimal,
                   saved_card=None, ip_address: str = None) -> Payment:
    """Yangi to'lov yozuvi yaratish."""
    payment = Payment.objects.create(
        order=order,
        user=user,
        method=method,
        amount=amount,
        status=PaymentStatus.PENDING,
        saved_card=saved_card,
        ip_address=ip_address,
    )
    logger.info("Payment created: id=%s order=%s method=%s amount=%s", payment.id, order.id, method, amount)
    return payment


@transaction.atomic
def mark_payment_completed(payment: Payment, gateway_txn_id: str,
                           gateway_response: dict = None) -> Payment:
    """To'lovni muvaffaqiyatli deb belgilash."""
    if payment.status == PaymentStatus.COMPLETED:
        raise PaymentAlreadyCompleted()
    if payment.status == PaymentStatus.CANCELLED:
        raise PaymentAlreadyCancelled()

    payment.status = PaymentStatus.COMPLETED
    payment.gateway_transaction_id = gateway_txn_id
    payment.gateway_response = gateway_response or {}
    payment.paid_at = timezone.now()
    payment.save(update_fields=[
        "status", "gateway_transaction_id", "gateway_response", "paid_at", "updated_at"
    ])

    # Agar wallet bilan to'langan bo'lsa — debit qilish
    if payment.method == PaymentMethod.WALLET:
        wallet = get_wallet_for_update(payment.user)
        debit_wallet(
            wallet=wallet,
            amount=payment.amount,
            transaction_type=TransactionType.PAYMENT,
            description=f"Buyurtma #{payment.order_id} uchun to'lov",
            payment=payment,
        )

    logger.info("Payment completed: id=%s gateway_txn=%s", payment.id, gateway_txn_id)
    return payment


@transaction.atomic
def mark_payment_failed(payment: Payment, reason: str = "", gateway_response: dict = None) -> Payment:
    """To'lovni muvaffaqiyatsiz deb belgilash."""
    if payment.status in (PaymentStatus.COMPLETED, PaymentStatus.CANCELLED):
        return payment  # Idempotent

    payment.status = PaymentStatus.FAILED
    payment.failure_reason = reason
    payment.gateway_response = gateway_response or {}
    payment.failed_at = timezone.now()
    payment.save(update_fields=[
        "status", "failure_reason", "gateway_response", "failed_at", "updated_at"
    ])
    logger.warning("Payment failed: id=%s reason=%s", payment.id, reason)
    return payment


def cancel_payment(payment: Payment) -> Payment:
    """To'lovni bekor qilish (faqat pending)."""
    if payment.status == PaymentStatus.COMPLETED:
        raise PaymentAlreadyCompleted()
    if payment.status == PaymentStatus.CANCELLED:
        raise PaymentAlreadyCancelled()

    payment.status = PaymentStatus.CANCELLED
    payment.save(update_fields=["status", "updated_at"])
    return payment


# ─── Refund Services ──────────────────────────────────────────────────────────

@transaction.atomic
def initiate_refund(payment: Payment, amount: Decimal, reason: str = "",
                    initiated_by=None) -> Refund:
    """Qaytarishni boshlash."""
    if not payment.is_refundable:
        raise RefundNotAllowed()

    already_refunded = get_total_refunded_amount(payment)
    if amount > (payment.amount - already_refunded):
        raise RefundAmountExceeded()

    refund = Refund.objects.create(
        payment=payment,
        initiated_by=initiated_by,
        amount=amount,
        reason=reason,
        status=PaymentStatus.PENDING,
    )

    logger.info("Refund initiated: payment=%s amount=%s", payment.id, amount)
    return refund


@transaction.atomic
def complete_refund(refund: Refund, gateway_refund_id: str,
                    gateway_response: dict = None) -> Refund:
    """Qaytarishni muvaffaqiyatli deb belgilash va hamyonga qaytarish."""
    refund.status = PaymentStatus.COMPLETED
    refund.gateway_refund_id = gateway_refund_id
    refund.gateway_response = gateway_response or {}
    refund.save(update_fields=["status", "gateway_refund_id", "gateway_response", "updated_at"])

    # Agar wallet bilan to'langan bo'lsa — qaytarish
    if refund.payment.method == PaymentMethod.WALLET:
        wallet = get_wallet_for_update(refund.payment.user)
        credit_wallet(
            wallet=wallet,
            amount=refund.amount,
            transaction_type=TransactionType.REFUND,
            description=f"Qaytarish: buyurtma #{refund.payment.order_id}",
            payment=refund.payment,
        )

    # Payment statusini yangilash
    payment = refund.payment
    total_refunded = get_total_refunded_amount(payment)
    if total_refunded >= payment.amount:
        payment.status = PaymentStatus.REFUNDED
    else:
        payment.status = PaymentStatus.PARTIALLY_REFUNDED
    payment.save(update_fields=["status", "updated_at"])

    logger.info("Refund completed: refund=%s gateway_refund=%s", refund.id, gateway_refund_id)
    return refund


# ─── Payment Session Services ─────────────────────────────────────────────────

def create_payment_session(payment: Payment, redirect_url: str = "") -> PaymentSession:
    """To'lov sessiyasini yaratish."""
    token = secrets.token_urlsafe(32)
    session = PaymentSession.objects.create(
        payment=payment,
        session_token=token,
        redirect_url=redirect_url,
        expires_at=timezone.now() + timedelta(minutes=PAYMENT_SESSION_EXPIRY_MINUTES),
    )
    return session


def consume_payment_session(token: str) -> PaymentSession:
    """Sessiyani ishlatilgan deb belgilash."""
    session = get_payment_session_by_token(token)
    if not session:
        raise PaymentSessionExpired()
    if session.is_expired:
        raise PaymentSessionExpired()

    session.is_used = True
    session.save(update_fields=["is_used"])
    return session


# ─── Gateway Routing ──────────────────────────────────────────────────────────

def route_payment_to_gateway(payment: Payment) -> dict:
    """
    To'lov usuliga qarab tegishli gateway'ga yo'naltirish.
    Returns: {'redirect_url': ..., 'payment_token': ...}
    """
    if payment.method == PaymentMethod.PAYME:
        return _init_payme_payment(payment)
    elif payment.method == PaymentMethod.CLICK:
        return _init_click_payment(payment)
    elif payment.method == PaymentMethod.UPAY:
        return _init_upay_payment(payment)
    elif payment.method == PaymentMethod.WALLET:
        return _init_wallet_payment(payment)
    elif payment.method == PaymentMethod.CASH:
        return _init_cash_payment(payment)
    else:
        from .exceptions import PaymentException
        raise PaymentException("Noto'g'ri to'lov usuli.")


def _init_payme_payment(payment: Payment) -> dict:
    """Payme.uz orqali to'lov boshlash."""
    import base64
    from django.conf import settings

    merchant_id = settings.PAYME_MERCHANT_ID
    amount_tiyin = int(payment.amount * 100)  # UZS → tiyin
    order_id = str(payment.order_id)

    params = f"m={merchant_id};ac.order_id={order_id};a={amount_tiyin}"
    encoded = base64.b64encode(params.encode()).decode()
    redirect_url = f"https://checkout.paycom.uz/{encoded}"

    payment.gateway_order_id = order_id
    payment.save(update_fields=["gateway_order_id"])

    return {
        "gateway": "payme",
        "redirect_url": redirect_url,
        "order_id": order_id,
    }


def _init_click_payment(payment: Payment) -> dict:
    """Click.uz orqali to'lov boshlash."""
    from django.conf import settings

    merchant_id = settings.CLICK_MERCHANT_ID
    service_id = settings.CLICK_SERVICE_ID
    amount = int(payment.amount)
    order_id = str(payment.order_id)
    return_url = settings.CLICK_RETURN_URL

    redirect_url = (
        f"https://my.click.uz/services/pay?"
        f"service_id={service_id}&merchant_id={merchant_id}"
        f"&amount={amount}&transaction_param={order_id}"
        f"&return_url={return_url}"
    )

    payment.gateway_order_id = order_id
    payment.save(update_fields=["gateway_order_id"])

    return {
        "gateway": "click",
        "redirect_url": redirect_url,
        "order_id": order_id,
    }


def _init_upay_payment(payment: Payment) -> dict:
    """UPAY (UzCard/Humo) orqali to'lov boshlash."""
    from django.conf import settings

    order_id = str(payment.order_id)
    payment.gateway_order_id = order_id
    payment.save(update_fields=["gateway_order_id"])

    return {
        "gateway": "upay",
        "order_id": order_id,
        "amount": str(payment.amount),
        "terminal_id": settings.UPAY_TERMINAL_ID,
    }


def _init_wallet_payment(payment: Payment) -> dict:
    """Hamyon to'lovi — to'g'ridan-to'g'ri debit."""
    return {
        "gateway": "wallet",
        "message": "Hamyon orqali to'lov tayyor.",
    }


def _init_cash_payment(payment: Payment) -> dict:
    """Naqd pul — faqat tasdiqlash."""
    return {
        "gateway": "cash",
        "message": "Kurier yetkazib kelganda naqd to'lang.",
    }


# ─── Webhook Handlers ─────────────────────────────────────────────────────────

def handle_payme_webhook(data: dict) -> dict:
    """
    Payme webhook'ini qayta ishlash.
    https://developer.paycom.uz/ru/merch_api/
    """
    method = data.get("method")
    params = data.get("params", {})

    if method == "CheckPerformTransaction":
        order_id = params.get("account", {}).get("order_id")
        from orders.selectors import get_order_by_id
        order = get_order_by_id(order_id)
        if not order:
            return {"error": {"code": -31050, "message": "Buyurtma topilmadi."}}
        return {"result": {"allow": True}}

    elif method == "CreateTransaction":
        txn_id = params.get("id")
        order_id = params.get("account", {}).get("order_id")

        payment = Payment.objects.filter(order__id=order_id).first()
        if not payment:
            return {"error": {"code": -31050, "message": "To'lov topilmadi."}}

        payment.gateway_transaction_id = txn_id
        payment.status = PaymentStatus.PROCESSING
        payment.save(update_fields=["gateway_transaction_id", "status", "updated_at"])

        return {"result": {"create_time": int(timezone.now().timestamp() * 1000), "transaction": txn_id, "state": 1}}

    elif method == "PerformTransaction":
        txn_id = params.get("id")
        payment = Payment.objects.filter(gateway_transaction_id=txn_id).first()
        if not payment:
            return {"error": {"code": -31003, "message": "Tranzaksiya topilmadi."}}

        mark_payment_completed(payment, gateway_txn_id=txn_id, gateway_response=data)
        return {"result": {"perform_time": int(timezone.now().timestamp() * 1000), "transaction": txn_id, "state": 2}}

    elif method == "CancelTransaction":
        txn_id = params.get("id")
        payment = Payment.objects.filter(gateway_transaction_id=txn_id).first()
        if payment:
            mark_payment_failed(payment, reason="Payme tomonidan bekor qilindi.")
        return {"result": {"cancel_time": int(timezone.now().timestamp() * 1000), "transaction": txn_id, "state": -1}}

    return {"error": {"code": -32601, "message": "Method not found."}}


def handle_click_webhook(data: dict) -> dict:
    """Click webhook'ini qayta ishlash."""
    action = data.get("action")
    order_id = data.get("merchant_trans_id")
    payment_id = data.get("payment_id")
    error_code = data.get("error", 0)

    payment = Payment.objects.filter(order__id=order_id).first()
    if not payment:
        return {"error": -5, "error_note": "To'lov topilmadi."}

    if action == 0:  # Prepare
        return {
            "click_trans_id": payment_id,
            "merchant_trans_id": order_id,
            "merchant_prepare_id": str(payment.id),
            "error": 0,
            "error_note": "Success",
        }

    elif action == 1:  # Complete
        if error_code == 0:
            mark_payment_completed(payment, gateway_txn_id=str(payment_id), gateway_response=data)
        else:
            mark_payment_failed(payment, reason=f"Click xato kodi: {error_code}")
        return {
            "click_trans_id": payment_id,
            "merchant_trans_id": order_id,
            "error": 0,
            "error_note": "Success",
        }

    return {"error": -3, "error_note": "Action noto'g'ri."}


# payment refund

from apps.notifications.tasks import send_payment_notification
from apps.notifications.constants import NotificationEvent

send_payment_notification.delay(
    event=NotificationEvent.PAYMENT_RECEIVED,
    customer_id=order.customer_id,
    context={"amount": str(transaction.amount)},
    order_id=str(order.id),
)