
import uuid
from django.conf import settings
from django.db import models
from apps.payments.constants.enums import PaymentProvider, PaymentStatus, RefundStatus

class PaymentTransaction(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    public_id=models.UUIDField(default=uuid.uuid4,editable=False,db_index=True)
    order=models.ForeignKey("orders.Order",on_delete=models.PROTECT,related_name="payment_transactions")
    provider=models.CharField(max_length=20,choices=PaymentProvider.choices)
    provider_transaction_id=models.CharField(max_length=128,blank=True,null=True)
    method=models.CharField(max_length=32)
    amount=models.DecimalField(max_digits=12,decimal_places=2)
    currency=models.CharField(max_length=8,default="UZS")
    status=models.CharField(max_length=32,choices=PaymentStatus.choices,default=PaymentStatus.CREATED)
    idempotency_key=models.CharField(max_length=128,db_index=True)
    attempt_count=models.PositiveIntegerField(default=0)
    raw_request=models.JSONField(default=dict,blank=True)
    raw_response=models.JSONField(default=dict,blank=True)
    failure_reason=models.TextField(blank=True)
    initiated_at=models.DateTimeField(null=True,blank=True)
    paid_at=models.DateTimeField(null=True,blank=True)
    failed_at=models.DateTimeField(null=True,blank=True)
    expires_at=models.DateTimeField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        indexes=[models.Index(fields=["order","status"]),models.Index(fields=["provider","provider_transaction_id"])]
        constraints=[models.UniqueConstraint(fields=["provider","provider_transaction_id"],name="uniq_provider_txid",condition=models.Q(provider_transaction_id__isnull=False))]
    def __str__(self): return f"{self.provider}:{self.public_id}:{self.status}"

class PaymentMethodRecord(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="payment_methods")
    provider=models.CharField(max_length=20,choices=PaymentProvider.choices)
    masked_identifier=models.CharField(max_length=64)
    is_default=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)

class Refund(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    order=models.ForeignKey("orders.Order",on_delete=models.PROTECT,related_name="refunds")
    transaction=models.ForeignKey(PaymentTransaction,on_delete=models.PROTECT,related_name="refunds")
    amount=models.DecimalField(max_digits=12,decimal_places=2)
    currency=models.CharField(max_length=8,default="UZS")
    reason=models.TextField()
    status=models.CharField(max_length=20,choices=RefundStatus.choices,default=RefundStatus.PENDING)
    initiated_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True)
    provider_refund_id=models.CharField(max_length=128,blank=True,null=True)
    raw_response=models.JSONField(default=dict,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

class WebhookEvent(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    provider=models.CharField(max_length=20,choices=PaymentProvider.choices)
    event_type=models.CharField(max_length=64)
    provider_transaction_id=models.CharField(max_length=128,blank=True,null=True)
    payload=models.JSONField(default=dict)
    signature_valid=models.BooleanField(default=False)
    processed=models.BooleanField(default=False)
    processed_at=models.DateTimeField(null=True,blank=True)
    received_at=models.DateTimeField(auto_now_add=True)
