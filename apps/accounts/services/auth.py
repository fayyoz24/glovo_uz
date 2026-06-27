import random
import string
from django.utils import timezone
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User, OTPCode, OTPChannel, TelegramBinding
from apps.accounts.constants import UserRole, OTP_COOLDOWN_SECONDS, OTP_MAX_ATTEMPTS
from apps.accounts.exceptions import (
    OTPCooldownActive,
    OTPExpired,
    OTPInvalid,
    OTPMaxAttemptsReached,
    OTPChannelUnavailable,
    UserInactive,
)
from apps.accounts.selectors.user import (
    get_user_by_phone,
    get_active_otp,
    get_telegram_binding,
)
from apps.notifications.tasks import send_otp_sms, send_otp_telegram


def _generate_otp_code(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def get_available_channels(phone: str) -> dict:
    """
    Frontend uchun: bu telefon qaysi OTP kanallarini ishlatishi mumkin.

    Returns:
        {
            "channels": ["sms"] | ["sms", "telegram"],
            "default":  "sms"   | "telegram",
        }
    """
    binding = get_telegram_binding(phone)
    if binding:
        return {"channels": [OTPChannel.SMS, OTPChannel.TELEGRAM], "default": OTPChannel.TELEGRAM}
    return {"channels": [OTPChannel.SMS], "default": OTPChannel.SMS}


def request_otp(phone: str, channel: str = OTPChannel.SMS) -> OTPCode:
    """
    Generate and send an OTP for the given phone number via the chosen channel.

    Raises:
        OTPCooldownActive       – agar oxirgi OTP OTP_COOLDOWN_SECONDS ichida yuborilgan bo'lsa
        OTPChannelUnavailable   – agar Telegram tanlansa, lekin bog'lanmagan bo'lsa
    """
    # Cooldown tekshiruvi (channel'dan qat'i nazar)
    last_otp = (
        OTPCode.objects.filter(phone=phone)
        .order_by("-created_at")
        .first()
    )
    if last_otp:
        elapsed = (timezone.now() - last_otp.created_at).total_seconds()
        if elapsed < OTP_COOLDOWN_SECONDS:
            raise OTPCooldownActive()

    # Telegram tanlansa — binding mavjudligini tekshir
    telegram_user_id = None
    if channel == OTPChannel.TELEGRAM:
        binding = get_telegram_binding(phone)
        if not binding:
            raise OTPChannelUnavailable()
        telegram_user_id = binding.telegram_user_id

    code = _generate_otp_code()
    otp = OTPCode.objects.create(phone=phone, code=code, channel=channel)

    # Kanal bo'yicha yuborish
    if channel == OTPChannel.TELEGRAM:
        send_otp_telegram.delay(
            telegram_user_id=telegram_user_id,
            code=code,
        )
    else:
        send_otp_sms.delay(phone=phone, code=code)

    return otp


def verify_otp_and_login(phone: str, code: str, channel: str = OTPChannel.SMS) -> dict:
    """
    Verify OTP code, create or retrieve the user, return JWT tokens.
    """
    otp = get_active_otp(phone, channel)

    if otp is None:
        raise OTPExpired()

    if otp.attempts >= OTP_MAX_ATTEMPTS:
        raise OTPMaxAttemptsReached()

    otp.increment_attempts()

    if otp.code != code:
        raise OTPInvalid()

    if otp.is_expired:
        raise OTPExpired()

    with transaction.atomic():
        otp.mark_used()

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