from django.core.exceptions import ValidationError
from django.utils import timezone

from orders.models import Coupon, Order, ShippingSettings

COUPON_UNAVAILABLE_MESSAGE = (
    "کد تخفیف واردشده معتبر نیست یا در حال حاضر قابل استفاده نیست."
)


def validate_coupon(coupon, subtotal):
    now = timezone.now()
    if not coupon.is_active:
        raise ValidationError({"coupon": COUPON_UNAVAILABLE_MESSAGE})
    if coupon.starts_at and now < coupon.starts_at:
        raise ValidationError({"coupon": COUPON_UNAVAILABLE_MESSAGE})
    if coupon.expires_at and now >= coupon.expires_at:
        raise ValidationError({"coupon": COUPON_UNAVAILABLE_MESSAGE})
    if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
        raise ValidationError({"coupon": COUPON_UNAVAILABLE_MESSAGE})
    if subtotal < coupon.min_order_amount:
        raise ValidationError(
            {"coupon": "مبلغ سفارش به حداقل لازم برای استفاده از این کد نرسیده است."}
        )
    if (
        coupon.discount_type == Coupon.DiscountType.PERCENTAGE
        and coupon.discount_value > 100
    ):
        raise ValidationError({"coupon": COUPON_UNAVAILABLE_MESSAGE})
    if (
        coupon.discount_type == Coupon.DiscountType.FIXED
        and coupon.discount_value > subtotal
    ):
        raise ValidationError({"coupon": COUPON_UNAVAILABLE_MESSAGE})
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


def get_shipping_cost(shipping_zone, *, for_update=False):
    settings_obj = ShippingSettings.load(for_update=for_update)
    if shipping_zone == Order.ShippingZone.TABRIZ:
        return settings_obj.tabriz_shipping_fee
    if shipping_zone == Order.ShippingZone.NATIONWIDE:
        return settings_obj.nationwide_shipping_fee
    raise ValidationError({"shipping_zone": "Select a valid shipping zone."})


def calculate_order_totals(subtotal, coupon=None, *, shipping_cost=0):
    discount_amount = calculate_discount(coupon, subtotal)
    discounted_subtotal = subtotal - discount_amount
    return {
        "subtotal": subtotal,
        "discount_amount": discount_amount,
        "shipping_cost": shipping_cost,
        "total_amount": discounted_subtotal + shipping_cost,
    }
