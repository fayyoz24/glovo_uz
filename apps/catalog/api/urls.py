from django.urls import path
from apps.catalog.api.views import (
    CategoryListView,
    BranchProductListView,
    ProductDetailView,
    MerchantProductListView,
    MerchantProductCreateView,
    MerchantProductUpdateView,
    MerchantProductToggleAvailabilityView,
)

urlpatterns = [
    # Public
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("merchants/<uuid:merchant_id>/products/", BranchProductListView.as_view(), name="branch-products"),
    path("products/<uuid:pk>/", ProductDetailView.as_view(), name="product-detail"),

    # Merchant panel
    path("merchant/products/", MerchantProductListView.as_view(), name="merchant-product-list"),
    path("merchant/products/create/", MerchantProductCreateView.as_view(), name="merchant-product-create"),
    path("merchant/products/<uuid:pk>/", MerchantProductUpdateView.as_view(), name="merchant-product-update"),
    path(
        "merchant/products/<uuid:pk>/toggle-availability/",
        MerchantProductToggleAvailabilityView.as_view(),
        name="merchant-product-toggle",
    ),
]
