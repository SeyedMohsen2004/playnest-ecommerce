from django.contrib import admin

from payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer_phone",
        "order",
        "gateway",
        "amount",
        "status",
        "authority",
        "ref_id",
        "created_at",
        "paid_at",
    )
    search_fields = (
        "authority",
        "ref_id",
        "user__phone_number",
        "user__email",
        "order__id",
    )
    list_filter = ("gateway", "status", "created_at", "paid_at")
    list_select_related = ("order", "user")
    readonly_fields = (
        "authority",
        "ref_id",
        "gateway_response",
        "created_at",
        "updated_at",
        "paid_at",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    autocomplete_fields = ("user", "order")
    fieldsets = (
        (
            "Payment",
            {
                "fields": (
                    "user",
                    "order",
                    "gateway",
                    "amount",
                    "status",
                )
            },
        ),
        ("Gateway tracking", {"fields": ("authority", "ref_id", "card_pan")}),
        ("Gateway response", {"fields": ("gateway_response",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at", "paid_at")}),
    )

    @admin.display(description="Customer phone", ordering="user__phone_number")
    def customer_phone(self, obj):
        return obj.user.phone_number
