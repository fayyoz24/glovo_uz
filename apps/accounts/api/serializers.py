from rest_framework import serializers
from apps.accounts.models import User
from apps.accounts.constants import Language


class RequestOTPSerializer(serializers.Serializer):
    phone = serializers.RegexField(
        regex=r"^\+?998\d{9}$",
        error_messages={"invalid": "Enter a valid Uzbekistan phone number (+998XXXXXXXXX)."},
    )


class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.RegexField(regex=r"^\+?998\d{9}$")
    code = serializers.CharField(min_length=6, max_length=6)


class UserMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone", "email", "full_name", "role", "language", "is_verified"]
        read_only_fields = ["id", "phone", "role", "is_verified"]

    def validate_language(self, value):
        valid_langs = [lang[0] for lang in Language.CHOICES]
        if value not in valid_langs:
            raise serializers.ValidationError("Unsupported language.")
        return value


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["full_name", "email", "language"]
