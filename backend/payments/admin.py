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
        "status_from_gateway",
        "gateway_code",
        "authority",
        "ref_id",
        "created_at",
        "verified_at",
    )
    search_fields = (
        "authority",
        "status_from_gateway",
        "ref_id",
        "user__phone_number",
        "user__email",
        "order__id",
    )
    list_filter = ("gateway", "status", "gateway_code", "created_at", "verified_at")
    list_select_related = ("order", "user")
    readonly_fields = (
        "authority",
        "status_from_gateway",
        "gateway_code",
        "gateway_message",
        "ref_id",
        "card_pan",
        "card_hash",
        "fee",
        "fee_type",
        "gateway_response",
        "cart_finalized",
        "created_at",
        "updated_at",
        "paid_at",
        "verified_at",
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
        (
            "Gateway tracking",
            {
                "fields": (
                    "authority",
                    "status_from_gateway",
                    "gateway_code",
                    "gateway_message",
                    "ref_id",
                    "card_pan",
                    "card_hash",
                    "fee",
                    "fee_type",
                    "cart_finalized",
                )
            },
        ),
        ("Gateway response", {"fields": ("gateway_response",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at", "paid_at", "verified_at")},
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        fields = self.readonly_fields
        return fields + (("amount",) if obj is not None else ())

    @admin.display(description="Customer phone", ordering="user__phone_number")
    def customer_phone(self, obj):
        return obj.user.phone_number
