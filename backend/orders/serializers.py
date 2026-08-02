from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from orders.models import Cart, CartItem, Coupon, Order, OrderItem
from orders.pricing import calculate_order_totals
from orders.services import checkout_cart
from products.models import Product
from products.serializers import ProductImageSerializer


class CartProductSerializer(serializers.ModelSerializer):
    final_price = serializers.IntegerField(read_only=True)
    main_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "sku",
            "final_price",
            "stock",
            "main_image",
        )
        read_only_fields = fields

    @extend_schema_field(ProductImageSerializer(allow_null=True))
    def get_main_image(self, obj):
        image = next(iter(obj.images.all()), None)
        if image is None:
            return None
        return ProductImageSerializer(image, context=self.context).data


class CartItemSerializer(serializers.ModelSerializer):
    product = CartProductSerializer(read_only=True)
    subtotal = serializers.IntegerField(read_only=True)

    class Meta:
        model = CartItem
        fields = (
            "id",
            "product",
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


class ShippingRateSerializer(serializers.Serializer):
    label = serializers.CharField(read_only=True)
    fee = serializers.IntegerField(read_only=True)


class ShippingRatesSerializer(serializers.Serializer):
    tabriz = ShippingRateSerializer(read_only=True)
    nationwide = ShippingRateSerializer(read_only=True)


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
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        product = attrs["product"]
        quantity = attrs["quantity"]
        if not product.is_active:
            raise serializers.ValidationError(
                {"product": "Inactive products cannot be added to a cart."}
            )
        if quantity > product.stock:
            raise serializers.ValidationError(
                {"quantity": "Quantity cannot exceed available stock."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        cart = validated_data.pop("cart")
        product = validated_data["product"]
        quantity = validated_data["quantity"]
        item = (
            CartItem.objects.select_for_update()
            .filter(cart=cart, product=product)
            .first()
        )
        if item:
            quantity += item.quantity
            if quantity > product.stock:
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
        if value > self.instance.product.stock:
            raise serializers.ValidationError("Quantity cannot exceed available stock.")
        if not self.instance.product.is_active:
            raise serializers.ValidationError("This product is inactive.")
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    product_slug = serializers.CharField(source="product.slug", read_only=True)
    product_image = serializers.SerializerMethodField()
    unit_price = serializers.IntegerField(source="product_price", read_only=True)
    total_price = serializers.IntegerField(source="line_total", read_only=True)

    class Meta:
        model = OrderItem
        fields = (
            "id",
            "product",
            "product_slug",
            "product_image",
            "product_name",
            "product_price",
            "unit_price",
            "quantity",
            "line_total",
            "total_price",
        )
        read_only_fields = fields

    @extend_schema_field(ProductImageSerializer(allow_null=True))
    def get_product_image(self, obj):
        image = next(iter(obj.product.images.all()), None)
        if image is None:
            return None
        return ProductImageSerializer(image, context=self.context).data


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_label = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()
    payment_status_label = serializers.SerializerMethodField()
    payment_ref_id = serializers.SerializerMethodField()
    can_retry_payment = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()
    can_edit_shipping_info = serializers.SerializerMethodField()
    manual_review_message = serializers.SerializerMethodField()
    shipping_zone_display = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            "id",
            "status",
            "status_label",
            "payment_status",
            "payment_status_label",
            "payment_ref_id",
            "can_retry_payment",
            "can_cancel",
            "can_edit_shipping_info",
            "stock_reduced",
            "requires_manual_review",
            "manual_review_message",
            "coupon",
            "subtotal_amount",
            "discount_amount",
            "shipping_zone",
            "shipping_zone_display",
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

    def get_status_label(self, obj) -> str:
        labels = {
            Order.Status.PENDING: "در انتظار پرداخت",
            Order.Status.PAYMENT_FAILED: "پرداخت ناموفق",
            Order.Status.PAID: "پرداخت موفق، در انتظار تایید",
            Order.Status.PROCESSING: "در حال آماده‌سازی",
            Order.Status.SHIPPED: "ارسال شده",
            Order.Status.DELIVERED: "تحویل داده شده",
            Order.Status.CANCELLED: "لغو شده",
        }
        return labels.get(obj.status, obj.get_status_display())

    def get_payment_status(self, obj) -> str | None:
        payment = self._latest_payment(obj)
        return payment.status if payment else None

    def get_payment_ref_id(self, obj) -> str | None:
        payment = self._latest_payment(obj)
        return payment.ref_id if payment and payment.status == "paid" else None

    def get_payment_status_label(self, obj) -> str | None:
        status = self.get_payment_status(obj)
        if status is None:
            return None
        labels = {
            "pending": "در انتظار پرداخت",
            "paid": "پرداخت شده",
            "failed": "ناموفق",
            "cancelled": "لغو شده",
        }
        return labels.get(status, status)

    def _latest_payment(self, obj):
        if not hasattr(obj, "_latest_payment_cache"):
            prefetched = list(obj.payments.all())
            obj._latest_payment_cache = max(
                prefetched,
                key=lambda payment: payment.created_at,
                default=None,
            )
        return obj._latest_payment_cache

    def get_can_retry_payment(self, obj) -> bool:
        return obj.status in (Order.Status.PENDING, Order.Status.PAYMENT_FAILED)

    def get_can_cancel(self, obj) -> bool:
        return obj.status in (Order.Status.PENDING, Order.Status.PAYMENT_FAILED)

    def get_can_edit_shipping_info(self, obj) -> bool:
        return obj.status in (
            Order.Status.PENDING,
            Order.Status.PAYMENT_FAILED,
            Order.Status.PAID,
        )

    def get_shipping_zone_display(self, obj) -> str:
        if not obj.shipping_zone:
            return "ثبت نشده"
        return obj.get_shipping_zone_display()

    def get_manual_review_message(self, obj) -> str | None:
        if not obj.requires_manual_review:
            return None
        return "پرداخت ثبت شده و سفارش برای بررسی دستی در حال پیگیری است."


class OrderShippingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = (
            "recipient_name",
            "recipient_phone",
            "shipping_address",
            "postal_code",
        )
        extra_kwargs = {
            "recipient_name": {"required": False},
            "recipient_phone": {"required": False},
            "shipping_address": {"required": False},
            "postal_code": {"required": False},
        }


class CheckoutSerializer(serializers.Serializer):
    shipping_address = serializers.CharField()
    postal_code = serializers.CharField(max_length=20)
    recipient_name = serializers.CharField(max_length=255)
    recipient_phone = serializers.CharField(max_length=20)
    shipping_zone = serializers.ChoiceField(choices=Order.ShippingZone.choices)
    coupon_code = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        write_only=True,
    )

    def validate(self, attrs):
        if "shipping_cost" in self.initial_data:
            raise serializers.ValidationError(
                {"shipping_cost": "Shipping cost is calculated by the server."}
            )
        return attrs

    def create(self, validated_data):
        try:
            return checkout_cart(
                user=self.context["request"].user,
                **validated_data,
            )
        except DjangoValidationError as exc:
            detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            raise serializers.ValidationError(detail) from exc
