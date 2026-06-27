
from rest_framework import serializers
from apps.payments.models import PaymentTransaction, Refund
class PaymentIntentSerializer(serializers.Serializer):
    order_id=serializers.UUIDField()
    provider=serializers.CharField()
    idempotency_key=serializers.CharField()
class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta: model=PaymentTransaction; fields="__all__"
class RefundCreateSerializer(serializers.Serializer):
    transaction_id=serializers.UUIDField()
    amount=serializers.DecimalField(max_digits=12, decimal_places=2)
    reason=serializers.CharField()
class RefundSerializer(serializers.ModelSerializer):
    class Meta: model=Refund; fields="__all__"
