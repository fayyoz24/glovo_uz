
from django.db import models

class PaymentProvider(models.TextChoices):
    CLICK="click","Click"
    PAYME="payme","Payme"
    COD="cod","Cash on delivery"

class PaymentStatus(models.TextChoices):
    CREATED="created","Created"
    PENDING="pending","Pending"
    PENDING_COD="pending_cod","Pending COD"
    PAID="paid","Paid"
    FAILED="failed","Failed"
    CANCELLED="cancelled","Cancelled"
    REFUND_PENDING="refund_pending","Refund pending"
    REFUNDED="refunded","Refunded"
    PARTIALLY_REFUNDED="partially_refunded","Partially refunded"

class RefundStatus(models.TextChoices):
    PENDING="pending","Pending"
    REFUNDED="refunded","Refunded"
    FAILED="failed","Failed"
