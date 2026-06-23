from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.accounts.models import User, CustomerProfile, CourierProfile, MerchantStaffProfile, OTPCode, DeviceToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["phone", "full_name", "role", "is_verified", "is_active", "created_at"]
    list_filter = ["role", "is_active", "is_verified"]
    search_fields = ["phone", "full_name", "email"]
    ordering = ["-created_at"]
    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("Personal info", {"fields": ("full_name", "email", "language")}),
        ("Permissions", {"fields": ("role", "is_active", "is_verified", "is_staff", "is_superuser")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("phone", "password1", "password2", "role")}),
    )


@admin.register(CourierProfile)
class CourierProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "vehicle_type", "is_online", "is_available", "is_approved", "rating"]
    list_filter = ["vehicle_type", "is_online", "is_approved"]


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ["phone", "code", "is_used", "attempts", "created_at", "expires_at"]
    list_filter = ["is_used"]


admin.site.register(CustomerProfile)
admin.site.register(MerchantStaffProfile)
admin.site.register(DeviceToken)
