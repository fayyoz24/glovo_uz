from rest_framework import generics, views, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from apps.catalog.selectors import (
    get_active_categories,
    get_products_for_branch,
    get_product_detail,
    get_products_for_merchant,
)
from apps.catalog.services import (
    create_product,
    update_product,
    toggle_product_availability,
)
from apps.catalog.api.serializers import (
    ProductCategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateSerializer,
    ProductUpdateSerializer,
)
from apps.catalog.exceptions import ProductNotFound


class CategoryListView(generics.ListAPIView):
    """GET /api/v1/categories/  — barcha faol kategoriyalar (daraxt)"""
    serializer_class = ProductCategorySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return get_active_categories()


class BranchProductListView(generics.ListAPIView):
    """GET /api/v1/merchants/{merchant_id}/products/?branch=&category=&q="""
    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        branch_id = self.request.query_params.get("branch")
        category_id = self.request.query_params.get("category")
        search = self.request.query_params.get("q", "")
        return get_products_for_branch(branch_id=branch_id, category_id=category_id, search=search)


class ProductDetailView(generics.RetrieveAPIView):
    """GET /api/v1/products/{id}/"""
    serializer_class = ProductDetailSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        try:
            return get_product_detail(self.kwargs["pk"])
        except Product.DoesNotExist:
            raise ProductNotFound()


class MerchantProductListView(generics.ListAPIView):
    """GET /api/v1/merchant/products/  — merchant panel uchun"""
    serializer_class = ProductListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return get_products_for_merchant(
            merchant_id=self.request.user.merchant_staff_profile.merchant_id,
            search=self.request.query_params.get("q", ""),
        )


class MerchantProductCreateView(generics.CreateAPIView):
    """POST /api/v1/merchant/products/"""
    serializer_class = ProductCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        data = serializer.validated_data
        create_product(
            merchant=data["merchant"],
            branch=data.get("branch"),
            category=data.get("category"),
            name_uz=data["name_uz"],
            name_ru=data.get("name_ru", ""),
            description_uz=data.get("description_uz", ""),
            description_ru=data.get("description_ru", ""),
            base_price=data["base_price"],
            sku=data.get("sku", ""),
        )


class MerchantProductUpdateView(generics.UpdateAPIView):
    """PATCH /api/v1/merchant/products/{id}/"""
    serializer_class = ProductUpdateSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        try:
            product = update_product(product_id=kwargs["pk"], **request.data)
        except ProductNotFound as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProductDetailSerializer(product).data)


class MerchantProductToggleAvailabilityView(views.APIView):
    """POST /api/v1/merchant/products/{id}/toggle-availability/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        is_available = request.data.get("is_available")
        if is_available is None:
            return Response(
                {"detail": "is_available maydoni kerak."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            product = toggle_product_availability(product_id=pk, is_available=bool(is_available))
        except ProductNotFound as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response({"id": str(product.id), "is_available": product.is_available})
