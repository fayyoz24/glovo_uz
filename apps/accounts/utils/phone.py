from phonenumbers import parse, format_number, PhoneNumberFormat
from datetime import timedelta
from django.utils import timezone

def normalize_phone(phone: str) -> str:
    parsed = parse(phone, "UZ")
    return format_number(parsed, PhoneNumberFormat.E164)


def otp_expiry_time():
    return timezone.now() + timedelta(seconds=OTP_EXPIRY_SECONDS)