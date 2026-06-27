from django.db.models import QuerySet, Sum, Q
from django.utils import timezone

from .models import Wallet, SavedCard, Payment, Refund, WalletTransaction, PaymentSession
from .constants import PaymentStatus, WalletTransactionStatus


# ─── Wallet ───────────────────────────────────────────────────────────────────

def get_wallet_by_user(user) -> Wallet:
    """Foydalanuvchining hamyonini qaytaradi (yo'q bo'lsa yaratadi)."""
    wallet, _ = Wallet.objects.get_or_create(user=user)
    return wallet


def get_wallet_for_update(user) -> Wallet:
    """select_for_update() bilan hamyon (atomic operatsiyalar uchun)."""
    return Wallet.objects.select_for_update().get(user=user)


# ─── SavedCard ────────────────────────────────────────────────────────────────

def get_saved_cards(user) -> QuerySet:
    return SavedCard.objects.filter(user=user).order_by("-is_default", "-created_at")


def get_saved_card_by_id(card_id, user) -> SavedCard | None:
    return SavedCard.objects.filter(id=card_id, user=user).first()


def get_default_card(user) -> SavedCard | None:
    return SavedCard.objects.filter(user=user, is_default=True).first()


def card_exists_by_token(token: str) -> bool:
    return SavedCard.objects.filter(token=token).exists()


# ─── Payment ──────────────────────────────────────────────────────────────────

def get_payment_by_id(payment_id) -> Payment | None:
    return (
        Payment.objects
        .select_related("order", "user", "saved_card")
        .filter(id=payment_id)
        .first()
    )


def get_payment_by_order(order) -> Payment | None:
    return Payment.objects.filter(order=order).select_related("order").first()


def get_payment_by_gateway_txn(gateway_txn_id: str) -> Payment | None:
    return Payment.objects.filter(gateway_transaction_id=gateway_txn_id).first()


def get_user_payments(user, filters: dict | None = None) -> QuerySet:
    qs = Payment.objects.filter(user=user).select_related("order", "saved_card")

    if filters:
        if status := filters.get("status"):
            qs = qs.filter(status=status)
        if method := filters.get("method"):
            qs = qs.filter(method=method)
        if date_from := filters.get("date_from"):
            qs = qs.filter(created_at__gte=date_from)
        if date_to := filters.get("date_to"):
            qs = qs.filter(created_at__lte=date_to)

    return qs.order_by("-created_at")


def get_pending_payments_older_than(minutes: int) -> QuerySet:
    """Muddati o'tgan pending to'lovlar (auto-cancel uchun)."""
    cutoff = timezone.now() - timezone.timedelta(minutes=minutes)
    return Payment.objects.filter(
        status=PaymentStatus.PENDING,
        created_at__lte=cutoff,
    )


def get_all_payments(filters: dict | None = None) -> QuerySet:
    """Admin uchun barcha to'lovlar."""
    qs = Payment.objects.select_related("order", "user", "saved_card")

    if filters:
        if status := filters.get("status"):
            qs = qs.filter(status=status)
        if method := filters.get("method"):
            qs = qs.filter(method=method)
        if user_id := filters.get("user_id"):
            qs = qs.filter(user_id=user_id)

    return qs.order_by("-created_at")


# ─── Refund ───────────────────────────────────────────────────────────────────

def get_refunds_by_payment(payment) -> QuerySet:
    return Refund.objects.filter(payment=payment).order_by("-created_at")


def get_total_refunded_amount(payment) -> float:
    result = Refund.objects.filter(
        payment=payment,
        status=PaymentStatus.COMPLETED,
    ).aggregate(total=Sum("amount"))
    return result["total"] or 0


# ─── WalletTransaction ────────────────────────────────────────────────────────

def get_wallet_transactions(wallet, filters: dict | None = None) -> QuerySet:
    qs = WalletTransaction.objects.filter(wallet=wallet)

    if filters:
        if txn_type := filters.get("transaction_type"):
            qs = qs.filter(transaction_type=txn_type)
        if status := filters.get("status"):
            qs = qs.filter(status=status)

    return qs.order_by("-created_at")


def get_completed_wallet_transactions(wallet) -> QuerySet:
    return WalletTransaction.objects.filter(
        wallet=wallet,
        status=WalletTransactionStatus.COMPLETED,
    ).order_by("-created_at")


# ─── PaymentSession ───────────────────────────────────────────────────────────

def get_payment_session_by_token(token: str) -> PaymentSession | None:
    return (
        PaymentSession.objects
        .select_related("payment")
        .filter(session_token=token, is_used=False)
        .first()
    )


def get_active_session_by_payment(payment) -> PaymentSession | None:
    return PaymentSession.objects.filter(
        payment=payment,
        is_used=False,
        expires_at__gt=timezone.now(),
    ).first()
