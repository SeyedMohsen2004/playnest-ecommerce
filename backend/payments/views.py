from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order
from orders.serializers import OrderSerializer
from payments.models import Payment
from payments.serializers import (
    MockGatewayResponseSerializer,
    PaymentRequestSerializer,
    PaymentSerializer,
    PaymentVerifyResponseSerializer,
    PaymentVerifySerializer,
)
from payments.services import payment_url, verify_payment


class PaymentRequestView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(request=PaymentRequestSerializer, responses={201: PaymentSerializer})
    def post(self, request):
        serializer = PaymentRequestSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        try:
            payment = serializer.save()
        except DjangoValidationError as exc:
            return Response(
                {"detail": exc.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class MockGatewayView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(responses={200: MockGatewayResponseSerializer})
    def get(self, request):
        if not settings.DEBUG:
            raise Http404
        authority = request.query_params.get("authority")
        payment = Payment.objects.filter(
            authority=authority,
            status=Payment.Status.PENDING,
        ).first()
        if payment is None:
            return Response(
                {"detail": "Pending payment was not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {
                "authority": authority,
                "instruction": "POST the authority and status=OK to the verify URL.",
                "success_verify_url": ("http://127.0.0.1:8000/api/v1/payments/verify/"),
                "payment_url": payment_url(payment),
            }
        )


class ZarinPalCallbackView(APIView):
    permission_classes = (AllowAny,)

    def get_payload(self, request):
        return request.query_params if request.method == "GET" else request.data

    def handle_callback(self, request):
        payload = self.get_payload(request)
        authority = payload.get("Authority") or payload.get("authority")
        gateway_status = payload.get("Status") or payload.get("status")
        if not authority:
            return Response(
                {"detail": "Authority is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment = Payment.objects.filter(authority=authority).first()
        if payment is None:
            return Response(
                {
                    "detail": "Payment was not found.",
                    "authority": authority,
                    "status": gateway_status,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        payment.status_from_gateway = gateway_status or ""
        payment.gateway_response = {
            **payment.gateway_response,
            "callback": {
                "authority": authority,
                "status": gateway_status,
            },
        }
        payment.save(
            update_fields=(
                "status_from_gateway",
                "gateway_response",
                "updated_at",
            )
        )
        return Response(
            {
                "authority": authority,
                "status": gateway_status,
                "payment": PaymentSerializer(payment).data,
            }
        )

    def get(self, request):
        return self.handle_callback(request)

    def post(self, request):
        return self.handle_callback(request)


class PaymentVerifyView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        request=PaymentVerifySerializer,
        responses={200: PaymentVerifyResponseSerializer},
    )
    def post(self, request):
        serializer = PaymentVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = Payment.objects.filter(
            authority=serializer.validated_data["authority"]
        ).first()
        if payment is None:
            return Response(
                {"detail": "Payment was not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            payment = verify_payment(payment, serializer.validated_data["status"])
        except DjangoValidationError as exc:
            return Response(
                {
                    "detail": (
                        exc.message_dict
                        if hasattr(exc, "message_dict")
                        else exc.messages
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        order = Order.objects.prefetch_related("items").get(pk=payment.order_id)
        return Response(
            {
                "payment": PaymentSerializer(payment).data,
                "order": OrderSerializer(order).data,
            }
        )
