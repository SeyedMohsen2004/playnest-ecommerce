from django.contrib import admin

from orders.models import Cart, CartItem, Coupon, Order, OrderItem
from payments.models import Payment


class PaymentStatusFilter(admin.SimpleListFilter):
    title = "payment status"
    parameter_name = "payment_status"

    def lookups(self, request, model_admin):
        return Payment.Status.choices

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(payments__status=self.value()).distinct()
        return queryset


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
        "starts_at",
        "ends_at",
        "is_active",
    )
    search_fields = ("code",)
    list_filter = ("discount_type", "is_active", "starts_at", "expires_at")
    readonly_fields = ("used_count", "created_at", "updated_at")
    ordering = ("-is_active", "code")
    date_hierarchy = "created_at"
    fieldsets = (
        ("Coupon", {"fields": ("code", "is_active")}),
        (
            "Discount rules",
            {
                "fields": (
                    "discount_type",
                    "discount_value",
                    "max_discount_amount",
                    "min_order_amount",
                )
            },
        ),
        ("Usage", {"fields": ("usage_limit", "used_count")}),
        ("Schedule", {"fields": ("starts_at", "expires_at")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Ends at", ordering="expires_at")
    def ends_at(self, obj):
        return obj.expires_at


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("created_at",)
    fields = ("product", "selected_options", "quantity", "created_at")
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
    date_hierarchy = "created_at"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id", "cart", "product", "quantity", "created_at")
    search_fields = (
        "cart__user__phone_number",
        "product__name",
        "product__sku",
    )
    list_filter = ("created_at",)
    list_select_related = ("cart", "cart__user", "product")
    autocomplete_fields = ("cart", "product")
    readonly_fields = ("created_at",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = (
        "product",
        "product_name",
        "selected_options_snapshot",
        "product_price",
        "quantity",
        "line_total",
    )
    readonly_fields = (
        "product",
        "product_name",
        "selected_options_snapshot",
        "product_price",
        "quantity",
        "line_total",
    )
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "customer_phone",
        "total_amount",
        "status",
        "payment_status",
        "created_at",
    )
    search_fields = (
        "id",
        "user__phone_number",
        "user__email",
        "recipient_name",
        "recipient_phone",
        "postal_code",
        "shipping_address",
    )
    list_filter = ("status", PaymentStatusFilter, "stock_reduced", "created_at")
    list_select_related = ("user", "coupon")
    readonly_fields = (
        "payment_status",
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
    date_hierarchy = "created_at"
    fieldsets = (
        (
            "Order status",
            {"fields": ("user", "status", "payment_status", "stock_reduced", "coupon")},
        ),
        (
            "Financial summary",
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

    @admin.display(description="Order", ordering="id")
    def order_number(self, obj):
        return f"#{obj.pk}"

    @admin.display(description="Customer phone", ordering="user__phone_number")
    def customer_phone(self, obj):
        return obj.user.phone_number

    @admin.display(description="Payment status")
    def payment_status(self, obj):
        payment = obj.payments.order_by("-created_at").first()
        if not payment:
            return "No payment"
        return payment.get_status_display()

    @admin.action(description="ارسال سفارش‌های انتخاب‌شده به مرحله پردازش")
    def mark_as_processing(self, request, queryset):
        queryset.update(status=Order.Status.PROCESSING)

    @admin.action(description="ثبت سفارش‌های انتخاب‌شده به عنوان ارسال‌شده")
    def mark_as_shipped(self, request, queryset):
        queryset.update(status=Order.Status.SHIPPED)

    @admin.action(description="ثبت سفارش‌های انتخاب‌شده به عنوان تحویل‌شده")
    def mark_as_delivered(self, request, queryset):
        queryset.update(status=Order.Status.DELIVERED)

    @admin.action(description="لغو سفارش‌های انتخاب‌شده")
    def mark_as_cancelled(self, request, queryset):
        queryset.update(status=Order.Status.CANCELLED)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "product_name",
        "selected_options_snapshot",
        "product_price",
        "quantity",
        "line_total",
    )
    search_fields = ("order__id", "product_name", "product__sku")
    list_filter = ("order__status",)
    list_select_related = ("order", "product")
    readonly_fields = (
        "product_name",
        "selected_options_snapshot",
        "product_price",
        "line_total",
    )
    autocomplete_fields = ("order", "product")
