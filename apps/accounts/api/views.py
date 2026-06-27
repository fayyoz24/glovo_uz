from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.accounts.api.serializers import (
    RequestOTPSerializer,
    VerifyOTPSerializer,
    OTPChannelsSerializer,
    UserMeSerializer,
    UpdateProfileSerializer,
    TelegramLinkSerializer,
    TelegramConfirmSerializer,
)
from apps.accounts.services.auth import (
    get_available_channels,
    request_otp,
    verify_otp_and_login,
)
from apps.accounts.services.otp import (
    initiate_telegram_link,
    confirm_telegram_link,
    unlink_telegram,
)
from apps.accounts.services.profile import update_user_profile


class OTPChannelsView(APIView):
    """
    GET /api/auth/otp-channels/?phone=998901234567

    Frontend login ekranida foydalanuvchiga qaysi kanallar mavjudligini ko'rsatadi.
    Telegram bog'langan bo'lsa — ikki variant chiqadi, aks holda faqat SMS.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        phone = request.query_params.get("phone", "")
        data = get_available_channels(phone)
        serializer = OTPChannelsSerializer(data)
        return Response(serializer.data)


class RequestOTPView(APIView):
    """
    POST /api/auth/request-otp/
    { "phone": "998901234567", "channel": "sms" | "telegram" }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request_otp(
            phone=serializer.validated_data["phone"],
            channel=serializer.validated_data["channel"],
        )
        return Response({"detail": "OTP yuborildi."}, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    """
    POST /api/auth/verify-otp/
    { "phone": "998901234567", "code": "123456", "channel": "sms" | "telegram" }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = verify_otp_and_login(
            phone=serializer.validated_data["phone"],
            code=serializer.validated_data["code"],
            channel=serializer.validated_data["channel"],
        )
        return Response(tokens, status=status.HTTP_200_OK)


class MeView(APIView):
    """
    GET  /api/auth/me/   — profil ma'lumotlari
    PATCH /api/auth/me/  — profil yangilash
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UpdateProfileSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = update_user_profile(request.user, serializer.validated_data)
        return Response(UserMeSerializer(user).data)


class TelegramInitiateLinkView(APIView):
    """
    POST /api/auth/telegram/link/

    Foydalanuvchi "Telegram'ni ulash" tugmasini bosganda chaqiriladi.
    Javobda deep link qaytariladi — frontend uni ko'rsatadi.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        binding = initiate_telegram_link(request.user)
        bot_username = settings.TELEGRAM_BOT_USERNAME
        link_url = f"https://t.me/{bot_username}?start={binding.link_token}"
        serializer = TelegramLinkSerializer({
            "link_url": link_url,
            "link_token": binding.link_token,
        })
        return Response(serializer.data, status=status.HTTP_200_OK)


class TelegramUnlinkView(APIView):
    """
    DELETE /api/auth/telegram/link/

    Foydalanuvchi Telegram'ni ajratib olmoqchi bo'lganda.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        unlink_telegram(request.user)
        return Response({"detail": "Telegram ajratildi."}, status=status.HTTP_204_NO_CONTENT)


class TelegramWebhookView(APIView):
    """
    POST /api/auth/telegram/webhook/

    Telegram bot shu endpointga murojaat qiladi:
    foydalanuvchi /start <token> yuborganda.

    Bot secret token orqali himoyalangan (TELEGRAM_WEBHOOK_SECRET).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Webhook secret tekshiruvi
        secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if secret != settings.TELEGRAM_WEBHOOK_SECRET:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = TelegramConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        confirm_telegram_link(
            token=serializer.validated_data["token"],
            telegram_user_id=serializer.validated_data["telegram_user_id"],
            telegram_username=serializer.validated_data.get("telegram_username", ""),
        )
        return Response({"detail": "Telegram bog'landi."}, status=status.HTTP_200_OK)