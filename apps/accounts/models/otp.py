import uuid
from django.db import models
from django.utils import timezone
from apps.accounts.constants import OTP_EXPIRY_SECONDS
from datetime import timedelta


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
        default=lambda: timezone.now() + timedelta(seconds=OTP_EXPIRY_SECONDS),
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
        return f"OTP({self.phone})"

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
