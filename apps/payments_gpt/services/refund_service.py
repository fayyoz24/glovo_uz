
from django.db.models import Sum
from apps.payments.models import Refund
from apps.payments.constants.enums import PaymentStatus, RefundStatus
from apps.payments.services.payment_service import PROVIDERS
from apps.payments.exceptions.base import PaymentError
class RefundService:
    @classmethod
    def create_refund(cls, transaction, amount, reason, initiated_by=None):
        refunded=transaction.refunds.filter(status=RefundStatus.REFUNDED).aggregate(s=Sum("amount"))["s"] or 0
        if refunded + amount > transaction.amount: raise PaymentError("Refund exceeds paid amount")
        refund=Refund.objects.create(order=transaction.order,transaction=transaction,amount=amount,currency=transaction.currency,reason=reason,initiated_by=initiated_by)
        res=PROVIDERS[transaction.provider].refund(transaction.provider_transaction_id, amount)
        refund.raw_response=res; refund.status=RefundStatus.REFUNDED; refund.save(update_fields=["raw_response","status","updated_at"])
        transaction.status=PaymentStatus.REFUNDED if refunded+amount==transaction.amount else PaymentStatus.PARTIALLY_REFUNDED
        transaction.save(update_fields=["status","updated_at"])
        return refund
