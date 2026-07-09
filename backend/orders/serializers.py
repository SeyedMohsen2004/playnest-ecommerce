from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from orders.models import Cart, CartItem, Coupon, Order, OrderItem
from orders.pricing import calculate_order_totals
from products.models import Product, ProductVariant


class CartProductSerializer(serializers.ModelSerializer):
    final_price = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = ("id", "name", "slug", "sku", "final_price", "stock")
        read_only_fields = fields


class CartItemSerializer(serializers.ModelSerializer):
    product = CartProductSerializer(read_only=True)
    variant = serializers.PrimaryKeyRelatedField(read_only=True)
    variant_id = serializers.IntegerField(source="variant.id", read_only=True)
    variant_price = serializers.IntegerField(source="unit_price", read_only=True)
    selected_options_label = serializers.CharField(read_only=True)
    subtotal = serializers.IntegerField(read_only=True)

    class Meta:
        model = CartItem
        fields = (
            "id",
            "product",
            "variant",
            "variant_id",
            "variant_price",
            "selected_options_label",
            "quantity",
            "subtotal",
            "created_at",
        )
        read_only_fields = fields


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_price = serializers.IntegerField(source="subtotal", read_only=True)

    class Meta:
        model = Cart
        fields = ("items", "total_items", "total_price", "created_at", "updated_at")
        read_only_fields = fields


class CartSummarySerializer(serializers.Serializer):
    subtotal = serializers.IntegerField(read_only=True)
    discount_amount = serializers.IntegerField(read_only=True)
    shipping_cost = serializers.IntegerField(read_only=True)
    total_amount = serializers.IntegerField(read_only=True)


class ApplyCouponSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)

    def validate_code(self, value):
        coupon = Coupon.objects.filter(code__iexact=value.strip()).first()
        if coupon is None:
            raise serializers.ValidationError("Coupon was not found.")
        self.coupon = coupon
        return value

    def create(self, validated_data):
        try:
            return calculate_order_totals(
                self.context["cart"].subtotal,
                self.coupon,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc


class CartItemCreateSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.select_related("product").all(),
        source="variant",
        required=False,
        allow_null=True,
    )
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        product = attrs["product"]
        quantity = attrs["quantity"]
        variant = attrs.get("variant")
        if not product.is_active:
            raise serializers.ValidationError(
                {"product": "Inactive products cannot be added to a cart."}
            )
        active_variants_exist = product.variants.filter(is_active=True).exists()
        if active_variants_exist and variant is None:
            raise serializers.ValidationError(
                {"variant_id": "لطفاً گزینه‌های محصول را انتخاب کنید."}
            )
        if variant is not None:
            if variant.product_id != product.id:
                raise serializers.ValidationError(
                    {"variant_id": "Variant does not belong to this product."}
                )
            if not variant.is_active:
                raise serializers.ValidationError(
                    {"variant_id": "Selected variant is inactive."}
                )
            if quantity > variant.stock:
                raise serializers.ValidationError(
                    {"quantity": "Quantity cannot exceed selected variant stock."}
                )
            return attrs
        if quantity > product.stock:
            raise serializers.ValidationError(
                {"quantity": "Quantity cannot exceed available stock."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        cart = validated_data.pop("cart")
        product = validated_data["product"]
        variant = validated_data.get("variant")
        quantity = validated_data["quantity"]
        item = (
            CartItem.objects.select_for_update()
            .filter(
                cart=cart,
                product=product,
                variant=variant,
            )
            .first()
        )
        if item:
            quantity += item.quantity
            available_stock = variant.stock if variant else product.stock
            if quantity > available_stock:
                raise serializers.ValidationError(
                    {"quantity": "Quantity cannot exceed available stock."}
                )
            item.quantity = quantity
            item.save(update_fields=("quantity",))
            return item
        return CartItem.objects.create(cart=cart, **validated_data)


class CartItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ("quantity",)
        extra_kwargs = {"quantity": {"min_value": 1}}

    def validate_quantity(self, value):
        available_stock = (
            self.instance.variant.stock
            if self.instance.variant_id
            else self.instance.product.stock
        )
        if value > available_stock:
            raise serializers.ValidationError("Quantity cannot exceed available stock.")
        if not self.instance.product.is_active:
            raise serializers.ValidationError("This product is inactive.")
        if self.instance.variant_id and not self.instance.variant.is_active:
            raise serializers.ValidationError("Selected variant is inactive.")
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = (
            "id",
            "product",
            "variant",
            "product_name",
            "selected_options_snapshot",
            "product_price",
            "quantity",
            "line_total",
        )
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "status",
            "stock_reduced",
            "coupon",
            "subtotal_amount",
            "discount_amount",
            "shipping_cost",
            "total_amount",
            "shipping_address",
            "postal_code",
            "recipient_name",
            "recipient_phone",
            "items",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class CheckoutSerializer(serializers.Serializer):
    shipping_address = serializers.CharField()
    postal_code = serializers.CharField(max_length=20)
    recipient_name = serializers.CharField(max_length=255)
    recipient_phone = serializers.CharField(max_length=20)
    coupon_code = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        write_only=True,
    )

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user
        cart = (
            Cart.objects.select_for_update()
            .filter(user=user)
            .prefetch_related("items__product", "items__variant__option_values__option")
            .first()
        )
        if cart is None or not cart.items.exists():
            raise serializers.ValidationError("Cart is empty.")

        cart_items = list(cart.items.all())
        products = {
            product.id: product
            for product in Product.objects.select_for_update().filter(
                id__in=[item.product_id for item in cart_items]
            )
        }
        variants = {
            variant.id: variant
            for variant in ProductVariant.objects.select_for_update()
            .filter(id__in=[item.variant_id for item in cart_items if item.variant_id])
            .prefetch_related("option_values__option")
        }
        subtotal_amount = 0
        order_lines = []
        for item in cart_items:
            product = products[item.product_id]
            if not product.is_active:
                raise serializers.ValidationError(
                    {"cart": f"{product.name} is inactive."}
                )
            if item.variant_id:
                variant = variants[item.variant_id]
                if not variant.is_active:
                    raise serializers.ValidationError(
                        {"cart": f"{product.name} selected variant is inactive."}
                    )
                if item.quantity > variant.stock:
                    raise serializers.ValidationError(
                        {"cart": f"Insufficient stock for {product.name}."}
                    )
                price = variant.price
                selected_options_snapshot = variant.selected_options_label
            else:
                if item.quantity > product.stock:
                    raise serializers.ValidationError(
                        {"cart": f"Insufficient stock for {product.name}."}
                    )
                price = product.final_price
                selected_options_snapshot = ""

            line_total = price * item.quantity
            subtotal_amount += line_total
            order_lines.append(
                {
                    "product": product,
                    "variant": item.variant if item.variant_id else None,
                    "product_name": product.name,
                    "selected_options_snapshot": selected_options_snapshot,
                    "product_price": price,
                    "quantity": item.quantity,
                    "line_total": line_total,
                }
            )

        coupon_code = validated_data.pop("coupon_code", "").strip()
        coupon = None
        if coupon_code:
            coupon = Coupon.objects.filter(code__iexact=coupon_code).first()
            if coupon is None:
                raise serializers.ValidationError(
                    {"coupon_code": "Coupon was not found."}
                )
        try:
            totals = calculate_order_totals(subtotal_amount, coupon)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc

        order = Order.objects.create(
            user=user,
            coupon=coupon,
            subtotal_amount=totals["subtotal"],
            discount_amount=totals["discount_amount"],
            shipping_cost=totals["shipping_cost"],
            total_amount=totals["total_amount"],
            **validated_data,
        )
        OrderItem.objects.bulk_create(
            [OrderItem(order=order, **line) for line in order_lines]
        )
        cart.items.all().delete()
        return order
