from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.accounts.api.views import RequestOTPView, VerifyOTPView, MeView

urlpatterns = [
    path("auth/request-otp/", RequestOTPView.as_view(), name="auth-request-otp"),
    path("auth/verify-otp/", VerifyOTPView.as_view(), name="auth-verify-otp"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("me/", MeView.as_view(), name="me"),
]
