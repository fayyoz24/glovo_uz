
from django.db import transaction
from django.utils import timezone
from apps.payments.models import PaymentTransaction, WebhookEvent
from apps.payments.constants.enums import PaymentProvider, PaymentStatus
from apps.payments.providers.click import ClickProvider
from apps.payments.providers.payme import PaymeProvider
from apps.payments.providers.cod import CODProvider
from apps.payments.exceptions.base import PaymentError

PROVIDERS={PaymentProvider.CLICK:ClickProvider(),PaymentProvider.PAYME:PaymeProvider(),PaymentProvider.COD:CODProvider()}

class PaymentService:
    @classmethod
    def create_intent(cls, order, provider, idempotency_key):
        tx=PaymentTransaction.objects.filter(order=order,idempotency_key=idempotency_key).first()
        if tx: return tx
        tx=PaymentTransaction.objects.create(order=order,provider=provider,method=provider,amount=order.total_amount,currency=order.currency,idempotency_key=idempotency_key,status=PaymentStatus.CREATED)
        intent=PROVIDERS[provider].create_intent(tx)
        tx.provider_transaction_id=intent.provider_transaction_id
        tx.status=PaymentStatus.PENDING_COD if provider==PaymentProvider.COD else PaymentStatus.PENDING
        tx.initiated_at=timezone.now()
        tx.raw_response=intent.raw or {}
        tx.save(update_fields=["provider_transaction_id","status","initiated_at","raw_response","updated_at"])
        return tx
    @classmethod
    @transaction.atomic
    def mark_paid(cls, transaction_obj):
        tx=PaymentTransaction.objects.select_for_update().get(pk=transaction_obj.pk)
        if tx.status==PaymentStatus.PAID: return tx
        if tx.status not in [PaymentStatus.PENDING, PaymentStatus.PENDING_COD, PaymentStatus.CREATED]:
            raise PaymentError("Invalid transition to paid")
        tx.status=PaymentStatus.PAID; tx.paid_at=timezone.now(); tx.save(update_fields=["status","paid_at","updated_at"])
        return tx
