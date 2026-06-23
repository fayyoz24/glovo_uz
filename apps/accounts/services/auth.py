import random
import string
from django.utils import timezone
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User, OTPCode
from apps.accounts.constants import UserRole, OTP_COOLDOWN_SECONDS, OTP_MAX_ATTEMPTS
from apps.accounts.exceptions import (
    OTPCooldownActive,
    OTPExpired,
    OTPInvalid,
    OTPMaxAttemptsReached,
    UserInactive,
)
from apps.accounts.selectors import get_user_by_phone, get_active_otp


def _generate_otp_code(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def request_otp(phone: str) -> OTPCode:
    """
    Generate and send an OTP for the given phone number.
    Enforces cooldown: if a valid OTP was issued within OTP_COOLDOWN_SECONDS, raise.
    """
    last_otp = OTPCode.objects.filter(phone=phone).order_by("-created_at").first()
    if last_otp:
        elapsed = (timezone.now() - last_otp.created_at).total_seconds()
        if elapsed < OTP_COOLDOWN_SECONDS:
            raise OTPCooldownActive()

    code = _generate_otp_code()
    otp = OTPCode.objects.create(phone=phone, code=code)

    # TODO: integrate SMS gateway (Eskiz / SMS.uz)
    # send_sms.delay(phone=phone, message=f"Your Glovo UZ code: {code}")

    return otp


def verify_otp_and_login(phone: str, code: str) -> dict:
    """
    Verify OTP code, create or retrieve the user, return JWT tokens.
    """
    otp = get_active_otp(phone)

    if otp is None:
        raise OTPExpired()

    if otp.attempts >= OTP_MAX_ATTEMPTS:
        raise OTPMaxAttemptsReached()

    otp.attempts += 1
    otp.save(update_fields=["attempts"])

    if otp.code != code:
        raise OTPInvalid()

    if otp.is_expired:
        raise OTPExpired()

    with transaction.atomic():
        otp.is_used = True
        otp.save(update_fields=["is_used"])

        user, created = User.objects.get_or_create(
            phone=phone,
            defaults={"role": UserRole.CUSTOMER, "is_verified": True},
        )

        if not created and not user.is_active:
            raise UserInactive()

        if not user.is_verified:
            user.is_verified = True
            user.save(update_fields=["is_verified"])

    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user_id": str(user.id),
        "role": user.role,
        "is_new": created,
    }
