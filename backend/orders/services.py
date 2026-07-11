from django.core.exceptions import ValidationError
from django.db import transaction

from orders.models import Coupon, Order
from orders.pricing import validate_coupon
from products.models import Product, ProductOptionValue


@transaction.atomic
def mark_order_as_paid(order):
    locked_order = Order.objects.select_for_update().get(pk=order.pk)
    if locked_order.stock_reduced or locked_order.status == Order.Status.PAID:
        return locked_order

    order_items = list(locked_order.items.select_related("product").all())
    products = {
        product.id: product
        for product in Product.objects.select_for_update().filter(
            id__in=[
                item.product_id
                for item in order_items
                if not item.selected_option_value_ids_snapshot
            ]
        )
    }
    option_values = {
        value.id: value
        for value in ProductOptionValue.objects.select_for_update().filter(
            id__in=[
                value_id
                for item in order_items
                for value_id in item.selected_option_value_ids_snapshot
            ]
        )
    }

    errors = []
    for item in order_items:
        if item.selected_option_value_ids_snapshot:
            for value_id in item.selected_option_value_ids_snapshot:
                option_value = option_values.get(value_id)
                if option_value is None or item.quantity > option_value.stock:
                    errors.append(f"Insufficient stock for {item.product_name}.")
            continue

        product = products.get(item.product_id)
        if product is None or item.quantity > product.stock:
            errors.append(f"Insufficient stock for {item.product_name}.")
    if errors:
        raise ValidationError({"stock": errors})

    for item in order_items:
        if item.selected_option_value_ids_snapshot:
            for value_id in item.selected_option_value_ids_snapshot:
                option_value = option_values[value_id]
                option_value.stock -= item.quantity
                option_value.save(update_fields=("stock", "updated_at"))
            continue

        product = products[item.product_id]
        product.stock -= item.quantity
        product.save(update_fields=("stock",))

    if locked_order.coupon_id:
        coupon = Coupon.objects.select_for_update().get(pk=locked_order.coupon_id)
        validate_coupon(coupon, locked_order.subtotal_amount)
        coupon.used_count += 1
        coupon.save(update_fields=("used_count", "updated_at"))

    locked_order.stock_reduced = True
    locked_order.status = Order.Status.PAID
    locked_order.save(update_fields=("stock_reduced", "status", "updated_at"))
    order.stock_reduced = locked_order.stock_reduced
    order.status = locked_order.status
    return locked_order
