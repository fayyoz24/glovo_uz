from rest_framework.exceptions import APIException
from rest_framework import status


class OTPExpired(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "OTP code has expired."
    default_code = "otp_expired"


class OTPInvalid(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid OTP code."
    default_code = "otp_invalid"


class OTPMaxAttemptsReached(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "Too many OTP attempts. Please request a new code."
    default_code = "otp_max_attempts"


class OTPCooldownActive(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "Please wait before requesting a new OTP."
    default_code = "otp_cooldown"


class UserNotVerified(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "User account is not verified."
    default_code = "user_not_verified"


class UserInactive(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "User account is disabled."
    default_code = "user_inactive"


class OTPChannelUnavailable(APIException):
    status_code = 400
    default_detail = "Bu kanal mavjud emas yoki bog'lanmagan"