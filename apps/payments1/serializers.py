from decimal import Decimal
from rest_framework import serializers

from .models import Wallet, SavedCard, Payment, Refund, WalletTransaction, PaymentSession
from .constants import PaymentMethod, TransactionType


# ─── Wallet ───────────────────────────────────────────────────────────────────

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ["id", "balance", "is_active", "updated_at"]
        read_only_fields = fields


class WalletTopUpSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("1000"))
    reference_id = serializers.CharField(max_length=100, required=False, allow_blank=True)


class WalletWithdrawSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("10000"))


# ─── SavedCard ────────────────────────────────────────────────────────────────

class SavedCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedCard
        fields = [
            "id", "card_type", "masked_number",
            "expire_month", "expire_year",
            "is_default", "is_verified", "gateway",
            "created_at",
        ]
        read_only_fields = fields


class AddCardSerializer(serializers.Serializer):
    card_number = serializers.CharField(
        min_length=16, max_length=19,
        help_text="16 xonali karta raqami (probelsiz yoki probel bilan)"
    )
    expire_month = serializers.IntegerField(min_value=1, max_value=12)
    expire_year = serializers.IntegerField(min_value=2024, max_value=2040)
    gateway = serializers.ChoiceField(choices=[
        PaymentMethod.PAYME, PaymentMethod.CLICK, PaymentMethod.UPAY
    ])
    token = serializers.CharField(max_length=255, help_text="Gateway tokenizatsiya natijasi")
    is_default = serializers.BooleanField(default=False)


class SetDefaultCardSerializer(serializers.Serializer):
    card_id = serializers.UUIDField()


# ─── Payment ──────────────────────────────────────────────────────────────────

class PaymentSerializer(serializers.ModelSerializer):
    method_display = serializers.CharField(source="get_method_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    order_id = serializers.UUIDField(source="order.id", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id", "order_id", "method", "method_display",
            "status", "status_display", "amount", "currency",
            "gateway_transaction_id",
            "paid_at", "failed_at", "failure_reason",
            "ip_address", "created_at", "updated_at",
        ]
        read_only_fields = fields


class PaymentDetailSerializer(PaymentSerializer):
    saved_card = SavedCardSerializer(read_only=True)
    gateway_response = serializers.JSONField(read_only=True)
    is_refundable = serializers.BooleanField(read_only=True)

    class Meta(PaymentSerializer.Meta):
        fields = PaymentSerializer.Meta.fields + [
            "saved_card", "gateway_response", "is_refundable"
        ]


class CreatePaymentSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    method = serializers.ChoiceField(choices=PaymentMethod.choices)
    card_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="Saqlangan karta ID (faqat karta orqali to'lovda)"
    )

    def validate(self, attrs):
        method = attrs.get("method")
        card_id = attrs.get("card_id")
        if method in (PaymentMethod.PAYME, PaymentMethod.CLICK, PaymentMethod.UPAY) and not card_id:
            # card_id optional — gateway redirect bo'lishi ham mumkin
            pass
        return attrs


class PaymentFilterSerializer(serializers.Serializer):
    status = serializers.CharField(required=False)
    method = serializers.CharField(required=False)
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)


# ─── Refund ───────────────────────────────────────────────────────────────────

class RefundSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Refund
        fields = [
            "id", "payment_id", "amount", "reason",
            "status", "status_display",
            "gateway_refund_id", "created_at", "updated_at",
        ]
        read_only_fields = fields


class CreateRefundSerializer(serializers.Serializer):
    payment_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("100"))
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)


# ─── WalletTransaction ────────────────────────────────────────────────────────

class WalletTransactionSerializer(serializers.ModelSerializer):
    transaction_type_display = serializers.CharField(
        source="get_transaction_type_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = WalletTransaction
        fields = [
            "id", "transaction_type", "transaction_type_display",
            "amount", "balance_before", "balance_after",
            "status", "status_display",
            "description", "reference_id", "created_at",
        ]
        read_only_fields = fields


class WalletTransactionFilterSerializer(serializers.Serializer):
    transaction_type = serializers.ChoiceField(choices=TransactionType.choices, required=False)
    status = serializers.CharField(required=False)


# ─── PaymentSession ───────────────────────────────────────────────────────────

class PaymentSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentSession
        fields = ["id", "session_token", "redirect_url", "expires_at", "is_used", "created_at"]
        read_only_fields = fields


# ─── Gateway Webhooks ─────────────────────────────────────────────────────────

class PaymeWebhookSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    method = serializers.CharField()
    params = serializers.DictField(required=False)


class ClickWebhookSerializer(serializers.Serializer):
    click_trans_id = serializers.IntegerField()
    service_id = serializers.IntegerField()
    click_paydoc_id = serializers.IntegerField(required=False)
    merchant_trans_id = serializers.CharField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    action = serializers.IntegerField()
    error = serializers.IntegerField(default=0)
    error_note = serializers.CharField(required=False)
    sign_time = serializers.CharField(required=False)
    sign_string = serializers.CharField(required=False)
    payment_id = serializers.IntegerField(required=False)
