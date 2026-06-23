from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.api.serializers import (
    RequestOTPSerializer,
    VerifyOTPSerializer,
    UserMeSerializer,
    UpdateProfileSerializer,
)
from apps.accounts.services import request_otp, verify_otp_and_login, update_user_profile


class RequestOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request_otp(phone=serializer.validated_data["phone"])
        return Response({"detail": "OTP sent."}, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = verify_otp_and_login(
            phone=serializer.validated_data["phone"],
            code=serializer.validated_data["code"],
        )
        return Response(tokens, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UpdateProfileSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = update_user_profile(request.user, serializer.validated_data)
        return Response(UserMeSerializer(user).data)
