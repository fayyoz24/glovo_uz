from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.accounts.api.views import (
    OTPChannelsView,
    RequestOTPView,
    VerifyOTPView,
    MeView,
    TelegramInitiateLinkView,
    TelegramUnlinkView,
    TelegramWebhookView,
)

urlpatterns = [
    # OTP
    path("auth/otp-channels/",  OTPChannelsView.as_view(),  name="otp-channels"),
    path("auth/request-otp/",   RequestOTPView.as_view(),   name="request-otp"),
    path("auth/verify-otp/",    VerifyOTPView.as_view(),    name="verify-otp"),

    # JWT
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    # Profile
    path("auth/me/",            MeView.as_view(),           name="me"),

    # Telegram
    path("auth/telegram/link/",    TelegramInitiateLinkView.as_view(), name="telegram-link"),
    path("auth/telegram/unlink/",  TelegramUnlinkView.as_view(),       name="telegram-unlink"),
    path("auth/telegram/webhook/", TelegramWebhookView.as_view(),      name="telegram-webhook"),
]