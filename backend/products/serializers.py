from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from products.models import (
    Brand,
    Category,
    Product,
    ProductImage,
    ProductReview,
    WishlistItem,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
            "parent",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("id", "image", "alt_text", "is_main", "created_at")
        read_only_fields = fields


class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    final_price = serializers.IntegerField(read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)
    main_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "sku",
            "category",
            "brand",
            "price",
            "discount_price",
            "final_price",
            "stock",
            "is_in_stock",
            "age_group",
            "gender",
            "is_featured",
            "main_image",
            "created_at",
        )

    @extend_schema_field(ProductImageSerializer(allow_null=True))
    def get_main_image(self, obj):
        image = next((item for item in obj.images.all() if item.is_main), None)
        if image is None:
            return None
        return ProductImageSerializer(image, context=self.context).data


class ProductDetailSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(source="category", read_only=True)
    brand_detail = BrandSerializer(source="brand", read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    final_price = serializers.IntegerField(read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)
    average_rating = serializers.FloatField(read_only=True, allow_null=True)
    review_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "category",
            "category_detail",
            "brand",
            "brand_detail",
            "name",
            "slug",
            "description",
            "short_description",
            "sku",
            "price",
            "discount_price",
            "final_price",
            "stock",
            "is_in_stock",
            "age_group",
            "gender",
            "is_active",
            "is_featured",
            "images",
            "average_rating",
            "review_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "final_price",
            "is_in_stock",
            "images",
            "average_rating",
            "review_count",
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):
        price = attrs.get("price", getattr(self.instance, "price", None))
        discount_price = attrs.get(
            "discount_price",
            getattr(self.instance, "discount_price", None),
        )
        if price is not None and discount_price is not None and discount_price >= price:
            raise serializers.ValidationError(
                {"discount_price": "Discount price must be less than price."}
            )
        return attrs


class WishlistItemSerializer(serializers.ModelSerializer):
    product_detail = ProductListSerializer(source="product", read_only=True)

    class Meta:
        model = WishlistItem
        fields = ("id", "product", "product_detail", "created_at")
        read_only_fields = ("id", "product_detail", "created_at")

    def validate_product(self, product):
        if not product.is_active:
            raise serializers.ValidationError("Inactive products cannot be wishlisted.")
        return product

    def validate(self, attrs):
        request = self.context["request"]
        product = attrs.get("product")
        if WishlistItem.objects.filter(user=request.user, product=product).exists():
            raise serializers.ValidationError(
                {"product": "This product is already in your wishlist."}
            )
        return attrs


class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    product = serializers.SlugRelatedField(read_only=True, slug_field="slug")

    class Meta:
        model = ProductReview
        fields = (
            "id",
            "user_name",
            "product",
            "rating",
            "comment",
            "is_approved",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "user_name",
            "product",
            "is_approved",
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):
        request = self.context["request"]
        product = self.context["product"]
        if ProductReview.objects.filter(user=request.user, product=product).exists():
            raise serializers.ValidationError("You have already reviewed this product.")
        return attrs
