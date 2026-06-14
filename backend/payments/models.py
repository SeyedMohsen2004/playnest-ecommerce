from django.conf import settings
from django.db import models
from django.db.models import Q

from orders.models import Order


class Payment(models.Model):
    class Gateway(models.TextChoices):
        ZARINPAL = "zarinpal", "ZarinPal"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    gateway = models.CharField(
        max_length=20,
        choices=Gateway.choices,
        default=Gateway.ZARINPAL,
    )
    amount = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    authority = models.CharField(max_length=100, blank=True, null=True, unique=True)
    ref_id = models.CharField(max_length=100, blank=True, null=True)
    card_pan = models.CharField(max_length=30, blank=True, null=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("order",),
                condition=Q(status="pending"),
                name="unique_pending_payment_per_order",
            )
        ]

    def __str__(self):
        return f"Payment #{self.pk} for order #{self.order_id}"
