
from apps.payments.models import PaymentTransaction, Refund

def get_transaction_for_user(public_id, user):
    return PaymentTransaction.objects.select_related("order").get(public_id=public_id, order__customer=user)

def get_latest_order_transaction(order_id):
    return PaymentTransaction.objects.filter(order_id=order_id).order_by("-created_at").first()

def admin_list_transactions(filters):
    qs=PaymentTransaction.objects.select_related("order","order__customer").all().order_by("-created_at")
    if status:=filters.get("status"): qs=qs.filter(status=status)
    if provider:=filters.get("provider"): qs=qs.filter(provider=provider)
    return qs

def get_refund(refund_id): return Refund.objects.select_related("transaction","order").get(id=refund_id)
