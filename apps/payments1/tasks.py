import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_refund_task(self, refund_id: str):
    """
    Qaytarishni gateway orqali async qayta ishlash.
    """
    from .models import Refund
    from .services import complete_refund
    from .constants import PaymentMethod, PaymentStatus

    try:
        refund = Refund.objects.select_related("payment").get(id=refund_id)
    except Refund.DoesNotExist:
        logger.error("Refund not found: %s", refund_id)
        return

    if refund.status == PaymentStatus.COMPLETED:
        logger.info("Refund already completed: %s", refund_id)
        return

    payment = refund.payment
    method = payment.method

    try:
        # Gateway'ga qaytarish so'rovi
        gateway_refund_id = None

        if method == PaymentMethod.PAYME:
            gateway_refund_id = _payme_refund(payment, refund)
        elif method == PaymentMethod.CLICK:
            gateway_refund_id = _click_refund(payment, refund)
        elif method == PaymentMethod.UPAY:
            gateway_refund_id = _upay_refund(payment, refund)
        elif method in (PaymentMethod.WALLET, PaymentMethod.CASH):
            # Wallet/cash — to'g'ridan-to'g'ri
            gateway_refund_id = f"internal_{refund_id}"

        if gateway_refund_id:
            complete_refund(refund, gateway_refund_id=gateway_refund_id)
            logger.info("Refund processed: refund=%s gateway=%s", refund_id, gateway_refund_id)
        else:
            logger.warning("Refund gateway_refund_id is empty: %s", refund_id)

    except Exception as exc:
        logger.exception("Refund task failed: refund=%s error=%s", refund_id, exc)
        self.retry(exc=exc)


def _payme_refund(payment, refund) -> str:
    """Payme orqali qaytarish (stub — real API call kerak)."""
    import uuid
    # TODO: Payme API CancelTransaction call
    return f"payme_refund_{uuid.uuid4().hex[:8]}"


def _click_refund(payment, refund) -> str:
    """Click orqali qaytarish (stub)."""
    import uuid
    # TODO: Click refund API call
    return f"click_refund_{uuid.uuid4().hex[:8]}"


def _upay_refund(payment, refund) -> str:
    """UPAY orqali qaytarish (stub)."""
    import uuid
    # TODO: UPAY refund API call
    return f"upay_refund_{uuid.uuid4().hex[:8]}"


@shared_task
def auto_cancel_expired_payments():
    """
    Muddati o'tgan PENDING to'lovlarni avtomatik bekor qilish.
    Har 15 daqiqada ishga tushadi (Celery Beat orqali).
    """
    from .selectors import get_pending_payments_older_than
    from .services import mark_payment_failed
    from .constants import PAYMENT_SESSION_EXPIRY_MINUTES

    expired_payments = get_pending_payments_older_than(PAYMENT_SESSION_EXPIRY_MINUTES)
    count = 0

    for payment in expired_payments:
        mark_payment_failed(
            payment,
            reason="Sessiya muddati tugadi (auto-cancel).",
        )
        count += 1

    logger.info("Auto-cancelled %d expired payments", count)
    return count


@shared_task
def send_payment_receipt_task(payment_id: str):
    """
    To'lov kvitansiyasini foydalanuvchiga yuborish (email/SMS).
    """
    from .models import Payment
    from .constants import PaymentStatus

    try:
        payment = Payment.objects.select_related("user", "order").get(id=payment_id)
    except Payment.DoesNotExist:
        logger.error("Payment not found for receipt: %s", payment_id)
        return

    if payment.status != PaymentStatus.COMPLETED:
        return

    # TODO: Email/SMS notification service integratsiyasi
    logger.info(
        "Payment receipt queued: payment=%s user=%s",
        payment_id, payment.user_id
    )


@shared_task
def sync_gateway_payment_status(payment_id: str):
    """
    Gateway'dan to'lov statusini sinxronlash (PROCESSING holatidagilar uchun).
    """
    from .models import Payment
    from .constants import PaymentStatus, PaymentMethod

    try:
        payment = Payment.objects.get(id=payment_id)
    except Payment.DoesNotExist:
        return

    if payment.status != PaymentStatus.PROCESSING:
        return

    # TODO: gateway'ga so'rov yuborish va statusni yangilash
    logger.info(
        "Gateway sync triggered: payment=%s method=%s",
        payment_id, payment.method
    )


@shared_task
def cleanup_expired_payment_sessions():
    """
    Muddati o'tgan va ishlatilmagan sessiyalarni tozalash.
    Kuniga bir marta ishga tushadi.
    """
    from .models import PaymentSession

    deleted_count, _ = PaymentSession.objects.filter(
        expires_at__lt=timezone.now(),
        is_used=False,
    ).delete()

    logger.info("Deleted %d expired payment sessions", deleted_count)
    return deleted_count
