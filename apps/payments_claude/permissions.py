from rest_framework.permissions import BasePermission, IsAuthenticated


class IsPaymentOwner(BasePermission):
    """Faqat to'lov egasi ko'ra oladi."""

    message = "Siz bu to'lovga kirish huquqiga ega emassiz."

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsCardOwner(BasePermission):
    """Faqat karta egasi murojaat qila oladi."""

    message = "Siz bu kartaga kirish huquqiga ega emassiz."

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsWalletOwner(BasePermission):
    """Faqat hamyon egasi ko'ra/boshqara oladi."""

    message = "Siz bu hamyonga kirish huquqiga ega emassiz."

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsAdminOrReadOnly(BasePermission):
    """Admin — yozish, boshqalar — faqat o'qish."""

    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return request.user and request.user.is_staff


class CanInitiateRefund(BasePermission):
    """Faqat admin yoki to'lov egasi qaytarish boshlashi mumkin."""

    message = "Qaytarishni boshlash uchun ruxsat yo'q."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # obj = Payment
        return obj.user == request.user or request.user.is_staff
