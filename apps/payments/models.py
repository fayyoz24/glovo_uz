import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

from .constants import (
    PaymentStatus,
    PaymentMethod,
    TransactionType,
    WalletTransactionStatus,
    CardType,
    WALLET_MAX_BALANCE,
)


class Wallet(models.Model):
    """
    Har bir foydalanuvchining ichki hamyoni.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallet",
    )
    balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(WALLET_MAX_BALANCE),
        ],
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wallets"
        verbose_name = "Hamyon"
        verbose_name_plural = "Hamyonlar"

    def __str__(self):
        return f"{self.user} — {self.balance} UZS"


class SavedCard(models.Model):
    """
    Foydalanuvchi tomonidan saqlangan bank kartalari.
    Karta raqami tokenizatsiya qilingan holda saqlanadi.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_cards",
    )
    card_type = models.CharField(max_length=20, choices=CardType.choices)
    masked_number = models.CharField(max_length=19)  # e.g. "8600 **** **** 1234"
    token = models.CharField(max_length=255, unique=True)  # gateway token
    expire_month = models.PositiveSmallIntegerField()
    expire_year = models.PositiveSmallIntegerField()
    is_default = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    gateway = models.CharField(max_length=20, choices=PaymentMethod.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "saved_cards"
        verbose_name = "Saqlangan karta"
        verbose_name_plural = "Saqlangan kartalar"
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.user} — {self.masked_number}"


class Payment(models.Model):
    """
    Har bir buyurtma uchun to'lov yozuvi.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="payment",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    status = models.CharField(
        max_length=25,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default="UZS")

    # Gateway-specific fields
    gateway_transaction_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    gateway_order_id = models.CharField(max_length=255, blank=True, null=True)
    gateway_response = models.JSONField(default=dict, blank=True)

    # Card reference (if paid by card)
    saved_card = models.ForeignKey(
        SavedCard,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payments",
    )

    # Timestamps
    paid_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Meta
    failure_reason = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = "payments"
        verbose_name = "To'lov"
        verbose_name_plural = "To'lovlar"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["method"]),
            models.Index(fields=["user", "status"]),
            models.Index(fields=["gateway_transaction_id"]),
        ]

    def __str__(self):
        return f"Payment #{self.id} — {self.amount} UZS ({self.status})"

    @property
    def is_refundable(self):
        from django.utils import timezone
        from datetime import timedelta
        from .constants import REFUND_WINDOW_HOURS

        if self.status != PaymentStatus.COMPLETED:
            return False
        if self.paid_at is None:
            return False
        return timezone.now() <= self.paid_at + timedelta(hours=REFUND_WINDOW_HOURS)


class Refund(models.Model):
    """
    Qaytarish yozuvlari.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(
        Payment,
        on_delete=models.PROTECT,
        related_name="refunds",
    )
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="initiated_refunds",
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=25,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    gateway_refund_id = models.CharField(max_length=255, blank=True, null=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "refunds"
        verbose_name = "Qaytarish"
        verbose_name_plural = "Qaytarishlar"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Refund #{self.id} — {self.amount} UZS"


class WalletTransaction(models.Model):
    """
    Hamyon harakatlari tarixi.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    balance_before = models.DecimalField(max_digits=14, decimal_places=2)
    balance_after = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=WalletTransactionStatus.choices,
        default=WalletTransactionStatus.PENDING,
    )
    # Reference to the triggering payment (if any)
    payment = models.ForeignKey(
        Payment,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="wallet_transactions",
    )
    description = models.CharField(max_length=255, blank=True)
    reference_id = models.CharField(max_length=100, blank=True, null=True)  # external ref
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wallet_transactions"
        verbose_name = "Hamyon tranzaksiyasi"
        verbose_name_plural = "Hamyon tranzaksiyalari"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["wallet", "status"]),
            models.Index(fields=["transaction_type"]),
        ]

    def __str__(self):
        return f"{self.transaction_type} — {self.amount} UZS ({self.status})"


class PaymentSession(models.Model):
    """
    Vaqtincha to'lov sessiyasi (gateway redirect uchun).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name="session",
    )
    session_token = models.CharField(max_length=255, unique=True)
    redirect_url = models.URLField(blank=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payment_sessions"
        verbose_name = "To'lov sessiyasi"
        verbose_name_plural = "To'lov sessiyalari"

    def __str__(self):
        return f"Session for Payment #{self.payment_id}"

    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at
