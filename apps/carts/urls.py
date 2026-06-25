from django.urls import path
from apps.carts.api.views import (
    CartView,
    CartItemAddView,
    CartItemDetailView,
    CartPromoView,
)

urlpatterns = [
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/items/", CartItemAddView.as_view(), name="cart-item-add"),
    path("cart/items/<uuid:item_id>/", CartItemDetailView.as_view(), name="cart-item-detail"),
    path("cart/promo/", CartPromoView.as_view(), name="cart-promo"),
]
