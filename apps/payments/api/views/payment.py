
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.orders.models import Order
from apps.payments.api.serializers.payment import *
from apps.payments.services.payment_service import PaymentService
from apps.payments.services.refund_service import RefundService
from apps.payments.selectors.payment_selectors import get_transaction_for_user, get_latest_order_transaction
from apps.payments.models import PaymentTransaction

class PaymentIntentCreateApi(APIView):
    permission_classes=[IsAuthenticated]
    def post(self, request):
        s=PaymentIntentSerializer(data=request.data); s.is_valid(raise_exception=True)
        order=Order.objects.get(id=s.validated_data["order_id"], customer=request.user)
        tx=PaymentService.create_intent(order, s.validated_data["provider"], s.validated_data["idempotency_key"])
        return Response(PaymentTransactionSerializer(tx).data)

class PaymentTransactionDetailApi(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request, public_id):
        tx=get_transaction_for_user(public_id, request.user)
        return Response(PaymentTransactionSerializer(tx).data)

class OrderLatestTransactionApi(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request, order_id):
        tx=get_latest_order_transaction(order_id)
        return Response(PaymentTransactionSerializer(tx).data if tx else None)
