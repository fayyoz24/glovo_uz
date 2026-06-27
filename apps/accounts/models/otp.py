import uuid
from django.db import models
from django.utils import timezone
from apps.accounts.constants import OTP_EXPIRY_SECONDS
from datetime import timedelta
from apps.accounts.utils.phone import otp_expiry_time

class OTPChannel(models.TextChoices):
    SMS      = "sms",      "SMS"
    TELEGRAM = "telegram", "Telegram"


class OTPCode(models.Model):
    MAX_ATTEMPTS = 5

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    phone = models.CharField(
        max_length=20,
        db_index=True,
    )
    code = models.CharField(
        max_length=6,
    )
    channel = models.CharField(
        max_length=20,
        choices=OTPChannel.choices,
        default=OTPChannel.SMS,
    )
    is_used = models.BooleanField(
        default=False,
        db_index=True,
    )
    attempts = models.PositiveSmallIntegerField(
        default=0,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    expires_at = models.DateTimeField(
        default=otp_expiry_time,
        db_index=True,
    )

    class Meta:
        db_table = "accounts_otp_code"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["phone", "is_used"]),
            models.Index(fields=["phone", "created_at"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self) -> str:
        return f"OTP({self.phone}, {self.channel})"

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def is_blocked(self) -> bool:
        return self.attempts >= self.MAX_ATTEMPTS

    @property
    def can_verify(self) -> bool:
        return (
            not self.is_used
            and not self.is_expired
            and not self.is_blocked
        )

    def increment_attempts(self) -> None:
        self.attempts += 1
        self.save(update_fields=["attempts"])

    def mark_used(self) -> None:
        self.is_used = True
        self.save(update_fields=["is_used"])

    def extend(self, seconds: int) -> None:
        self.expires_at = timezone.now() + timedelta(seconds=seconds)
        self.save(update_fields=["expires_at"])


class TelegramBinding(models.Model):
    """
    User o'z Telegram akkauntini bir marta bog'laydi.
    Shundan so'ng login paytida OTP kanalini tanlash imkoni paydo bo'ladi.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="telegram_binding",
    )
    telegram_user_id = models.BigIntegerField(
        unique=True,
        help_text="Telegram chat_id (from bot)",
    )
    telegram_username = models.CharField(
        max_length=100,
        blank=True,
        help_text="@username (optional, for display)",
    )
    link_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text="Deep-link token: t.me/Bot?start=<token>",
    )
    is_confirmed = models.BooleanField(
        default=False,
        help_text="True after user clicked the deep link in Telegram",
    )
    linked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounts_telegram_binding"
        indexes = [
            models.Index(fields=["link_token"]),
            models.Index(fields=["telegram_user_id"]),
        ]

    def __str__(self) -> str:
        return f"TelegramBinding({self.user.phone} → tg:{self.telegram_user_id})"