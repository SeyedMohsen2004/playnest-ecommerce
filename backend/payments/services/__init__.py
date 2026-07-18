import logging
from collections import Counter
from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from orders.models import Cart, CartItem, Order
from orders.services import mark_order_as_paid
from payments.models import Payment
from payments.services.zarinpal import (
    PaymentVerificationResult,
    ZarinPalError,
    ZarinPalService,
)

logger = logging.getLogger(__name__)

INVENTORY_REVIEW_REASON = (
    "Verified payment completed, but inventory was insufficient during " "finalization."
)
CANCELLED_ORDER_REVIEW_REASON = (
    "Verified payment was received for an order that was already cancelled."
)
INCONSISTENT_ORDER_REVIEW_REASON = (
    "Verified payment requires manual review because the order was already in "
    "fulfillment without completed inventory finalization."
)


@dataclass(frozen=True)
class PaymentFinalizationResult:
    payment_id: int
    order_id: int
    order_paid: bool
    requires_manual_review: bool
    reason: str = ""


def request_payment(payment):
    """Request a ZarinPal authority without holding database locks."""
    payment = Payment.objects.select_related("order", "order__user").get(pk=payment.pk)
    if payment.status != Payment.Status.PENDING:
        raise ValidationError("Only pending payments can be requested.")
    if payment.authority:
        return payment

    try:
        result = ZarinPalService().create_payment(payment.order)
    except ZarinPalError as exc:
        raise ValidationError(str(exc)) from exc

    with transaction.atomic():
        locked_payment = Payment.objects.select_for_update().get(pk=payment.pk)
        if locked_payment.authority:
            return locked_payment
        if locked_payment.status != Payment.Status.PENDING:
            raise ValidationError("Only pending payments can be requested.")
        locked_payment.authority = result.authority
        locked_payment.gateway_code = result.code
        locked_payment.gateway_message = result.message[:255]
        locked_payment.gateway_response = result.gateway_response
        locked_payment.save(
            update_fields=(
                "authority",
                "gateway_code",
                "gateway_message",
                "gateway_response",
                "updated_at",
            )
        )
        return locked_payment


def payment_url(payment):
    return ZarinPalService().payment_url(payment.authority)


@transaction.atomic
def record_failed_callback(
    payment_id,
    *,
    callback_status,
    gateway_code=None,
    gateway_message="",
    gateway_response=None,
):
    """Record a definite failure without downgrading paid or fulfilled orders."""
    payment = Payment.objects.select_for_update().get(pk=payment_id)
    order = Order.objects.select_for_update().get(pk=payment.order_id)

    if payment.status == Payment.Status.PAID:
        return payment, order

    payment.status_from_gateway = callback_status
    payment.gateway_code = gateway_code
    payment.gateway_message = gateway_message[:255]
    if gateway_response is not None:
        payment.gateway_response = gateway_response

    if payment.status == Payment.Status.PENDING:
        payment.status = Payment.Status.FAILED

    payment.save(
        update_fields=(
            "status",
            "status_from_gateway",
            "gateway_code",
            "gateway_message",
            "gateway_response",
            "updated_at",
        )
    )

    if order.status in (Order.Status.PENDING, Order.Status.PAYMENT_FAILED):
        order.status = Order.Status.PAYMENT_FAILED
        order.save(update_fields=("status", "updated_at"))
    return payment, order


@transaction.atomic
def record_verification_uncertainty(
    payment_id, *, gateway_message, gateway_response=None
):
    """Persist safe diagnostics while keeping an uncertain payment retryable."""
    payment = Payment.objects.select_for_update().get(pk=payment_id)
    payment.status_from_gateway = "OK"
    payment.gateway_message = gateway_message[:255]
    if gateway_response is not None:
        payment.gateway_response = gateway_response
    payment.save(
        update_fields=(
            "status_from_gateway",
            "gateway_message",
            "gateway_response",
            "updated_at",
        )
    )
    return payment


@transaction.atomic
def finalize_verified_payment(
    payment_id,
    *,
    authority,
    verification: PaymentVerificationResult,
):
    """Finalize verified gateway state exactly once under row locks."""
    payment = Payment.objects.select_for_update().get(pk=payment_id)
    order = Order.objects.select_for_update().get(pk=payment.order_id)
    if payment.authority != authority:
        raise ValidationError("Payment authority does not match.")

    _mark_payment_paid(payment, verification)

    if order.status == Order.Status.CANCELLED:
        _flag_manual_review(order, CANCELLED_ORDER_REVIEW_REASON, keep_status=True)
        logger.critical(
            "Verified payment received for cancelled order.",
            extra={"payment_id": payment.id, "order_id": order.id},
        )
        return PaymentFinalizationResult(
            payment.id,
            order.id,
            order_paid=False,
            requires_manual_review=True,
            reason="order_cancelled",
        )

    fulfillment_statuses = (
        Order.Status.PROCESSING,
        Order.Status.SHIPPED,
        Order.Status.DELIVERED,
    )
    if order.status in fulfillment_statuses and not order.stock_reduced:
        _flag_manual_review(order, INCONSISTENT_ORDER_REVIEW_REASON, keep_status=True)
        logger.critical(
            "Verified payment found fulfillment order without reduced stock.",
            extra={"payment_id": payment.id, "order_id": order.id},
        )
        return PaymentFinalizationResult(
            payment.id,
            order.id,
            order_paid=True,
            requires_manual_review=True,
            reason="manual_review",
        )

    try:
        finalized_order = mark_order_as_paid(order)
    except ValidationError:
        _flag_manual_review(order, INVENTORY_REVIEW_REASON, keep_status=False)
        logger.critical(
            "Verified payment could not be finalized because stock was insufficient.",
            extra={"payment_id": payment.id, "order_id": order.id},
        )
        return PaymentFinalizationResult(
            payment.id,
            order.id,
            order_paid=True,
            requires_manual_review=True,
            reason="manual_review",
        )

    if finalized_order.requires_manual_review or finalized_order.manual_review_reason:
        finalized_order.requires_manual_review = False
        finalized_order.manual_review_reason = ""
        finalized_order.save(
            update_fields=(
                "requires_manual_review",
                "manual_review_reason",
                "updated_at",
            )
        )

    _finalize_cart(payment, finalized_order)
    return PaymentFinalizationResult(
        payment.id,
        finalized_order.id,
        order_paid=True,
        requires_manual_review=False,
    )


def _mark_payment_paid(payment, verification):
    now = timezone.now()
    payment.status = Payment.Status.PAID
    payment.status_from_gateway = "OK"
    payment.gateway_code = verification.code
    payment.gateway_message = verification.message[:255]
    payment.ref_id = verification.ref_id
    payment.card_pan = verification.card_pan
    payment.card_hash = verification.card_hash
    payment.fee = verification.fee
    payment.fee_type = verification.fee_type
    payment.gateway_response = verification.gateway_response
    payment.paid_at = payment.paid_at or now
    payment.verified_at = payment.verified_at or now
    payment.save(
        update_fields=(
            "status",
            "status_from_gateway",
            "gateway_code",
            "gateway_message",
            "ref_id",
            "card_pan",
            "card_hash",
            "fee",
            "fee_type",
            "gateway_response",
            "paid_at",
            "verified_at",
            "updated_at",
        )
    )


def _flag_manual_review(order, reason, *, keep_status):
    if not keep_status:
        order.status = Order.Status.PAID
    order.requires_manual_review = True
    order.manual_review_reason = reason
    order.save(
        update_fields=(
            "status",
            "requires_manual_review",
            "manual_review_reason",
            "updated_at",
        )
    )


def _finalize_cart(payment, order):
    if payment.cart_finalized:
        return

    purchased_quantities = Counter()
    for item in order.items.all():
        purchased_quantities[item.product_id] += item.quantity

    cart = Cart.objects.select_for_update().filter(user_id=order.user_id).first()
    if cart:
        cart_items = {
            item.product_id: item
            for item in CartItem.objects.select_for_update().filter(
                cart=cart,
                product_id__in=purchased_quantities,
            )
        }
        for product_id, purchased_quantity in purchased_quantities.items():
            cart_item = cart_items.get(product_id)
            if cart_item is None:
                continue
            if cart_item.quantity <= purchased_quantity:
                cart_item.delete()
            else:
                cart_item.quantity -= purchased_quantity
                cart_item.save(update_fields=("quantity",))

    payment.cart_finalized = True
    payment.save(update_fields=("cart_finalized", "updated_at"))
