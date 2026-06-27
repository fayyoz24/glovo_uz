
import base64
from django.conf import settings
from .base import BaseProvider, ProviderIntent
from apps.payments.exceptions.base import SignatureError
class PaymeProvider(BaseProvider):
    code="payme"
    def create_intent(self, transaction):
        return ProviderIntent(provider_transaction_id=str(transaction.id), invoice_id=str(transaction.id), raw={"invoice_id":str(transaction.id)})
    def verify_callback(self, raw_payload, headers):
        auth=headers.get("Authorization","")
        if not auth.startswith("Basic "): raise SignatureError("Missing basic auth")
        return raw_payload
    def check_status(self, provider_transaction_id): return {"state":"pending","provider_transaction_id":provider_transaction_id}
    def refund(self, provider_transaction_id, amount): return {"state":"refund_pending"}
