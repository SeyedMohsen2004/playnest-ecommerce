from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from orders.models import (
    Cart,
    CartItem,
    Coupon,
    CouponRedemption,
    Order,
    OrderItem,
)
from orders.pricing import calculate_order_totals, get_shipping_cost, validate_coupon
from products.models import Product


class OrderCancellationNotAllowed(Exception):
    pass


class ShippingUpdateNotAllowed(Exception):
    pass


class InventoryUnavailable(ValidationError):
    pass


class CouponCapacityUnavailable(ValidationError):
    pass


class CouponRedemptionInconsistent(ValidationError):
    pass


@dataclass(frozen=True)
class CancellationResult:
    order: Order
    cancelled: bool
    already_cancelled: bool


def lock_order_and_payments(order_id):
    """Lock an order, then every related payment in primary-key order.

    Commerce transactions use the canonical lock order documented in
    ``docs/commerce-domain.md``: Order, Payments, Cart, Coupon, redemption,
    Products, then CartItems. Callers must already be inside ``atomic()``.
    """
    from payments.models import Payment

    order = Order.objects.select_for_update().get(pk=order_id)
    payments = list(
        Payment.objects.select_for_update().filter(order_id=order.id).order_by("pk")
    )
    return order, payments


def lock_order_and_payments_for_payment(payment_id):
    from payments.models import Payment

    order_id = Payment.objects.only("order_id").get(pk=payment_id).order_id
    order, payments = lock_order_and_payments(order_id)
    payment = next(
        (candidate for candidate in payments if candidate.pk == payment_id),
        None,
    )
    if payment is None:
        raise Payment.DoesNotExist
    return order, payments, payment


def lock_user_cart(user_id):
    return Cart.objects.select_for_update().filter(user_id=user_id).first()


def lock_cart_items(cart, product_ids):
    if cart is None or not product_ids:
        return []
    return list(
        CartItem.objects.select_for_update()
        .filter(cart=cart, product_id__in=product_ids)
        .order_by("pk")
    )


def lock_coupon_redemption(order):
    if not order.coupon_id:
        return None, None
    coupon = Coupon.objects.select_for_update().get(pk=order.coupon_id)
    redemption = (
        CouponRedemption.objects.select_for_update().filter(order_id=order.id).first()
    )
    if redemption is not None and redemption.coupon_id != coupon.id:
        raise CouponRedemptionInconsistent(
            {"coupon": "Coupon reservation is inconsistent."}
        )
    return coupon, redemption


def _reserved_coupon_count(coupon):
    return CouponRedemption.objects.filter(
        coupon=coupon,
        state=CouponRedemption.State.RESERVED,
    ).count()


def ensure_coupon_capacity_for_reservation(coupon):
    if coupon.usage_limit is None:
        return
    allocated = coupon.used_count + _reserved_coupon_count(coupon)
    if allocated >= coupon.usage_limit:
        raise CouponCapacityUnavailable(
            {"coupon": "Coupon usage limit has been reached."}
        )


def ensure_coupon_can_be_consumed(coupon, redemption):
    if coupon is None or (
        redemption is not None and redemption.state == CouponRedemption.State.CONSUMED
    ):
        return
    if redemption is not None and redemption.state != CouponRedemption.State.RESERVED:
        raise CouponRedemptionInconsistent(
            {"coupon": "Coupon reservation is no longer available."}
        )
    if coupon.usage_limit is None:
        return
    if redemption is not None:
        has_capacity = coupon.used_count < coupon.usage_limit
    else:
        has_capacity = (
            coupon.used_count + _reserved_coupon_count(coupon) < coupon.usage_limit
        )
    if not has_capacity:
        raise CouponCapacityUnavailable(
            {"coupon": "Coupon usage limit has been reached."}
        )


def consume_coupon(order, coupon, redemption):
    if coupon is None:
        return None
    if redemption is not None and redemption.state == CouponRedemption.State.CONSUMED:
        return redemption

    coupon.used_count += 1
    coupon.save(update_fields=("used_count", "updated_at"))
    if redemption is None:
        return CouponRedemption.objects.create(
            coupon=coupon,
            order=order,
            state=CouponRedemption.State.CONSUMED,
        )
    redemption.state = CouponRedemption.State.CONSUMED
    redemption.save(update_fields=("state", "updated_at"))
    return redemption


def _lock_order_products(order):
    order_items = list(order.items.order_by("pk"))
    product_ids = sorted({item.product_id for item in order_items})
    products = list(
        Product.objects.select_for_update().filter(pk__in=product_ids).order_by("pk")
    )
    return order_items, {product.pk: product for product in products}


def _validate_locked_stock(order_items, products):
    errors = []
    for item in order_items:
        product = products.get(item.product_id)
        if product is None or item.quantity > product.stock:
            errors.append(f"Insufficient stock for {item.product_name}.")
    if errors:
        raise InventoryUnavailable({"stock": errors})


def finalize_locked_order_inventory(order):
    """Consume coupon capacity and stock once for an already locked order.

    The caller must hold the order and related payment locks. If cart state is
    also involved, the caller must lock the cart before entering this function.
    """
    if order.stock_reduced:
        return order

    coupon, redemption = lock_coupon_redemption(order)
    ensure_coupon_can_be_consumed(coupon, redemption)
    order_items, products = _lock_order_products(order)
    _validate_locked_stock(order_items, products)

    for item in order_items:
        product = products[item.product_id]
        product.stock -= item.quantity
        product.save(update_fields=("stock",))

    consume_coupon(order, coupon, redemption)
    order.stock_reduced = True
    order.status = Order.Status.PAID
    order.save(update_fields=("stock_reduced", "status", "updated_at"))
    return order


@transaction.atomic
def checkout_cart(
    *,
    user,
    shipping_address,
    postal_code,
    recipient_name,
    recipient_phone,
    shipping_zone,
    coupon_code="",
):
    cart = lock_user_cart(user.id)
    if cart is None:
        raise ValidationError("Cart is empty.")

    item_snapshot = list(
        CartItem.objects.filter(cart=cart).order_by("pk").values("pk", "product_id")
    )
    if not item_snapshot:
        raise ValidationError("Cart is empty.")

    shipping_cost = get_shipping_cost(shipping_zone, for_update=True)

    coupon = None
    normalized_coupon_code = coupon_code.strip()
    if normalized_coupon_code:
        coupon = (
            Coupon.objects.select_for_update()
            .filter(code__iexact=normalized_coupon_code)
            .order_by("pk")
            .first()
        )
        if coupon is None:
            raise ValidationError({"coupon_code": "Coupon was not found."})

    product_ids = sorted({item["product_id"] for item in item_snapshot})
    products = {
        product.pk: product
        for product in Product.objects.select_for_update()
        .filter(pk__in=product_ids)
        .order_by("pk")
    }
    snapshot_item_ids = [item["pk"] for item in item_snapshot]
    cart_items = list(
        CartItem.objects.select_for_update()
        .filter(cart=cart, pk__in=snapshot_item_ids)
        .order_by("pk")
    )
    if len(cart_items) != len(item_snapshot):
        raise ValidationError({"cart": "Cart changed during checkout. Try again."})

    subtotal_amount = 0
    order_lines = []
    for item in cart_items:
        product = products.get(item.product_id)
        if product is None:
            raise ValidationError(
                {"cart": "A product in the cart is no longer available."}
            )
        if not product.is_active:
            raise ValidationError({"cart": f"{product.name} is inactive."})
        if item.quantity > product.stock:
            raise ValidationError({"cart": f"Insufficient stock for {product.name}."})
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
                "cart_item_id_snapshot": item.pk,
            }
        )

    if coupon is not None:
        validate_coupon(coupon, subtotal_amount)
        ensure_coupon_capacity_for_reservation(coupon)
    totals = calculate_order_totals(
        subtotal_amount,
        coupon,
        shipping_cost=shipping_cost,
    )

    order = Order.objects.create(
        user=user,
        coupon=coupon,
        shipping_zone=shipping_zone,
        subtotal_amount=totals["subtotal"],
        discount_amount=totals["discount_amount"],
        shipping_cost=totals["shipping_cost"],
        total_amount=totals["total_amount"],
        shipping_address=shipping_address,
        postal_code=postal_code,
        recipient_name=recipient_name,
        recipient_phone=recipient_phone,
    )
    OrderItem.objects.bulk_create(
        [OrderItem(order=order, **line) for line in order_lines]
    )
    if coupon is not None:
        CouponRedemption.objects.create(
            coupon=coupon,
            order=order,
            state=CouponRedemption.State.RESERVED,
        )
    return order


@transaction.atomic
def cancel_order(order_id):
    from payments.models import Payment

    order, payments = lock_order_and_payments(order_id)
    if order.status == Order.Status.CANCELLED:
        return CancellationResult(order, cancelled=False, already_cancelled=True)
    if (
        order.status not in (Order.Status.PENDING, Order.Status.PAYMENT_FAILED)
        or order.stock_reduced
        or order.requires_manual_review
        or any(payment.status == Payment.Status.PAID for payment in payments)
    ):
        raise OrderCancellationNotAllowed

    _coupon, redemption = lock_coupon_redemption(order)
    now = timezone.now()
    pending_payments = [
        payment for payment in payments if payment.status == Payment.Status.PENDING
    ]
    for payment in pending_payments:
        payment.status = Payment.Status.CANCELLED
        payment.updated_at = now
    if pending_payments:
        Payment.objects.bulk_update(pending_payments, ("status", "updated_at"))

    if redemption is not None and redemption.state == CouponRedemption.State.RESERVED:
        redemption.state = CouponRedemption.State.RELEASED
        redemption.save(update_fields=("state", "updated_at"))

    order.status = Order.Status.CANCELLED
    order.save(update_fields=("status", "updated_at"))
    return CancellationResult(order, cancelled=True, already_cancelled=False)


@transaction.atomic
def update_order_shipping(order_id, validated_data):
    order = Order.objects.select_for_update().get(pk=order_id)
    if order.status not in (
        Order.Status.PENDING,
        Order.Status.PAYMENT_FAILED,
        Order.Status.PAID,
    ):
        raise ShippingUpdateNotAllowed
    for field, value in validated_data.items():
        setattr(order, field, value)
    if validated_data:
        order.save(update_fields=(*validated_data.keys(), "updated_at"))
    return order


@transaction.atomic
def mark_order_as_paid(order):
    locked_order, _payments = lock_order_and_payments(order.pk)
    finalized_order = finalize_locked_order_inventory(locked_order)
    order.stock_reduced = finalized_order.stock_reduced
    order.status = finalized_order.status
    return finalized_order
