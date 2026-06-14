from django.db import transaction
from rest_framework import serializers

from orders.models import Cart, CartItem, Order, OrderItem
from products.models import Product


class CartProductSerializer(serializers.ModelSerializer):
    final_price = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = ("id", "name", "slug", "sku", "final_price", "stock")
        read_only_fields = fields


class CartItemSerializer(serializers.ModelSerializer):
    product = CartProductSerializer(read_only=True)
    subtotal = serializers.IntegerField(read_only=True)

    class Meta:
        model = CartItem
        fields = ("id", "product", "quantity", "subtotal", "created_at")
        read_only_fields = fields


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_price = serializers.IntegerField(source="subtotal", read_only=True)

    class Meta:
        model = Cart
        fields = ("items", "total_items", "total_price", "created_at", "updated_at")
        read_only_fields = fields


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
            .filter(
                cart=cart,
                product=product,
            )
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
    class Meta:
        model = OrderItem
        fields = (
            "id",
            "product",
            "product_name",
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
        total_amount = 0
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
            total_amount += line_total
            order_lines.append(
                {
                    "product": product,
                    "product_name": product.name,
                    "product_price": price,
                    "quantity": item.quantity,
                    "line_total": line_total,
                }
            )
            product.stock -= item.quantity
            product.save(update_fields=("stock",))

        order = Order.objects.create(
            user=user,
            total_amount=total_amount,
            **validated_data,
        )
        OrderItem.objects.bulk_create(
            [OrderItem(order=order, **line) for line in order_lines]
        )
        cart.items.all().delete()
        return order
