from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers

from orders.models import Order
from payments.models import Payment
from payments.services import payment_url, request_payment
from payments.services.zarinpal import mask_card_pan
from products.models import Product


class PaymentSerializer(serializers.ModelSerializer):
    payment_url = serializers.SerializerMethodField()
    card_pan = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = (
            "id",
            "order",
            "gateway",
            "amount",
            "status",
            "ref_id",
            "card_pan",
            "payment_url",
            "created_at",
            "updated_at",
            "paid_at",
            "verified_at",
        )
        read_only_fields = fields

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_payment_url(self, obj):
        if obj.status == Payment.Status.PENDING and obj.authority:
            return payment_url(obj)
        return None

    def get_card_pan(self, obj):
        return mask_card_pan(obj.card_pan)


class PaymentRequestSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(min_value=1)

    def validate_order_id(self, value):
        request = self.context["request"]
        queryset = Order.objects.filter(pk=value)
        order = queryset.first()
        if order is None:
            raise serializers.ValidationError("Order was not found.")
        if not request.user.is_staff and order.user_id != request.user.id:
            raise PermissionDenied("You do not have permission to pay this order.")
        if order.status == Order.Status.PAID:
            raise serializers.ValidationError("این سفارش قبلاً پرداخت شده است.")
        if order.status == Order.Status.CANCELLED:
            raise serializers.ValidationError(
                "این سفارش لغو شده است و امکان پرداخت ندارد."
            )
        if order.status not in (Order.Status.PENDING, Order.Status.PAYMENT_FAILED):
            raise serializers.ValidationError("این سفارش در وضعیت قابل پرداخت نیست.")
        self.order = order
        return value

    def validate(self, attrs):
        order = Order.objects.filter(pk=self.order.pk).prefetch_related("items").first()
        self.validate_order_stock(order)
        return attrs

    def validate_order_stock(self, order, lock_products=False):
        order_items = list(order.items.all())
        product_ids = [item.product_id for item in order_items]
        products = Product.objects.filter(id__in=product_ids)
        if lock_products:
            products = products.select_for_update()
        products_by_id = {product.id: product for product in products}
        stock_errors = []
        for item in order_items:
            product = products_by_id.get(item.product_id)
            if (
                product is None
                or not product.is_active
                or product.stock < item.quantity
            ):
                stock_errors.append(
                    {
                        "product_name": item.product_name,
                        "requested_quantity": item.quantity,
                        "available_stock": (
                            product.stock if product and product.is_active else 0
                        ),
                    }
                )

        if stock_errors:
            raise serializers.ValidationError(
                {
                    "detail": "موجودی برخی از محصولات این سفارش کافی نیست.",
                    "items": stock_errors,
                }
            )

    def create(self, validated_data):
        payment = self._prepare_payment()
        return request_payment(payment)

    @transaction.atomic
    def _prepare_payment(self):
        order = Order.objects.select_for_update().get(pk=self.order.pk)
        if order.status not in (Order.Status.PENDING, Order.Status.PAYMENT_FAILED):
            raise serializers.ValidationError("این سفارش در وضعیت قابل پرداخت نیست.")
        self.validate_order_stock(order, lock_products=True)
        payment = Payment.objects.filter(
            order=order,
            status=Payment.Status.PENDING,
        ).first()
        if payment is None:
            payment = Payment.objects.create(
                user=order.user,
                order=order,
                amount=order.total_amount,
            )
        return payment
