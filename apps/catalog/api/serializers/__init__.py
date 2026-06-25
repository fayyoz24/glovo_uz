from rest_framework import serializers
from apps.catalog.models import (
    ProductCategory,
    Product,
    ProductImage,
    ProductVariant,
    ProductModifierGroup,
    ProductModifierOption,
)


class ProductCategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = ProductCategory
        fields = ["id", "parent", "name_uz", "name_ru", "icon", "sort_order", "children"]

    def get_children(self, obj):
        if obj.children.exists():
            return ProductCategorySerializer(obj.children.filter(is_active=True), many=True).data
        return []


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "sort_order"]


class ProductVariantSerializer(serializers.ModelSerializer):
    final_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = ProductVariant
        fields = ["id", "name_uz", "name_ru", "price_delta", "final_price", "is_default"]


class ProductModifierOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductModifierOption
        fields = ["id", "name_uz", "name_ru", "price_delta"]


class ProductModifierGroupSerializer(serializers.ModelSerializer):
    options = ProductModifierOptionSerializer(many=True, read_only=True)

    class Meta:
        model = ProductModifierGroup
        fields = ["id", "name_uz", "name_ru", "group_type", "min_select", "max_select", "required", "options"]


class ProductListSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source="category.name_uz", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name_uz", "name_ru", "base_price", "is_available",
            "category_name", "images", "sort_order",
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    modifier_groups = ProductModifierGroupSerializer(many=True, read_only=True)
    category = ProductCategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name_uz", "name_ru", "description_uz", "description_ru",
            "base_price", "is_active", "is_available", "sku",
            "category", "images", "variants", "modifier_groups",
        ]


class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "merchant", "branch", "category", "name_uz", "name_ru",
            "description_uz", "description_ru", "base_price", "sku",
        ]


class ProductUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "category", "name_uz", "name_ru", "description_uz",
            "description_ru", "base_price", "is_active", "is_available",
            "sku", "sort_order",
        ]
        extra_kwargs = {field: {"required": False} for field in fields}
