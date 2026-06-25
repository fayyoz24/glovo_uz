from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.catalog.api.serializers import (
    ProductCategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductWriteSerializer,
)
from apps.catalog.selectors import (
    get_active_categories,
    get_products_for_merchant,
    get_product_by_id,
    search_products,
)
from apps.catalog.services import (
    create_product,
    update_product,
    toggle_product_availability,
)
from apps.catalog.exceptions import ProductNotFound
from apps.catalog.permissions import IsMerchantOwnerOrManager
from apps.common.pagination import StandardPagination


class CategoryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        parent_id = request.query_params.get("parent")
        categories = get_active_categories(parent_id=parent_id)
        return Response(ProductCategorySerializer(categories, many=True).data)


class MerchantProductListView(APIView):
    """GET /merchants/<merchant_pk>/products/ — public catalog"""
    permission_classes = [AllowAny]

    def get(self, request, merchant_pk):
        category_id = request.query_params.get("category")
        products = get_products_for_merchant(merchant_pk, category_id=category_id)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(products, request)
        serializer = ProductListSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)


class ProductDetailView(APIView):
    """GET /products/<pk>/ — full detail with variants and modifiers"""
    permission_classes = [AllowAny]

    def get(self, request, pk):
        product = get_product_by_id(pk)
        if not product:
            raise ProductNotFound()
        return Response(ProductDetailSerializer(product, context={"request": request}).data)


class ProductSearchView(APIView):
    """GET /search/?q=... — full-text search across products"""
    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            return Response({"results": []})
        merchant_id = request.query_params.get("merchant")
        products = search_products(query, merchant_id=merchant_id)
        return Response({
            "results": ProductListSerializer(products, many=True, context={"request": request}).data
        })


# ── Merchant panel views ───────────────────────────────────────────────────────

class MerchantProductManageView(APIView):
    """POST /merchant/products/ — merchant o'z productini qo'shadi"""
    permission_classes = [IsAuthenticated, IsMerchantOwnerOrManager]

    def post(self, request):
        serializer = ProductWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        merchant = request.user.merchant_staff_profile.merchant
        product = create_product(merchant, serializer.validated_data)
        return Response(ProductDetailSerializer(product).data, status=status.HTTP_201_CREATED)


class MerchantProductUpdateView(APIView):
    """PATCH /merchant/products/<pk>/ — merchant o'z productini yangilaydi"""
    permission_classes = [IsAuthenticated, IsMerchantOwnerOrManager]

    def patch(self, request, pk):
        serializer = ProductWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        merchant = request.user.merchant_staff_profile.merchant
        product = update_product(pk, merchant, serializer.validated_data)
        return Response(ProductDetailSerializer(product).data)


class ProductToggleAvailabilityView(APIView):
    """POST /merchant/products/<pk>/toggle-availability/"""
    permission_classes = [IsAuthenticated, IsMerchantOwnerOrManager]

    def post(self, request, pk):
        is_available = request.data.get("is_available", True)
        merchant = request.user.merchant_staff_profile.merchant
        product = toggle_product_availability(pk, merchant, bool(is_available))
        return Response({"id": str(product.id), "is_available": product.is_available})
