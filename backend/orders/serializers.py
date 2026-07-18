from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from orders.models import Cart, CartItem, Coupon, Order, OrderItem
from orders.pricing import calculate_order_totals
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

    def get_status_label(self, obj):
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

    def get_payment_status(self, obj):
        payment = self._latest_payment(obj)
        return payment.status if payment else None

    def get_payment_ref_id(self, obj):
        payment = self._latest_payment(obj)
        return payment.ref_id if payment and payment.status == "paid" else None

    def get_payment_status_label(self, obj):
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

    def get_can_retry_payment(self, obj):
        return obj.status in (Order.Status.PENDING, Order.Status.PAYMENT_FAILED)

    def get_can_cancel(self, obj):
        return obj.status in (Order.Status.PENDING, Order.Status.PAYMENT_FAILED)

    def get_can_edit_shipping_info(self, obj):
        return obj.status in (
            Order.Status.PENDING,
            Order.Status.PAYMENT_FAILED,
            Order.Status.PAID,
        )

    def get_manual_review_message(self, obj):
        if not obj.requires_manual_review:
            return None
        return (
            "پرداخت با موفقیت انجام شد و سفارش برای بررسی موجودی " "در حال پیگیری است."
        )


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
            .prefetch_related("items__product")
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
        subtotal_amount = 0
        order_lines = []
        for item in cart_items:
            product = products[item.product_id]
            if not product.is_active:
                raise serializers.ValidationError(
                    {"cart": f"{product.name} is inactive."}
                )
            if item.quantity > product.stock:
                raise serializers.ValidationError(
                    {"cart": f"Insufficient stock for {product.name}."}
                )
            price = product.final_price

            line_total = price * item.quantity
            subtotal_amount += line_total
            order_lines.append(
                {
                    "product": product,
                    "product_name": product.name,
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
        return order
