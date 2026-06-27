from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from .models import Wallet, SavedCard, Payment, Refund, WalletTransaction, PaymentSession
from .constants import PaymentStatus


# ─── Inline ───────────────────────────────────────────────────────────────────

class WalletTransactionInline(admin.TabularInline):
    model = WalletTransaction
    extra = 0
    readonly_fields = [
        "transaction_type", "amount", "balance_before",
        "balance_after", "status", "description", "created_at",
    ]
    can_delete = False
    ordering = ["-created_at"]
    max_num = 20


class RefundInline(admin.TabularInline):
    model = Refund
    extra = 0
    readonly_fields = [
        "amount", "reason", "status", "gateway_refund_id", "created_at"
    ]
    can_delete = False


# ─── Wallet ───────────────────────────────────────────────────────────────────

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "balance_display", "is_active", "updated_at"]
    list_filter = ["is_active"]
    search_fields = ["user__phone", "user__email"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [WalletTransactionInline]

    def balance_display(self, obj):
        return f"{obj.balance:,.0f} UZS"
    balance_display.short_description = "Balans"


# ─── SavedCard ────────────────────────────────────────────────────────────────

@admin.register(SavedCard)
class SavedCardAdmin(admin.ModelAdmin):
    list_display = [
        "id", "user", "card_type", "masked_number",
        "is_default", "is_verified", "gateway", "created_at"
    ]
    list_filter = ["card_type", "gateway", "is_default", "is_verified"]
    search_fields = ["user__phone", "masked_number"]
    readonly_fields = ["id", "token", "created_at"]


# ─── Payment ──────────────────────────────────────────────────────────────────

class PaymentStatusFilter(admin.SimpleListFilter):
    title = "Status"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return PaymentStatus.choices

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "id", "user", "order_link", "method", "status_badge",
        "amount_display", "paid_at", "created_at"
    ]
    list_filter = ["method", PaymentStatusFilter]
    search_fields = [
        "id", "user__phone", "gateway_transaction_id",
        "order__id",
    ]
    readonly_fields = [
        "id", "order", "user", "method", "amount", "currency",
        "gateway_transaction_id", "gateway_order_id", "gateway_response",
        "paid_at", "failed_at", "failure_reason", "ip_address",
        "created_at", "updated_at",
    ]
    inlines = [RefundInline]

    def order_link(self, obj):
        return format_html(
            '<a href="/admin/orders/order/{}/change/">{}</a>',
            obj.order_id, obj.order_id
        )
    order_link.short_description = "Buyurtma"

    def status_badge(self, obj):
        colors = {
            PaymentStatus.PENDING: "#f59e0b",
            PaymentStatus.PROCESSING: "#3b82f6",
            PaymentStatus.COMPLETED: "#10b981",
            PaymentStatus.FAILED: "#ef4444",
            PaymentStatus.REFUNDED: "#8b5cf6",
            PaymentStatus.PARTIALLY_REFUNDED: "#f97316",
            PaymentStatus.CANCELLED: "#6b7280",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:12px">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def amount_display(self, obj):
        return f"{obj.amount:,.0f} {obj.currency}"
    amount_display.short_description = "Summa"

    actions = ["mark_failed", "mark_cancelled"]

    def mark_failed(self, request, queryset):
        from .services import mark_payment_failed
        count = 0
        for p in queryset.filter(status=PaymentStatus.PENDING):
            mark_payment_failed(p, reason="Admin tomonidan muvaffaqiyatsiz deb belgilandi.")
            count += 1
        self.message_user(request, f"{count} ta to'lov muvaffaqiyatsiz deb belgilandi.")
    mark_failed.short_description = "Tanlangan to'lovlarni muvaffaqiyatsiz deb belgilash"

    def mark_cancelled(self, request, queryset):
        from .services import cancel_payment
        count = 0
        for p in queryset:
            try:
                cancel_payment(p)
                count += 1
            except Exception:
                pass
        self.message_user(request, f"{count} ta to'lov bekor qilindi.")
    mark_cancelled.short_description = "Tanlangan to'lovlarni bekor qilish"


# ─── Refund ───────────────────────────────────────────────────────────────────

@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = [
        "id", "payment_link", "amount_display", "status",
        "gateway_refund_id", "created_at"
    ]
    list_filter = ["status"]
    search_fields = ["id", "payment__id", "gateway_refund_id"]
    readonly_fields = [
        "id", "payment", "initiated_by", "amount", "reason",
        "status", "gateway_refund_id", "gateway_response",
        "created_at", "updated_at",
    ]

    def payment_link(self, obj):
        return format_html(
            '<a href="/admin/payments/payment/{}/change/">{}</a>',
            obj.payment_id, obj.payment_id
        )
    payment_link.short_description = "To'lov"

    def amount_display(self, obj):
        return f"{obj.amount:,.0f} UZS"
    amount_display.short_description = "Summa"


# ─── WalletTransaction ────────────────────────────────────────────────────────

@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "id", "wallet_user", "transaction_type", "amount_display",
        "balance_before", "balance_after", "status", "created_at"
    ]
    list_filter = ["transaction_type", "status"]
    search_fields = ["wallet__user__phone", "reference_id", "description"]
    readonly_fields = [f.name for f in WalletTransaction._meta.fields]

    def wallet_user(self, obj):
        return obj.wallet.user
    wallet_user.short_description = "Foydalanuvchi"

    def amount_display(self, obj):
        return f"{obj.amount:,.0f} UZS"
    amount_display.short_description = "Summa"


# ─── PaymentSession ───────────────────────────────────────────────────────────

@admin.register(PaymentSession)
class PaymentSessionAdmin(admin.ModelAdmin):
    list_display = [
        "id", "payment", "is_used", "expires_at", "is_expired_display", "created_at"
    ]
    list_filter = ["is_used"]
    readonly_fields = [f.name for f in PaymentSession._meta.fields]

    def is_expired_display(self, obj):
        if obj.is_expired:
            return format_html('<span style="color:red">Ha</span>')
        return format_html('<span style="color:green">Yo\'q</span>')
    is_expired_display.short_description = "Muddati o'tganmi"
