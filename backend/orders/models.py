from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from products.models import Product


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user}"

    @property
    def subtotal(self):
        return sum(item.subtotal for item in self.items.select_related("product"))

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    quantity = models.PositiveIntegerField(validators=(MinValueValidator(1),))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("cart", "product"),
                name="unique_product_per_cart",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1),
                name="cart_item_quantity_minimum_one",
            ),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.product}"

    def clean(self):
        super().clean()
        errors = {}
        if not self.product.is_active:
            errors["product"] = "Inactive products cannot be added to a cart."
        if self.quantity > self.product.stock:
            errors["quantity"] = "Quantity cannot exceed available stock."
        if errors:
            raise ValidationError(errors)

    @property
    def subtotal(self):
        return self.product.final_price * self.quantity


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    stock_reduced = models.BooleanField(default=False)
    total_amount = models.PositiveBigIntegerField(default=0)
    shipping_address = models.TextField()
    postal_code = models.CharField(max_length=20)
    recipient_name = models.CharField(max_length=255)
    recipient_phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Order #{self.pk}"

    def mark_as_paid(self):
        from orders.services import mark_order_as_paid

        return mark_order_as_paid(self)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    product_name = models.CharField(max_length=255)
    product_price = models.PositiveBigIntegerField()
    quantity = models.PositiveIntegerField(validators=(MinValueValidator(1),))
    line_total = models.PositiveBigIntegerField()

    class Meta:
        ordering = ("id",)

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"
