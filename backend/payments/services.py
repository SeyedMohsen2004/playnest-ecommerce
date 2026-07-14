import secrets

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from orders.models import Order
from orders.services import mark_order_as_paid
from payments.models import Payment

MOCK_GATEWAY_URL = "http://127.0.0.1:8000/api/v1/payments/mock-gateway/"


@transaction.atomic
def request_payment(payment):
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    if payment.status != Payment.Status.PENDING:
        raise ValidationError("Only pending payments can be requested.")
    if payment.authority:
        return payment
    if not settings.DEBUG:
        raise ValidationError("ZarinPal integration is not configured.")

    payment.authority = f"mock-{secrets.token_urlsafe(24)}"
    payment.gateway_response = {
        "mode": "mock",
        "authority": payment.authority,
    }
    payment.save(update_fields=("authority", "gateway_response", "updated_at"))
    return payment


def payment_url(payment):
    return f"{MOCK_GATEWAY_URL}?authority={payment.authority}"


@transaction.atomic
def verify_payment(payment, status):
    payment = (
        Payment.objects.select_for_update().select_related("order").get(pk=payment.pk)
    )
    if payment.status == Payment.Status.PAID:
        return payment
    if payment.status != Payment.Status.PENDING:
        raise ValidationError("Only pending payments can be verified.")

    if status != "OK":
        payment.status = Payment.Status.FAILED
        payment.gateway_response = {
            **payment.gateway_response,
            "verification_status": status,
        }
        payment.save(update_fields=("status", "gateway_response", "updated_at"))
        order = Order.objects.select_for_update().get(pk=payment.order_id)
        if order.status == Order.Status.PENDING:
            order.status = Order.Status.PAYMENT_FAILED
            order.save(update_fields=("status", "updated_at"))
        return payment

    order = Order.objects.select_for_update().get(pk=payment.order_id)
    if order.status == Order.Status.PAID and not order.stock_reduced:
        raise ValidationError("Paid order has not had stock reduced.")
    mark_order_as_paid(order)

    payment.status = Payment.Status.PAID
    payment.ref_id = f"MOCK-{secrets.randbelow(1_000_000_000):09d}"
    payment.paid_at = timezone.now()
    payment.gateway_response = {
        **payment.gateway_response,
        "verification_status": status,
        "ref_id": payment.ref_id,
    }
    payment.save(
        update_fields=(
            "status",
            "ref_id",
            "paid_at",
            "gateway_response",
            "updated_at",
        )
    )
    if hasattr(order.user, "cart"):
        order.user.cart.items.all().delete()
    return payment
