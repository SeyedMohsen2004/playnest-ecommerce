from django.contrib import admin, messages
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone
from django.utils.html import format_html

from orders.models import Cart, CartItem, Coupon, Order, OrderItem
from payments.models import Payment
from payments.services.zarinpal import mask_card_pan


class OrderStatusFilter(admin.SimpleListFilter):
    title = "وضعیت سفارش"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return (
            (Order.Status.PENDING, "در انتظار پرداخت"),
            (Order.Status.PAYMENT_FAILED, "پرداخت ناموفق"),
            (Order.Status.PAID, "پرداخت موفق، در انتظار تایید فروشگاه"),
            (Order.Status.PROCESSING, "تایید شده و در حال آماده‌سازی"),
            (Order.Status.SHIPPED, "ارسال شده"),
            (Order.Status.DELIVERED, "تحویل داده شده"),
            (Order.Status.CANCELLED, "لغو شده"),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class PaymentStatusFilter(admin.SimpleListFilter):
    title = "وضعیت پرداخت"
    parameter_name = "payment_status"

    def lookups(self, request, model_admin):
        return (
            (Payment.Status.PENDING, "در انتظار پرداخت"),
            (Payment.Status.PAID, "پرداخت شده"),
            (Payment.Status.FAILED, "ناموفق"),
            (Payment.Status.CANCELLED, "لغو شده"),
        )

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
    show_change_link = False
    fields = (
        "product_thumbnail",
        "product",
        "product_name",
        "quantity",
        "product_price",
        "line_total",
        "current_stock",
    )
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("product")
            .prefetch_related("product__images")
        )

    @admin.display(description="تصویر محصول")
    def product_thumbnail(self, obj):
        image = next(iter(obj.product.images.all()), None)
        if image is None or not image.image:
            return "—"
        try:
            image_url = image.image.url
        except ValueError:
            return "—"
        return format_html(
            '<img src="{}" alt="" style="width:48px;height:48px;object-fit:cover;'
            'border-radius:8px" />',
            image_url,
        )

    @admin.display(description="موجودی فعلی", ordering="product__stock")
    def current_stock(self, obj):
        return obj.product.stock


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    can_delete = False
    show_change_link = True
    fields = (
        "status_badge",
        "authority",
        "ref_id",
        "masked_card_pan",
        "gateway_code",
        "gateway_message",
        "fee",
        "verified_at",
        "created_at",
    )
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="وضعیت پرداخت")
    def status_badge(self, obj):
        labels = {
            Payment.Status.PENDING: "در انتظار پرداخت",
            Payment.Status.PAID: "پرداخت شده",
            Payment.Status.FAILED: "ناموفق",
            Payment.Status.CANCELLED: "لغو شده",
        }
        colors = {
            Payment.Status.PENDING: ("#92400e", "#fef3c7"),
            Payment.Status.PAID: ("#166534", "#dcfce7"),
            Payment.Status.FAILED: ("#991b1b", "#fee2e2"),
            Payment.Status.CANCELLED: ("#4b5563", "#e5e7eb"),
        }
        foreground, background = colors[obj.status]
        return OrderAdmin._badge(labels[obj.status], foreground, background)

    @admin.display(description="شماره کارت")
    def masked_card_pan(self, obj):
        return mask_card_pan(obj.card_pan) or "—"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "customer_full_name",
        "customer_phone",
        "recipient_name",
        "recipient_phone",
        "formatted_total_amount",
        "status_badge",
        "payment_status_badge",
        "created_at",
        "manual_review_badge",
    )
    search_fields = (
        "=id",
        "user__phone_number",
        "user__first_name",
        "user__last_name",
        "recipient_name",
        "recipient_phone",
        "postal_code",
        "shipping_address",
        "payments__ref_id",
        "payments__authority",
    )
    list_filter = (
        OrderStatusFilter,
        PaymentStatusFilter,
        "stock_reduced",
        "requires_manual_review",
        "created_at",
    )
    list_select_related = ("user", "coupon")
    readonly_fields = (
        "order_number",
        "status",
        "status_badge",
        "user",
        "customer_full_name",
        "customer_phone",
        "created_at",
        "updated_at",
        "total_amount",
        "subtotal_amount",
        "discount_amount",
        "shipping_cost",
        "coupon",
        "coupon_usage",
        "payment_status_badge",
        "payment_authority",
        "payment_ref_id",
        "payment_card_pan",
        "payment_gateway_code",
        "payment_fee",
        "payment_verified_at",
        "stock_reduced",
        "manual_review_reason",
    )
    inlines = (OrderItemInline, PaymentInline)
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
            "شناسه و وضعیت سفارش",
            {
                "fields": (
                    "order_number",
                    "status_badge",
                    "created_at",
                    "updated_at",
                )
            },
        ),
        (
            "مشتری",
            {"fields": ("user", "customer_full_name", "customer_phone")},
        ),
        (
            "گیرنده و ارسال",
            {
                "fields": (
                    "recipient_name",
                    "recipient_phone",
                    "shipping_address",
                    "postal_code",
                )
            },
        ),
        (
            "جزئیات مالی",
            {
                "fields": (
                    "subtotal_amount",
                    "discount_amount",
                    "shipping_cost",
                    "total_amount",
                    "coupon",
                    "coupon_usage",
                )
            },
        ),
        (
            "پرداخت تاییدشده",
            {
                "fields": (
                    "payment_status_badge",
                    "payment_authority",
                    "payment_ref_id",
                    "payment_card_pan",
                    "payment_gateway_code",
                    "payment_fee",
                    "payment_verified_at",
                )
            },
        ),
        (
            "موجودی و نهایی‌سازی",
            {
                "fields": (
                    "stock_reduced",
                    "requires_manual_review",
                    "manual_review_reason",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("user", "coupon")
            .prefetch_related(
                Prefetch(
                    "payments",
                    queryset=Payment.objects.order_by("-created_at"),
                    to_attr="_admin_payments",
                )
            )
        )

    @admin.display(description="شماره سفارش", ordering="id")
    def order_number(self, obj):
        return f"#{obj.pk}"

    @admin.display(description="نام مشتری", ordering="user__last_name")
    def customer_full_name(self, obj):
        return obj.user.get_full_name() or "—"

    @admin.display(description="تلفن مشتری", ordering="user__phone_number")
    def customer_phone(self, obj):
        return obj.user.phone_number

    @admin.display(description="مبلغ کل", ordering="total_amount")
    def formatted_total_amount(self, obj):
        return f"{obj.total_amount:,} تومان"

    @admin.display(description="وضعیت سفارش", ordering="status")
    def status_badge(self, obj):
        labels = {
            Order.Status.PENDING: "در انتظار پرداخت",
            Order.Status.PAYMENT_FAILED: "پرداخت ناموفق",
            Order.Status.PAID: "پرداخت موفق، در انتظار تایید فروشگاه",
            Order.Status.PROCESSING: "تایید شده و در حال آماده‌سازی",
            Order.Status.SHIPPED: "ارسال شده",
            Order.Status.DELIVERED: "تحویل داده شده",
            Order.Status.CANCELLED: "لغو شده",
        }
        colors = {
            Order.Status.PENDING: ("#92400e", "#fef3c7"),
            Order.Status.PAYMENT_FAILED: ("#991b1b", "#fee2e2"),
            Order.Status.PAID: ("#1e40af", "#dbeafe"),
            Order.Status.PROCESSING: ("#5b21b6", "#ede9fe"),
            Order.Status.SHIPPED: ("#1e3a8a", "#dbeafe"),
            Order.Status.DELIVERED: ("#166534", "#dcfce7"),
            Order.Status.CANCELLED: ("#4b5563", "#e5e7eb"),
        }
        foreground, background = colors.get(obj.status, ("#374151", "#f3f4f6"))
        return self._badge(
            labels.get(obj.status, obj.get_status_display()), foreground, background
        )

    @admin.display(description="وضعیت پرداخت")
    def payment_status_badge(self, obj):
        payment = self._latest_payment(obj)
        if not payment:
            return self._badge("بدون پرداخت", "#4b5563", "#e5e7eb")
        labels = {
            Payment.Status.PENDING: "در انتظار پرداخت",
            Payment.Status.PAID: "پرداخت شده",
            Payment.Status.FAILED: "ناموفق",
            Payment.Status.CANCELLED: "لغو شده",
        }
        colors = {
            Payment.Status.PENDING: ("#92400e", "#fef3c7"),
            Payment.Status.PAID: ("#166534", "#dcfce7"),
            Payment.Status.FAILED: ("#991b1b", "#fee2e2"),
            Payment.Status.CANCELLED: ("#4b5563", "#e5e7eb"),
        }
        foreground, background = colors[payment.status]
        return self._badge(labels[payment.status], foreground, background)

    @admin.display(description="بررسی دستی", ordering="requires_manual_review")
    def manual_review_badge(self, obj):
        if obj.requires_manual_review:
            return self._badge("نیازمند بررسی فوری", "#9a3412", "#ffedd5")
        return self._badge("عادی", "#166534", "#dcfce7")

    @admin.display(description="وضعیت استفاده کوپن")
    def coupon_usage(self, obj):
        if obj.coupon is None:
            return "بدون کوپن"
        limit = (
            obj.coupon.usage_limit if obj.coupon.usage_limit is not None else "نامحدود"
        )
        return f"{obj.coupon.used_count} استفاده از {limit}"

    @admin.display(description="Authority")
    def payment_authority(self, obj):
        payment = self._latest_payment(obj)
        return payment.authority if payment and payment.authority else "—"

    @admin.display(description="شماره پیگیری")
    def payment_ref_id(self, obj):
        payment = self._latest_payment(obj)
        return payment.ref_id if payment and payment.ref_id else "—"

    @admin.display(description="شماره کارت")
    def payment_card_pan(self, obj):
        payment = self._latest_payment(obj)
        return mask_card_pan(payment.card_pan) if payment else "—"

    @admin.display(description="کد درگاه")
    def payment_gateway_code(self, obj):
        payment = self._latest_payment(obj)
        return (
            payment.gateway_code
            if payment and payment.gateway_code is not None
            else "—"
        )

    @admin.display(description="کارمزد")
    def payment_fee(self, obj):
        payment = self._latest_payment(obj)
        return payment.fee if payment and payment.fee is not None else "—"

    @admin.display(description="زمان تایید پرداخت")
    def payment_verified_at(self, obj):
        payment = self._latest_payment(obj)
        return payment.verified_at if payment else None

    @admin.action(description="تایید سفارش و شروع آماده‌سازی")
    def mark_as_processing(self, request, queryset):
        self._transition_orders(
            request,
            queryset,
            from_statuses=(Order.Status.PAID,),
            to_status=Order.Status.PROCESSING,
            success_message="{} سفارش تایید شد و وارد مرحله آماده‌سازی شد.",
        )

    @admin.action(description="تغییر وضعیت به ارسال شده")
    def mark_as_shipped(self, request, queryset):
        self._transition_orders(
            request,
            queryset,
            from_statuses=(Order.Status.PROCESSING,),
            to_status=Order.Status.SHIPPED,
            success_message="{} سفارش به وضعیت ارسال شده تغییر کرد.",
        )

    @admin.action(description="تغییر وضعیت به تحویل داده شده")
    def mark_as_delivered(self, request, queryset):
        self._transition_orders(
            request,
            queryset,
            from_statuses=(Order.Status.SHIPPED,),
            to_status=Order.Status.DELIVERED,
            success_message="{} سفارش به وضعیت تحویل داده شده تغییر کرد.",
        )

    @admin.action(description="لغو سفارش‌های انتخاب‌شده")
    def mark_as_cancelled(self, request, queryset):
        self._transition_orders(
            request,
            queryset,
            from_statuses=(Order.Status.PENDING, Order.Status.PAYMENT_FAILED),
            to_status=Order.Status.CANCELLED,
            success_message="{} سفارش لغو شد.",
        )

    def _transition_orders(
        self,
        request,
        queryset,
        *,
        from_statuses,
        to_status,
        success_message,
    ):
        selected_ids = set(queryset.values_list("pk", flat=True))
        changed_orders = []
        now = timezone.now()
        with transaction.atomic():
            locked_orders = list(
                Order.objects.select_for_update().filter(pk__in=selected_ids)
            )
            for order in locked_orders:
                if order.status not in from_statuses or order.requires_manual_review:
                    continue
                old_status = order.status
                order.status = to_status
                order.updated_at = now
                changed_orders.append((order, old_status))

            if changed_orders:
                Order.objects.bulk_update(
                    [order for order, _old_status in changed_orders],
                    ("status", "updated_at"),
                )
                for order, old_status in changed_orders:
                    self.log_change(
                        request,
                        order,
                        (
                            "تغییر وضعیت سفارش از "
                            f"{self._status_label(old_status)} به "
                            f"{self._status_label(to_status)}"
                        ),
                    )

        changed_count = len(changed_orders)
        skipped_count = len(selected_ids) - changed_count
        if changed_count:
            self.message_user(
                request,
                success_message.format(self._persian_number(changed_count)),
                level=messages.SUCCESS,
            )
        if skipped_count:
            self.message_user(
                request,
                (
                    f"{self._persian_number(skipped_count)} سفارش به دلیل وضعیت "
                    "نامعتبر یا نیاز به بررسی دستی تغییر نکرد."
                ),
                level=messages.WARNING,
            )

    def _latest_payment(self, obj):
        prefetched = getattr(obj, "_admin_payments", None)
        if prefetched is not None:
            return prefetched[0] if prefetched else None
        return obj.payments.order_by("-created_at").first()

    @staticmethod
    def _badge(label, foreground, background):
        return format_html(
            '<span style="display:inline-block;padding:4px 9px;border-radius:999px;'
            'font-weight:700;color:{};background:{};white-space:nowrap">{}</span>',
            foreground,
            background,
            label,
        )

    @staticmethod
    def _persian_number(value):
        return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

    @staticmethod
    def _status_label(status):
        return {
            Order.Status.PENDING: "در انتظار پرداخت",
            Order.Status.PAYMENT_FAILED: "پرداخت ناموفق",
            Order.Status.PAID: "پرداخت موفق، در انتظار تایید فروشگاه",
            Order.Status.PROCESSING: "تایید شده و در حال آماده‌سازی",
            Order.Status.SHIPPED: "ارسال شده",
            Order.Status.DELIVERED: "تحویل داده شده",
            Order.Status.CANCELLED: "لغو شده",
        }[status]


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
    readonly_fields = (
        "order",
        "product",
        "product_name",
        "product_price",
        "quantity",
        "line_total",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
