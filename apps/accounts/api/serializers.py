from rest_framework import serializers
from apps.accounts.models import User, OTPChannel
from apps.accounts.constants import Language

PHONE_REGEX = r"^\+?998\d{9}$"
PHONE_ERROR = "To'g'ri O'zbekiston telefon raqamini kiriting (+998XXXXXXXXX)."


class RequestOTPSerializer(serializers.Serializer):
    phone = serializers.RegexField(
        regex=PHONE_REGEX,
        error_messages={"invalid": PHONE_ERROR},
    )
    channel = serializers.ChoiceField(
        choices=OTPChannel.choices,
        default=OTPChannel.SMS,
    )


class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.RegexField(
        regex=PHONE_REGEX,
        error_messages={"invalid": PHONE_ERROR},
    )
    code = serializers.CharField(min_length=6, max_length=6)
    channel = serializers.ChoiceField(
        choices=OTPChannel.choices,
        default=OTPChannel.SMS,
    )


class OTPChannelsSerializer(serializers.Serializer):
    """GET /auth/otp-channels/?phone=... javobini serializatsiya qiladi."""
    channels = serializers.ListField(child=serializers.CharField())
    default = serializers.CharField()


class UserMeSerializer(serializers.ModelSerializer):
    telegram_linked = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "phone", "email", "full_name",
            "role", "language", "is_verified", "telegram_linked",
        ]
        read_only_fields = ["id", "phone", "role", "is_verified", "telegram_linked"]

    def get_telegram_linked(self, obj) -> bool:
        return hasattr(obj, "telegram_binding") and obj.telegram_binding.is_confirmed

    def validate_language(self, value):
        valid_langs = [lang[0] for lang in Language.CHOICES]
        if value not in valid_langs:
            raise serializers.ValidationError("Qo'llab-quvvatlanmaydigan til.")
        return value


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["full_name", "email", "language"]


class TelegramLinkSerializer(serializers.Serializer):
    """Telegram deep link initiate javobi."""
    link_url = serializers.CharField()
    link_token = serializers.UUIDField()


class TelegramConfirmSerializer(serializers.Serializer):
    """Bot webhook dan keladigan payload."""
    token = serializers.UUIDField()
    telegram_user_id = serializers.IntegerField()
    telegram_username = serializers.CharField(required=False, default="")