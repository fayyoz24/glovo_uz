from django.urls import path

from .views import (
    # Wallet
    WalletDetailView,
    WalletTopUpView,
    WalletWithdrawView,
    WalletTransactionListView,

    # Cards
    SavedCardListView,
    SavedCardAddView,
    SavedCardDetailView,
    SetDefaultCardView,

    # Payments
    PaymentListView,
    PaymentDetailView,
    CreatePaymentView,

    # Refunds
    RefundListView,
    CreateRefundView,

    # Admin
    AdminPaymentListView,

    # Webhooks
    PaymeWebhookView,
    ClickWebhookView,
    UPayWebhookView,
)

app_name = "payments"

urlpatterns = [
    # ─── Wallet ───────────────────────────────────────────────────────────────
    path("wallet/", WalletDetailView.as_view(), name="wallet-detail"),
    path("wallet/top-up/", WalletTopUpView.as_view(), name="wallet-top-up"),
    path("wallet/withdraw/", WalletWithdrawView.as_view(), name="wallet-withdraw"),
    path("wallet/transactions/", WalletTransactionListView.as_view(), name="wallet-transactions"),

    # ─── Saved Cards ──────────────────────────────────────────────────────────
    path("cards/", SavedCardListView.as_view(), name="card-list"),
    path("cards/add/", SavedCardAddView.as_view(), name="card-add"),
    path("cards/set-default/", SetDefaultCardView.as_view(), name="card-set-default"),
    path("cards/<uuid:card_id>/", SavedCardDetailView.as_view(), name="card-detail"),

    # ─── Payments ─────────────────────────────────────────────────────────────
    path("", PaymentListView.as_view(), name="payment-list"),
    path("create/", CreatePaymentView.as_view(), name="payment-create"),
    path("<uuid:payment_id>/", PaymentDetailView.as_view(), name="payment-detail"),
    path("<uuid:payment_id>/refunds/", RefundListView.as_view(), name="refund-list"),

    # ─── Refunds ──────────────────────────────────────────────────────────────
    path("refunds/", CreateRefundView.as_view(), name="refund-create"),

    # ─── Admin ────────────────────────────────────────────────────────────────
    path("admin/all/", AdminPaymentListView.as_view(), name="admin-payment-list"),

    # ─── Webhooks ─────────────────────────────────────────────────────────────
    path("webhooks/payme/", PaymeWebhookView.as_view(), name="webhook-payme"),
    path("webhooks/click/", ClickWebhookView.as_view(), name="webhook-click"),
    path("webhooks/upay/", UPayWebhookView.as_view(), name="webhook-upay"),
]
