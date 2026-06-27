
import hashlib
from django.conf import settings
from .base import BaseProvider, ProviderIntent
from apps.payments.exceptions.base import SignatureError
class ClickProvider(BaseProvider):
    code="click"
    def create_intent(self, transaction):
        txid=str(transaction.id)
        url=f"{settings.CLICK_CHECKOUT_URL}?merchant_trans_id={transaction.order_id}&amount={transaction.amount}&merchant_prepare_id={txid}"
        return ProviderIntent(provider_transaction_id=txid, checkout_url=url, raw={"checkout_url":url})
    def verify_callback(self, raw_payload, headers):
        sign_string=raw_payload.get("sign_string","")
        expected=hashlib.md5(f"{raw_payload.get('click_trans_id','')}{settings.CLICK_SERVICE_ID}{settings.CLICK_SECRET_KEY}".encode()).hexdigest()
        if sign_string != expected: raise SignatureError("Invalid Click signature")
        return raw_payload
    def check_status(self, provider_transaction_id): return {"provider_transaction_id":provider_transaction_id}
    def refund(self, provider_transaction_id, amount): return {"status":"requested"}
