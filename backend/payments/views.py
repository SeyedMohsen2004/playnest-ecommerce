import logging
import re
from urllib.parse import urlencode

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import HttpResponseRedirect
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from payments.models import Payment
from payments.serializers import (
    PaymentRequestSerializer,
    PaymentSerializer,
)
from payments.services import (
    finalize_verified_payment,
    record_failed_callback,
    record_verification_uncertainty,
)
from payments.services.zarinpal import (
    ZarinPalError,
    ZarinPalService,
    ZarinPalTransportError,
    ZarinPalVerificationError,
)

logger = logging.getLogger(__name__)
AUTHORITY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,100}$")


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


class ZarinPalCallbackView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        authority = str(request.query_params.get("Authority") or "").strip()
        if not authority:
            logger.warning("ZarinPal callback received without an authority.")
            return self._failure_redirect("missing_authority")
        if not AUTHORITY_PATTERN.fullmatch(authority):
            logger.warning("ZarinPal callback received an invalid authority format.")
            return self._failure_redirect("payment_not_found")

        gateway_status = str(request.query_params.get("Status") or "").strip().upper()
        if gateway_status not in {"OK", "NOK"}:
            logger.warning(
                "ZarinPal callback received an invalid status.",
                extra={"callback_status": gateway_status[:20]},
            )
            return self._failure_redirect("invalid_callback_status")

        payment = (
            Payment.objects.select_related("order").filter(authority=authority).first()
        )
        if payment is None or payment.order_id is None or payment.amount <= 0:
            logger.warning("ZarinPal callback payment could not be found.")
            return self._failure_redirect("payment_not_found")

        if gateway_status == "NOK":
            record_failed_callback(payment.id, callback_status="NOK")
            return self._failure_redirect(
                "cancelled_or_failed",
                order_id=payment.order_id,
            )

        if self._is_fully_finalized(payment):
            if payment.order.status == payment.order.Status.CANCELLED:
                return self._failure_redirect(
                    "order_cancelled",
                    order_id=payment.order_id,
                )
            return self._success_redirect(payment)

        try:
            verification = ZarinPalService().verify_payment(
                authority=payment.authority,
                amount=payment.amount,
            )
        except ZarinPalVerificationError as exc:
            record_failed_callback(
                payment.id,
                callback_status="OK",
                gateway_code=exc.code,
                gateway_message=str(exc),
                gateway_response=exc.gateway_response,
            )
            logger.warning(
                "ZarinPal verification was rejected.",
                extra={"payment_id": payment.id, "order_id": payment.order_id},
            )
            return self._failure_redirect(
                "verification_failed",
                order_id=payment.order_id,
            )
        except (ZarinPalTransportError, ZarinPalError) as exc:
            record_verification_uncertainty(
                payment.id,
                gateway_message="Verification could not be completed.",
                gateway_response=exc.gateway_response,
            )
            logger.warning(
                "ZarinPal verification could not be completed.",
                extra={"payment_id": payment.id, "order_id": payment.order_id},
            )
            return self._failure_redirect(
                "verification_unavailable",
                order_id=payment.order_id,
            )

        try:
            result = finalize_verified_payment(
                payment.id,
                authority=authority,
                verification=verification,
            )
        except DjangoValidationError:
            logger.error(
                "Local payment finalization validation failed.",
                extra={"payment_id": payment.id, "order_id": payment.order_id},
            )
            return self._failure_redirect(
                "finalization_failed",
                order_id=payment.order_id,
            )

        payment.refresh_from_db()
        if not result.order_paid:
            return self._failure_redirect(result.reason, order_id=result.order_id)
        return self._success_redirect(payment)

    def _is_fully_finalized(self, payment):
        order = payment.order
        return payment.status == Payment.Status.PAID and (
            (order.stock_reduced and payment.cart_finalized)
            or order.requires_manual_review
            or order.status == order.Status.CANCELLED
        )

    def _success_redirect(self, payment):
        return self._redirect(
            "/payment/success",
            order_id=payment.order_id,
            ref_id=payment.ref_id,
        )

    def _failure_redirect(self, reason, *, order_id=None):
        return self._redirect(
            "/payment/failed",
            order_id=order_id,
            reason=reason,
        )

    def _redirect(self, path, **parameters):
        query = urlencode(
            {key: value for key, value in parameters.items() if value not in (None, "")}
        )
        location = f"{settings.FRONTEND_BASE_URL.rstrip('/')}{path}"
        if query:
            location = f"{location}?{query}"
        return HttpResponseRedirect(location)


class PaymentVerifyView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        return Response(
            {"detail": "This legacy verification endpoint is no longer available."},
            status=status.HTTP_410_GONE,
        )
