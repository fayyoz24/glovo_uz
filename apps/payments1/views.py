import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from .models import Payment, SavedCard, Refund
from .serializers import (
    WalletSerializer,
    WalletTopUpSerializer,
    WalletWithdrawSerializer,
    WalletTransactionSerializer,
    WalletTransactionFilterSerializer,
    SavedCardSerializer,
    AddCardSerializer,
    SetDefaultCardSerializer,
    PaymentSerializer,
    PaymentDetailSerializer,
    CreatePaymentSerializer,
    PaymentFilterSerializer,
    RefundSerializer,
    CreateRefundSerializer,
    PaymeWebhookSerializer,
    ClickWebhookSerializer,
    PaymentSessionSerializer,
)
from .permissions import IsPaymentOwner, IsCardOwner, IsWalletOwner, CanInitiateRefund
from .selectors import (
    get_wallet_by_user,
    get_saved_cards,
    get_saved_card_by_id,
    get_payment_by_id,
    get_user_payments,
    get_refunds_by_payment,
    get_wallet_transactions,
    get_all_payments,
)
from .services import (
    top_up_wallet,
    withdraw_from_wallet,
    add_saved_card,
    remove_saved_card,
    set_default_card,
    create_payment,
    route_payment_to_gateway,
    initiate_refund,
    handle_payme_webhook,
    handle_click_webhook,
)
from .exceptions import (
    PaymentNotFound,
    CardNotFound,
)

logger = logging.getLogger(__name__)


# ─── Wallet ───────────────────────────────────────────────────────────────────

class WalletDetailView(APIView):
    """GET /payments/wallet/ — hamyon balansini ko'rish."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet = get_wallet_by_user(request.user)
        serializer = WalletSerializer(wallet)
        return Response(serializer.data)


class WalletTopUpView(APIView):
    """POST /payments/wallet/top-up/ — hamyonga pul qo'shish."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WalletTopUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        wallet = get_wallet_by_user(request.user)
        txn = top_up_wallet(
            wallet=wallet,
            amount=serializer.validated_data["amount"],
            reference_id=serializer.validated_data.get("reference_id", ""),
        )
        return Response(
            WalletTransactionSerializer(txn).data,
            status=status.HTTP_201_CREATED,
        )


class WalletWithdrawView(APIView):
    """POST /payments/wallet/withdraw/ — hamyondan pul yechish."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WalletWithdrawSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        wallet = get_wallet_by_user(request.user)
        txn = withdraw_from_wallet(
            wallet=wallet,
            amount=serializer.validated_data["amount"],
        )
        return Response(WalletTransactionSerializer(txn).data)


class WalletTransactionListView(ListAPIView):
    """GET /payments/wallet/transactions/ — hamyon tarixi."""
    permission_classes = [IsAuthenticated]
    serializer_class = WalletTransactionSerializer

    def get_queryset(self):
        wallet = get_wallet_by_user(self.request.user)
        filter_serializer = WalletTransactionFilterSerializer(data=self.request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        return get_wallet_transactions(wallet, filters=filter_serializer.validated_data)


# ─── Saved Cards ──────────────────────────────────────────────────────────────

class SavedCardListView(ListAPIView):
    """GET /payments/cards/ — saqlangan kartalar ro'yxati."""
    permission_classes = [IsAuthenticated]
    serializer_class = SavedCardSerializer

    def get_queryset(self):
        return get_saved_cards(self.request.user)


class SavedCardAddView(APIView):
    """POST /payments/cards/ — yangi karta qo'shish."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddCardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        card = add_saved_card(
            user=request.user,
            card_number=serializer.validated_data["card_number"],
            expire_month=serializer.validated_data["expire_month"],
            expire_year=serializer.validated_data["expire_year"],
            gateway=serializer.validated_data["gateway"],
            token=serializer.validated_data["token"],
            is_default=serializer.validated_data.get("is_default", False),
        )
        return Response(SavedCardSerializer(card).data, status=status.HTTP_201_CREATED)


class SavedCardDetailView(APIView):
    """GET/DELETE /payments/cards/<id>/"""
    permission_classes = [IsAuthenticated, IsCardOwner]

    def get_object(self, card_id):
        card = get_saved_card_by_id(card_id, self.request.user)
        if not card:
            raise CardNotFound()
        self.check_object_permissions(self.request, card)
        return card

    def get(self, request, card_id):
        card = self.get_object(card_id)
        return Response(SavedCardSerializer(card).data)

    def delete(self, request, card_id):
        card = self.get_object(card_id)
        remove_saved_card(card)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SetDefaultCardView(APIView):
    """POST /payments/cards/set-default/ — default kartani o'rnatish."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SetDefaultCardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        card = get_saved_card_by_id(serializer.validated_data["card_id"], request.user)
        if not card:
            raise CardNotFound()

        card = set_default_card(request.user, card)
        return Response(SavedCardSerializer(card).data)


# ─── Payments ─────────────────────────────────────────────────────────────────

class PaymentListView(ListAPIView):
    """GET /payments/ — foydalanuvchining to'lovlari."""
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_queryset(self):
        filter_serializer = PaymentFilterSerializer(data=self.request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        return get_user_payments(self.request.user, filters=filter_serializer.validated_data)


class PaymentDetailView(RetrieveAPIView):
    """GET /payments/<id>/ — to'lov tafsilotlari."""
    permission_classes = [IsAuthenticated, IsPaymentOwner]
    serializer_class = PaymentDetailSerializer

    def get_object(self):
        payment = get_payment_by_id(self.kwargs["payment_id"])
        if not payment:
            raise PaymentNotFound()
        self.check_object_permissions(self.request, payment)
        return payment


class CreatePaymentView(APIView):
    """POST /payments/create/ — yangi to'lov yaratish."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Order'ni olish
        from orders.selectors import get_order_by_id
        from orders.exceptions import OrderNotFound
        order = get_order_by_id(serializer.validated_data["order_id"])
        if not order:
            raise OrderNotFound()

        # Karta (ixtiyoriy)
        saved_card = None
        if card_id := serializer.validated_data.get("card_id"):
            saved_card = get_saved_card_by_id(card_id, request.user)
            if not saved_card:
                raise CardNotFound()

        # To'lov yaratish
        payment = create_payment(
            order=order,
            user=request.user,
            method=serializer.validated_data["method"],
            amount=order.total_price,
            saved_card=saved_card,
            ip_address=request.META.get("REMOTE_ADDR"),
        )

        # Gateway'ga yo'naltirish
        gateway_data = route_payment_to_gateway(payment)

        return Response(
            {
                "payment": PaymentSerializer(payment).data,
                "gateway": gateway_data,
            },
            status=status.HTTP_201_CREATED,
        )


# ─── Refunds ──────────────────────────────────────────────────────────────────

class RefundListView(ListAPIView):
    """GET /payments/<payment_id>/refunds/ — to'lov qaytarishlari."""
    permission_classes = [IsAuthenticated]
    serializer_class = RefundSerializer

    def get_queryset(self):
        payment = get_payment_by_id(self.kwargs["payment_id"])
        if not payment or payment.user != self.request.user:
            raise PaymentNotFound()
        return get_refunds_by_payment(payment)


class CreateRefundView(APIView):
    """POST /payments/refunds/ — qaytarish boshlash."""
    permission_classes = [IsAuthenticated, CanInitiateRefund]

    def post(self, request):
        serializer = CreateRefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = get_payment_by_id(serializer.validated_data["payment_id"])
        if not payment:
            raise PaymentNotFound()

        self.check_object_permissions(request, payment)

        refund = initiate_refund(
            payment=payment,
            amount=serializer.validated_data["amount"],
            reason=serializer.validated_data.get("reason", ""),
            initiated_by=request.user,
        )

        # Async qaytarish (task orqali)
        from .tasks import process_refund_task
        process_refund_task.delay(str(refund.id))

        return Response(RefundSerializer(refund).data, status=status.HTTP_201_CREATED)


# ─── Admin Views ──────────────────────────────────────────────────────────────

class AdminPaymentListView(ListAPIView):
    """GET /admin/payments/ — barcha to'lovlar (admin)."""
    permission_classes = [IsAdminUser]
    serializer_class = PaymentDetailSerializer

    def get_queryset(self):
        filter_serializer = PaymentFilterSerializer(data=self.request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        return get_all_payments(filters=filter_serializer.validated_data)


# ─── Webhook Views ────────────────────────────────────────────────────────────

class PaymeWebhookView(APIView):
    """POST /payments/webhooks/payme/ — Payme callback."""
    permission_classes = []  # IP whitelist middleware bilan himoyalanadi
    authentication_classes = []

    def post(self, request):
        serializer = PaymeWebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = handle_payme_webhook(request.data)
        return Response({"jsonrpc": "2.0", "id": request.data.get("id"), **result})


class ClickWebhookView(APIView):
    """POST /payments/webhooks/click/ — Click callback."""
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        serializer = ClickWebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = handle_click_webhook(request.data)
        return Response(result)


class UPayWebhookView(APIView):
    """POST /payments/webhooks/upay/ — UPAY (UzCard/Humo) callback."""
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        txn_id = request.data.get("transaction_id")
        order_id = request.data.get("merchant_order_id")
        status_code = request.data.get("status")  # "success" | "failed"

        payment = Payment.objects.filter(order__id=order_id).first()
        if not payment:
            return Response({"error": "Payment not found"}, status=404)

        if status_code == "success":
            from .services import mark_payment_completed
            mark_payment_completed(payment, gateway_txn_id=str(txn_id), gateway_response=request.data)
        else:
            from .services import mark_payment_failed
            mark_payment_failed(payment, reason="UPAY: to'lov rad etildi.", gateway_response=request.data)

        return Response({"status": "ok"})
