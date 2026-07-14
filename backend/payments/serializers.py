from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from orders.models import Order
from orders.serializers import OrderSerializer
from payments.models import Payment
from payments.services import payment_url, request_payment


class PaymentSerializer(serializers.ModelSerializer):
    payment_url = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = (
            "id",
            "order",
            "gateway",
            "amount",
            "status",
            "authority",
            "ref_id",
            "card_pan",
            "gateway_response",
            "payment_url",
            "created_at",
            "updated_at",
            "paid_at",
        )
        read_only_fields = fields

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_payment_url(self, obj):
        if obj.status == Payment.Status.PENDING and obj.authority:
            return payment_url(obj)
        return None


class PaymentRequestSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(min_value=1)

    def validate_order_id(self, value):
        request = self.context["request"]
        queryset = Order.objects.filter(pk=value)
        if not request.user.is_staff:
            queryset = queryset.filter(user=request.user)
        order = queryset.first()
        if order is None:
            raise serializers.ValidationError("Order was not found.")
        if order.status == Order.Status.PAID:
            raise serializers.ValidationError("Order is already paid.")
        if order.status not in (Order.Status.PENDING, Order.Status.PAYMENT_FAILED):
            raise serializers.ValidationError("Only unpaid orders can be paid.")
        self.order = order
        return value

    @transaction.atomic
    def create(self, validated_data):
        order = Order.objects.select_for_update().get(pk=self.order.pk)
        if order.status not in (Order.Status.PENDING, Order.Status.PAYMENT_FAILED):
            raise serializers.ValidationError("Only unpaid orders can be paid.")
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
        return request_payment(payment)


class PaymentVerifySerializer(serializers.Serializer):
    authority = serializers.CharField(max_length=100)
    status = serializers.CharField(max_length=20)


class PaymentVerifyResponseSerializer(serializers.Serializer):
    payment = PaymentSerializer(read_only=True)
    order = OrderSerializer(read_only=True)


class MockGatewayResponseSerializer(serializers.Serializer):
    authority = serializers.CharField(read_only=True)
    instruction = serializers.CharField(read_only=True)
    success_verify_url = serializers.URLField(read_only=True)
    payment_url = serializers.URLField(read_only=True)
