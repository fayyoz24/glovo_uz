from django.utils import timezone
from apps.accounts.models import User, OTPCode, TelegramBinding


def get_user_by_phone(phone: str) -> User | None:
    return User.objects.filter(phone=phone).first()


def get_user_by_id(user_id) -> User | None:
    return User.objects.filter(id=user_id, is_active=True).first()


def get_active_otp(phone: str, channel: str) -> OTPCode | None:
    """Return the latest active OTP for a phone number filtered by channel."""
    return (
        OTPCode.objects.filter(
            phone=phone,
            channel=channel,
            is_used=False,
            expires_at__gt=timezone.now(),
        )
        .order_by("-created_at")
        .first()
    )


def get_telegram_binding(phone: str) -> TelegramBinding | None:
    """Return confirmed TelegramBinding for a given phone, if exists."""
    return (
        TelegramBinding.objects.filter(
            user__phone=phone,
            is_confirmed=True,
        )
        .select_related("user")
        .first()
    )


def get_telegram_binding_by_token(token) -> TelegramBinding | None:
    """Used by bot webhook to confirm the deep-link token."""
    return (
        TelegramBinding.objects.filter(link_token=token)
        .select_related("user")
        .first()
    )