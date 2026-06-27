
from dataclasses import dataclass
from apps.payments.exceptions.base import SignatureError

@dataclass
class ProviderIntent:
    provider_transaction_id:str|None
    checkout_url:str|None=None
    invoice_id:str|None=None
    raw:dict|None=None

class BaseProvider:
    code=None
    def create_intent(self, transaction): raise NotImplementedError
    def verify_callback(self, raw_payload, headers): raise NotImplementedError
    def check_status(self, provider_transaction_id): raise NotImplementedError
    def refund(self, provider_transaction_id, amount): raise NotImplementedError
