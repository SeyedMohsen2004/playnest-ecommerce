from django.contrib import admin

from payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "user",
        "gateway",
        "amount",
        "status",
        "authority",
        "ref_id",
        "created_at",
        "paid_at",
    )
    search_fields = (
        "order__id",
        "user__phone_number",
        "authority",
        "ref_id",
        "card_pan",
    )
    list_filter = ("gateway", "status", "created_at", "paid_at")
    list_select_related = ("order", "user")
    readonly_fields = (
        "gateway_response",
        "created_at",
        "updated_at",
        "paid_at",
    )
