import logging
from collections import Counter
from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from orders.models import CouponRedemption, Order
from orders.services import (
    CouponCapacityUnavailable,
    CouponRedemptionInconsistent,
    InventoryUnavailable,
    ensure_coupon_capacity_for_reservation,
    finalize_locked_order_inventory,
    lock_cart_items,
    lock_coupon_redemption,
    lock_order_and_payments,
    lock_order_and_payments_for_payment,
    lock_user_cart,
)
from payments.models import Payment
from payments.services.zarinpal import (
    PaymentVerificationResult,
    ZarinPalError,
    ZarinPalService,
)
from products.models import Product

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
COUPON_REVIEW_REASON = (
    "Verified payment completed, but its coupon capacity was no longer safely "
    "available during finalization."
)
COUPON_REDEMPTION_REVIEW_REASON = (
    "Verified payment completed, but its coupon reservation was inconsistent."
)
LOCAL_CONSTRAINT_REVIEW_REASON = (
    "Verified payment completed, but a local finalization constraint failed."
)
LOCAL_VALIDATION_REVIEW_REASON = (
    "Verified payment completed, but local finalization validation failed."
)
MULTIPLE_PAID_PAYMENTS_REVIEW_REASON = (
    "More than one payment attempt for this order has verified as paid."
)
VERIFICATION_CONFLICT_REVIEW_REASON = (
    "A repeated gateway verification returned data that conflicts with the "
    "already stored verified payment."
)

RECOVERABLE_REVIEW_REASONS = frozenset(
    {
        INVENTORY_REVIEW_REASON,
        COUPON_REVIEW_REASON,
    }
)
REVIEW_REASON_PRIORITY = {
    INVENTORY_REVIEW_REASON: 10,
    COUPON_REVIEW_REASON: 10,
    LOCAL_VALIDATION_REVIEW_REASON: 30,
    LOCAL_CONSTRAINT_REVIEW_REASON: 40,
    COUPON_REDEMPTION_REVIEW_REASON: 50,
    INCONSISTENT_ORDER_REVIEW_REASON: 60,
    CANCELLED_ORDER_REVIEW_REASON: 70,
    MULTIPLE_PAID_PAYMENTS_REVIEW_REASON: 80,
    VERIFICATION_CONFLICT_REVIEW_REASON: 90,
}


class PaymentStockUnavailable(Exception):
    def __init__(self, items):
        self.items = items
        super().__init__("Order stock is unavailable.")


@dataclass(frozen=True)
class PaymentFinalizationResult:
    payment_id: int
    order_id: int
    order_paid: bool
    requires_manual_review: bool
    reason: str = ""


@transaction.atomic
def prepare_payment_attempt(order_id):
    """Create or reuse a pending attempt after rechecking locked order state."""
    order, payments = lock_order_and_payments(order_id)
    if order.status not in (Order.Status.PENDING, Order.Status.PAYMENT_FAILED):
        raise ValidationError("این سفارش در وضعیت قابل پرداخت نیست.")

    coupon, redemption = lock_coupon_redemption(order)
    if coupon is not None:
        if redemption is None:
            ensure_coupon_capacity_for_reservation(coupon)
            redemption = CouponRedemption.objects.create(
                coupon=coupon,
                order=order,
                state=CouponRedemption.State.RESERVED,
            )
        elif redemption.state != CouponRedemption.State.RESERVED:
            raise CouponCapacityUnavailable(
                {"coupon": "Coupon reservation is no longer available."}
            )

    order_items = list(order.items.order_by("pk"))
    product_ids = sorted({item.product_id for item in order_items})
    products = {
        product.pk: product
        for product in Product.objects.select_for_update()
        .filter(pk__in=product_ids)
        .order_by("pk")
    }
    stock_errors = []
    for item in order_items:
        product = products.get(item.product_id)
        if product is None or not product.is_active or product.stock < item.quantity:
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
        raise PaymentStockUnavailable(stock_errors)

    payment = next(
        (
            candidate
            for candidate in payments
            if candidate.status == Payment.Status.PENDING
        ),
        None,
    )
    if payment is None:
        payment = Payment.objects.create(
            user=order.user,
            order=order,
            amount=order.total_amount,
        )
    return payment


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
        order, _payments, locked_payment = lock_order_and_payments_for_payment(
            payment.pk
        )
        if locked_payment.authority:
            return locked_payment
        if locked_payment.status != Payment.Status.PENDING or order.status not in (
            Order.Status.PENDING,
            Order.Status.PAYMENT_FAILED,
        ):
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
    order, payments, payment = lock_order_and_payments_for_payment(payment_id)

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

    has_paid_payment = any(
        candidate.status == Payment.Status.PAID for candidate in payments
    )
    if not has_paid_payment and order.status in (
        Order.Status.PENDING,
        Order.Status.PAYMENT_FAILED,
    ):
        order.status = Order.Status.PAYMENT_FAILED
        order.save(update_fields=("status", "updated_at"))
    return payment, order


@transaction.atomic
def record_verification_uncertainty(
    payment_id, *, gateway_message, gateway_response=None
):
    """Persist safe diagnostics while keeping an uncertain payment retryable."""
    _order, _payments, payment = lock_order_and_payments_for_payment(payment_id)
    if payment.status == Payment.Status.PAID:
        return payment
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
    order, payments, payment = lock_order_and_payments_for_payment(payment_id)
    if payment.authority != authority:
        raise ValidationError("Payment authority does not match.")

    previously_verified = (
        payment.status == Payment.Status.PAID and payment.verified_at is not None
    )
    if previously_verified:
        if (
            payment.ref_id
            and verification.ref_id
            and payment.ref_id != verification.ref_id
        ):
            _flag_manual_review(
                order,
                VERIFICATION_CONFLICT_REVIEW_REASON,
                keep_status=True,
            )
            logger.critical(
                "Repeated verification conflicted with stored paid evidence.",
                extra={"payment_id": payment.id, "order_id": order.id},
            )
            return PaymentFinalizationResult(
                payment.id,
                order.id,
                order_paid=order.status != Order.Status.CANCELLED,
                requires_manual_review=True,
                reason="manual_review",
            )
    else:
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

    other_paid_payments = [
        candidate
        for candidate in payments
        if candidate.pk != payment.pk and candidate.status == Payment.Status.PAID
    ]
    if other_paid_payments:
        _flag_manual_review(
            order,
            MULTIPLE_PAID_PAYMENTS_REVIEW_REASON,
            keep_status=order.status
            in (Order.Status.PROCESSING, Order.Status.SHIPPED, Order.Status.DELIVERED),
        )
        logger.critical(
            "Multiple payment attempts verified for one order.",
            extra={"payment_id": payment.id, "order_id": order.id},
        )
        return PaymentFinalizationResult(
            payment.id,
            order.id,
            order_paid=True,
            requires_manual_review=True,
            reason="manual_review",
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

    existing_review_reason = (
        order.manual_review_reason if order.requires_manual_review else ""
    )
    stock_was_reduced = order.stock_reduced
    try:
        with transaction.atomic():
            cart = lock_user_cart(order.user_id)
            finalized_order = finalize_locked_order_inventory(order)
            _finalize_cart(payment, finalized_order, payments, cart)
    except CouponCapacityUnavailable:
        order.refresh_from_db()
        _flag_manual_review(order, COUPON_REVIEW_REASON, keep_status=False)
        logger.critical(
            "Verified payment could not consume its coupon reservation.",
            extra={"payment_id": payment.id, "order_id": order.id},
        )
        return PaymentFinalizationResult(
            payment.id,
            order.id,
            order_paid=True,
            requires_manual_review=True,
            reason="manual_review",
        )
    except CouponRedemptionInconsistent:
        order.refresh_from_db()
        _flag_manual_review(
            order,
            COUPON_REDEMPTION_REVIEW_REASON,
            keep_status=False,
        )
        logger.critical(
            "Verified payment found an inconsistent coupon reservation.",
            extra={"payment_id": payment.id, "order_id": order.id},
        )
        return PaymentFinalizationResult(
            payment.id,
            order.id,
            order_paid=True,
            requires_manual_review=True,
            reason="manual_review",
        )
    except InventoryUnavailable:
        order.refresh_from_db()
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
    except IntegrityError:
        order.refresh_from_db()
        _flag_manual_review(order, LOCAL_CONSTRAINT_REVIEW_REASON, keep_status=False)
        logger.exception(
            "Verified payment local finalization hit a database constraint.",
            extra={"payment_id": payment.id, "order_id": order.id},
        )
        return PaymentFinalizationResult(
            payment.id,
            order.id,
            order_paid=True,
            requires_manual_review=True,
            reason="manual_review",
        )
    except ValidationError:
        order.refresh_from_db()
        _flag_manual_review(order, LOCAL_VALIDATION_REVIEW_REASON, keep_status=False)
        logger.exception(
            "Verified payment local finalization validation was unexpected.",
            extra={"payment_id": payment.id, "order_id": order.id},
        )
        return PaymentFinalizationResult(
            payment.id,
            order.id,
            order_paid=True,
            requires_manual_review=True,
            reason="manual_review",
        )

    if (
        existing_review_reason in RECOVERABLE_REVIEW_REASONS
        and not stock_was_reduced
        and finalized_order.stock_reduced
        and payment.cart_finalized
        and finalized_order.requires_manual_review
        and finalized_order.manual_review_reason == existing_review_reason
    ):
        finalized_order.requires_manual_review = False
        finalized_order.manual_review_reason = ""
        finalized_order.save(
            update_fields=(
                "requires_manual_review",
                "manual_review_reason",
                "updated_at",
            )
        )

    return PaymentFinalizationResult(
        payment.id,
        finalized_order.id,
        order_paid=True,
        requires_manual_review=finalized_order.requires_manual_review,
        reason=("manual_review" if finalized_order.requires_manual_review else ""),
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
    existing_reason = order.manual_review_reason if order.requires_manual_review else ""
    existing_priority = REVIEW_REASON_PRIORITY.get(existing_reason, float("inf"))
    new_priority = REVIEW_REASON_PRIORITY[reason]
    if not existing_reason or new_priority > existing_priority:
        order.manual_review_reason = reason
    order.requires_manual_review = True
    order.save(
        update_fields=(
            "status",
            "requires_manual_review",
            "manual_review_reason",
            "updated_at",
        )
    )


def _finalize_cart(payment, order, locked_payments, cart):
    if payment.cart_finalized:
        return

    if any(
        candidate.pk != payment.pk and candidate.cart_finalized
        for candidate in locked_payments
    ):
        payment.cart_finalized = True
        payment.save(update_fields=("cart_finalized", "updated_at"))
        return

    purchased_quantities = Counter()
    cart_item_snapshots = {}
    for item in order.items.order_by("pk"):
        purchased_quantities[item.product_id] += item.quantity
        if item.product_id not in cart_item_snapshots:
            cart_item_snapshots[item.product_id] = item.cart_item_id_snapshot
        elif cart_item_snapshots[item.product_id] != item.cart_item_id_snapshot:
            cart_item_snapshots[item.product_id] = None

    if cart:
        cart_items = {
            item.product_id: item
            for item in lock_cart_items(cart, purchased_quantities)
        }
        for product_id, purchased_quantity in purchased_quantities.items():
            cart_item = cart_items.get(product_id)
            if cart_item is None:
                continue
            snapshot_id = cart_item_snapshots.get(product_id)
            if snapshot_id is None or cart_item.pk != snapshot_id:
                continue
            if cart_item.quantity <= purchased_quantity:
                cart_item.delete()
            else:
                cart_item.quantity -= purchased_quantity
                cart_item.save(update_fields=("quantity",))

    payment.cart_finalized = True
    payment.save(update_fields=("cart_finalized", "updated_at"))
