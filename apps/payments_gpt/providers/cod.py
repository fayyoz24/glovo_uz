
from .base import BaseProvider, ProviderIntent
class CODProvider(BaseProvider):
    code="cod"
    def create_intent(self, transaction): return ProviderIntent(None, raw={"status":"pending_cod"})
    def verify_callback(self, raw_payload, headers): return raw_payload
    def check_status(self, provider_transaction_id): return {"status":"pending_cod"}
    def refund(self, provider_transaction_id, amount): return {"status":"manual"}
