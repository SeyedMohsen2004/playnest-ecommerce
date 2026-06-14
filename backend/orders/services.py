from django.core.exceptions import ValidationError
from django.db import transaction

from orders.models import Order
from products.models import Product


@transaction.atomic
def mark_order_as_paid(order):
    locked_order = Order.objects.select_for_update().get(pk=order.pk)
    if locked_order.stock_reduced or locked_order.status == Order.Status.PAID:
        return locked_order

    order_items = list(locked_order.items.all())
    products = {
        product.id: product
        for product in Product.objects.select_for_update().filter(
            id__in=[item.product_id for item in order_items]
        )
    }

    errors = []
    for item in order_items:
        product = products.get(item.product_id)
        if product is None or item.quantity > product.stock:
            errors.append(f"Insufficient stock for {item.product_name}.")
    if errors:
        raise ValidationError({"stock": errors})

    for item in order_items:
        product = products[item.product_id]
        product.stock -= item.quantity
        product.save(update_fields=("stock",))

    locked_order.stock_reduced = True
    locked_order.status = Order.Status.PAID
    locked_order.save(update_fields=("stock_reduced", "status", "updated_at"))
    order.stock_reduced = locked_order.stock_reduced
    order.status = locked_order.status
    return locked_order
