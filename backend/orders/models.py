from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from products.models import Product


class Coupon(models.Model):
    class DiscountType(models.TextChoices):
        PERCENTAGE = "percentage", "Percentage"
        FIXED = "fixed", "Fixed"

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DiscountType.choices)
    discount_value = models.PositiveIntegerField()
    max_discount_amount = models.PositiveIntegerField(blank=True, null=True)
    min_order_amount = models.PositiveIntegerField(default=0)
    usage_limit = models.PositiveIntegerField(blank=True, null=True)
    used_count = models.PositiveIntegerField(default=0)
    starts_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("code",)
        constraints = [
            models.CheckConstraint(
                condition=models.Q(discount_type="fixed")
                | models.Q(discount_value__lte=100),
                name="coupon_percentage_maximum_100",
            )
        ]

    def __str__(self):
        return self.code

    def clean(self):
        super().clean()
        if (
            self.discount_type == self.DiscountType.PERCENTAGE
            and self.discount_value > 100
        ):
            raise ValidationError(
                {"discount_value": "Percentage discount cannot exceed 100."}
            )


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
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.PROTECT,
        related_name="orders",
        blank=True,
        null=True,
    )
    subtotal_amount = models.PositiveBigIntegerField(default=0)
    discount_amount = models.PositiveBigIntegerField(default=0)
    shipping_cost = models.PositiveBigIntegerField(default=0)
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
