from django.core.exceptions import ValidationError
from django.utils import timezone

from orders.models import Coupon

FIXED_SHIPPING_COST = 50_000
FREE_SHIPPING_THRESHOLD = 1_500_000


def validate_coupon(coupon, subtotal):
    now = timezone.now()
    if not coupon.is_active:
        raise ValidationError({"coupon": "Coupon is inactive."})
    if coupon.starts_at and now < coupon.starts_at:
        raise ValidationError({"coupon": "Coupon is not active yet."})
    if coupon.expires_at and now >= coupon.expires_at:
        raise ValidationError({"coupon": "Coupon has expired."})
    if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
        raise ValidationError({"coupon": "Coupon usage limit has been reached."})
    if subtotal < coupon.min_order_amount:
        raise ValidationError(
            {"coupon": "Order amount does not meet the coupon minimum."}
        )
    if (
        coupon.discount_type == Coupon.DiscountType.PERCENTAGE
        and coupon.discount_value > 100
    ):
        raise ValidationError({"coupon": "Percentage discount cannot exceed 100."})
    if (
        coupon.discount_type == Coupon.DiscountType.FIXED
        and coupon.discount_value > subtotal
    ):
        raise ValidationError({"coupon": "Fixed discount cannot exceed order total."})
    return coupon


def calculate_discount(coupon, subtotal):
    if coupon is None:
        return 0
    validate_coupon(coupon, subtotal)
    if coupon.discount_type == Coupon.DiscountType.PERCENTAGE:
        discount = subtotal * coupon.discount_value // 100
    else:
        discount = coupon.discount_value
    if coupon.max_discount_amount is not None:
        discount = min(discount, coupon.max_discount_amount)
    return discount


def calculate_order_totals(subtotal, coupon=None):
    discount_amount = calculate_discount(coupon, subtotal)
    discounted_subtotal = subtotal - discount_amount
    shipping_cost = (
        0 if discounted_subtotal >= FREE_SHIPPING_THRESHOLD else FIXED_SHIPPING_COST
    )
    return {
        "subtotal": subtotal,
        "discount_amount": discount_amount,
        "shipping_cost": shipping_cost,
        "total_amount": discounted_subtotal + shipping_cost,
    }
