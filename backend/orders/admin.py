from django.contrib import admin

from orders.models import Cart, CartItem, Coupon, Order, OrderItem


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "discount_type",
        "discount_value",
        "max_discount_amount",
        "min_order_amount",
        "usage_limit",
        "used_count",
        "is_active",
        "starts_at",
        "expires_at",
    )
    search_fields = ("code",)
    list_filter = ("discount_type", "is_active", "starts_at", "expires_at")
    readonly_fields = ("used_count", "created_at", "updated_at")
    ordering = ("code",)


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("created_at",)
    fields = ("product", "quantity", "created_at")
    autocomplete_fields = ("product",)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "total_items", "subtotal", "created_at", "updated_at")
    search_fields = ("user__phone_number", "user__first_name", "user__last_name")
    list_filter = ("created_at", "updated_at")
    list_select_related = ("user",)
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("user",)
    inlines = (CartItemInline,)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id", "cart", "product", "quantity", "created_at")
    search_fields = ("cart__user__phone_number", "product__name", "product__sku")
    list_filter = ("created_at",)
    list_select_related = ("cart", "cart__user", "product")
    autocomplete_fields = ("cart", "product")
    readonly_fields = ("created_at",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("product", "product_name", "product_price", "quantity", "line_total")
    readonly_fields = (
        "product",
        "product_name",
        "product_price",
        "quantity",
        "line_total",
    )
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "status",
        "subtotal_amount",
        "discount_amount",
        "shipping_cost",
        "total_amount",
        "stock_reduced",
        "created_at",
    )
    search_fields = (
        "id",
        "user__phone_number",
        "recipient_name",
        "recipient_phone",
        "postal_code",
    )
    list_filter = ("status", "stock_reduced", "created_at")
    list_select_related = ("user", "coupon")
    readonly_fields = (
        "created_at",
        "updated_at",
        "total_amount",
        "subtotal_amount",
        "discount_amount",
        "shipping_cost",
    )
    autocomplete_fields = ("user", "coupon")
    inlines = (OrderItemInline,)
    actions = (
        "mark_as_processing",
        "mark_as_shipped",
        "mark_as_delivered",
        "mark_as_cancelled",
    )
    ordering = ("-created_at",)
    fieldsets = (
        (None, {"fields": ("user", "status", "stock_reduced", "coupon")}),
        (
            "Amounts",
            {
                "fields": (
                    "subtotal_amount",
                    "discount_amount",
                    "shipping_cost",
                    "total_amount",
                )
            },
        ),
        (
            "Shipping",
            {
                "fields": (
                    "recipient_name",
                    "recipient_phone",
                    "postal_code",
                    "shipping_address",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    @admin.action(description="Mark selected orders as processing")
    def mark_as_processing(self, request, queryset):
        queryset.update(status=Order.Status.PROCESSING)

    @admin.action(description="Mark selected orders as shipped")
    def mark_as_shipped(self, request, queryset):
        queryset.update(status=Order.Status.SHIPPED)

    @admin.action(description="Mark selected orders as delivered")
    def mark_as_delivered(self, request, queryset):
        queryset.update(status=Order.Status.DELIVERED)

    @admin.action(description="Mark selected orders as cancelled")
    def mark_as_cancelled(self, request, queryset):
        queryset.update(status=Order.Status.CANCELLED)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "product_name",
        "product_price",
        "quantity",
        "line_total",
    )
    search_fields = ("order__id", "product_name", "product__sku")
    list_filter = ("order__status",)
    list_select_related = ("order", "product")
    readonly_fields = ("product_name", "product_price", "line_total")
    autocomplete_fields = ("order", "product")
