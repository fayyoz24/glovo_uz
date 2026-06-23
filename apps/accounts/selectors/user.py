from django.utils import timezone
from apps.accounts.models import User, OTPCode


def get_user_by_phone(phone: str) -> User | None:
    return User.objects.filter(phone=phone).first()


def get_user_by_id(user_id) -> User | None:
    return User.objects.filter(id=user_id, is_active=True).first()


def get_active_otp(phone: str) -> OTPCode | None:
    """Return the latest non-used, non-expired OTP for a phone number."""
    return (
        OTPCode.objects.filter(
            phone=phone,
            is_used=False,
            expires_at__gt=timezone.now(),
        )
        .order_by("-created_at")
        .first()
    )
