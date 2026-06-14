from django.contrib import admin

from orders.models import Cart, CartItem, Coupon, Order, OrderItem


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "discount_type",
        "discount_value",
        "used_count",
        "usage_limit",
        "is_active",
        "starts_at",
        "expires_at",
    )
    search_fields = ("code",)
    list_filter = ("discount_type", "is_active", "starts_at", "expires_at")


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "total_items", "subtotal", "updated_at")
    search_fields = ("user__phone_number", "user__first_name", "user__last_name")
    list_filter = ("created_at", "updated_at")
    inlines = (CartItemInline,)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id", "cart", "product", "quantity", "created_at")
    search_fields = ("cart__user__phone_number", "product__name", "product__sku")
    list_filter = ("created_at",)
    list_select_related = ("cart", "product")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
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
        "stock_reduced",
        "coupon",
        "subtotal_amount",
        "discount_amount",
        "shipping_cost",
        "total_amount",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "user__phone_number",
        "recipient_name",
        "recipient_phone",
        "postal_code",
    )
    list_filter = ("status", "stock_reduced", "created_at", "updated_at")
    list_select_related = ("user", "coupon")
    inlines = (OrderItemInline,)


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
    list_select_related = ("order", "product")
