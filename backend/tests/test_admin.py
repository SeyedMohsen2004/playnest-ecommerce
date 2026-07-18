from unittest.mock import patch

import pytest
from django.contrib import admin
from django.test import RequestFactory
from django.urls import reverse

from accounts.models import PhoneOTP, User
from orders.admin import (
    OrderItemInline,
    OrderStatusFilter,
    PaymentInline,
    PaymentStatusFilter,
)
from orders.models import Cart, CartItem, Coupon, Order, OrderItem
from payments.models import Payment
from products.models import (
    Brand,
    Category,
    HomepageProductSlot,
    Product,
    ProductImage,
    ProductReview,
    WishlistItem,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_user():
    return User.objects.create_superuser(
        phone_number="09000000000",
        password="StrongPassword!42",
        first_name="Store",
        last_name="Manager",
    )


@pytest.fixture
def customer():
    return User.objects.create_user(
        phone_number="09123456789",
        password="StrongPassword!42",
        first_name="Customer",
        last_name="Name",
        is_active=True,
        is_phone_verified=True,
    )


@pytest.fixture
def admin_product():
    category = Category.objects.create(name="Admin Toys", slug="admin-toys")
    brand = Brand.objects.create(name="Admin Brand", slug="admin-brand")
    return Product.objects.create(
        category=category,
        brand=brand,
        name="Admin Test Toy",
        slug="admin-test-toy",
        description="Admin action test product.",
        sku="ADMIN-001",
        price=2000,
        stock=8,
        age_group=Product.AgeGroup.THREE_TO_FIVE,
        gender=Product.Gender.UNISEX,
    )


def create_admin_order(customer, product, *, status, manual_review=False):
    order = Order.objects.create(
        user=customer,
        status=status,
        stock_reduced=status
        in {
            Order.Status.PAID,
            Order.Status.PROCESSING,
            Order.Status.SHIPPED,
            Order.Status.DELIVERED,
        },
        requires_manual_review=manual_review,
        manual_review_reason=(
            "Manual inventory check required." if manual_review else ""
        ),
        subtotal_amount=2000,
        total_amount=2000,
        shipping_address="Admin Test Address",
        postal_code="1234567890",
        recipient_name="Order Recipient",
        recipient_phone="09121111111",
    )
    OrderItem.objects.create(
        order=order,
        product=product,
        product_name=product.name,
        product_price=2000,
        quantity=1,
        line_total=2000,
    )
    return order


def run_order_action(order_admin, action_name, admin_user, queryset):
    request = RequestFactory().post("/admin/orders/order/")
    request.user = admin_user
    with patch.object(order_admin, "message_user") as message_user:
        getattr(order_admin, action_name)(request, queryset)
    return [call.args[1] for call in message_user.call_args_list]


@pytest.mark.parametrize(
    "model",
    (
        User,
        PhoneOTP,
        Category,
        Brand,
        Product,
        ProductImage,
        HomepageProductSlot,
        ProductReview,
        WishlistItem,
        Cart,
        CartItem,
        Order,
        OrderItem,
        Coupon,
        Payment,
    ),
)
def test_major_models_are_registered_in_admin(model):
    admin.autodiscover()

    assert model in admin.site._registry


def test_store_manager_admin_actions_are_available():
    admin.autodiscover()

    review_admin = admin.site._registry[ProductReview]
    order_admin = admin.site._registry[Order]

    assert {"approve_reviews", "reject_reviews"}.issubset(review_admin.actions)
    assert {
        "mark_as_processing",
        "mark_as_shipped",
        "mark_as_delivered",
        "mark_as_cancelled",
    }.issubset(order_admin.actions)


def test_cancelled_product_option_models_are_not_registered_in_admin():
    admin.autodiscover()

    registered_model_names = {
        model.__name__
        for model in admin.site._registry
        if model._meta.app_label == "products"
    }
    product_admin = admin.site._registry[Product]
    product_inline_model_names = {
        inline.model.__name__ for inline in product_admin.inlines
    }

    assert "ProductOption" not in registered_model_names
    assert "ProductOptionValue" not in registered_model_names
    assert "ProductVariant" not in registered_model_names
    assert "ProductOption" not in product_inline_model_names
    assert "ProductOptionValue" not in product_inline_model_names


def test_homepage_product_slot_admin_supports_popular_and_featured_sections():
    admin.autodiscover()

    slot_admin = admin.site._registry[HomepageProductSlot]
    section_values = {value for value, _label in HomepageProductSlot.Section.choices}

    assert HomepageProductSlot.Section.POPULAR_MARQUEE in section_values
    assert HomepageProductSlot.Section.FEATURED_PRODUCTS in section_values
    assert "section_label" in slot_admin.list_display
    assert "product" in slot_admin.list_display
    assert "sort_order" in slot_admin.list_display
    assert "is_active" in slot_admin.list_display
    assert "section" in slot_admin.list_filter
    assert "is_active" in slot_admin.list_filter
    assert "product__name" in slot_admin.search_fields
    assert "section" in slot_admin.search_fields


def test_paid_order_approval_preserves_payment_stock_and_cart(
    admin_user, customer, admin_product
):
    order = create_admin_order(customer, admin_product, status=Order.Status.PAID)
    payment = Payment.objects.create(
        user=customer,
        order=order,
        amount=order.total_amount,
        status=Payment.Status.PAID,
        authority="A" * 36,
        ref_id="admin-ref-id",
    )
    cart = Cart.objects.create(user=customer)
    cart_item = CartItem.objects.create(
        cart=cart,
        product=admin_product,
        quantity=4,
    )
    original_stock = admin_product.stock

    order_admin = admin.site._registry[Order]
    action_messages = run_order_action(
        order_admin,
        "mark_as_processing",
        admin_user,
        Order.objects.filter(pk=order.pk),
    )

    order.refresh_from_db()
    payment.refresh_from_db()
    admin_product.refresh_from_db()
    cart_item.refresh_from_db()
    assert order.status == Order.Status.PROCESSING
    assert payment.status == Payment.Status.PAID
    assert payment.ref_id == "admin-ref-id"
    assert admin_product.stock == original_stock
    assert cart_item.quantity == 4
    assert "۱ سفارش تایید شد و وارد مرحله آماده‌سازی شد." in action_messages


def test_manual_review_order_is_not_approved(admin_user, customer, admin_product):
    order = create_admin_order(
        customer,
        admin_product,
        status=Order.Status.PAID,
        manual_review=True,
    )
    order_admin = admin.site._registry[Order]

    action_messages = run_order_action(
        order_admin,
        "mark_as_processing",
        admin_user,
        Order.objects.filter(pk=order.pk),
    )

    order.refresh_from_db()
    assert order.status == Order.Status.PAID
    assert any("نیاز به بررسی دستی" in message for message in action_messages)


@pytest.mark.parametrize(
    "invalid_status",
    (
        Order.Status.PENDING,
        Order.Status.PAYMENT_FAILED,
        Order.Status.CANCELLED,
    ),
)
def test_invalid_order_cannot_move_to_processing(
    admin_user, customer, admin_product, invalid_status
):
    order = create_admin_order(customer, admin_product, status=invalid_status)
    order_admin = admin.site._registry[Order]

    run_order_action(
        order_admin,
        "mark_as_processing",
        admin_user,
        Order.objects.filter(pk=order.pk),
    )

    order.refresh_from_db()
    assert order.status == invalid_status


def test_processing_order_can_move_to_shipped(admin_user, customer, admin_product):
    order = create_admin_order(
        customer,
        admin_product,
        status=Order.Status.PROCESSING,
    )
    order_admin = admin.site._registry[Order]

    run_order_action(
        order_admin,
        "mark_as_shipped",
        admin_user,
        Order.objects.filter(pk=order.pk),
    )

    order.refresh_from_db()
    assert order.status == Order.Status.SHIPPED


def test_paid_order_cannot_move_directly_to_shipped(
    admin_user, customer, admin_product
):
    order = create_admin_order(customer, admin_product, status=Order.Status.PAID)
    order_admin = admin.site._registry[Order]

    run_order_action(
        order_admin,
        "mark_as_shipped",
        admin_user,
        Order.objects.filter(pk=order.pk),
    )

    order.refresh_from_db()
    assert order.status == Order.Status.PAID


def test_shipped_order_can_move_to_delivered(admin_user, customer, admin_product):
    order = create_admin_order(customer, admin_product, status=Order.Status.SHIPPED)
    order_admin = admin.site._registry[Order]

    run_order_action(
        order_admin,
        "mark_as_delivered",
        admin_user,
        Order.objects.filter(pk=order.pk),
    )

    order.refresh_from_db()
    assert order.status == Order.Status.DELIVERED


def test_delivered_order_cannot_move_backward(admin_user, customer, admin_product):
    order = create_admin_order(customer, admin_product, status=Order.Status.DELIVERED)
    order_admin = admin.site._registry[Order]

    run_order_action(
        order_admin,
        "mark_as_shipped",
        admin_user,
        Order.objects.filter(pk=order.pk),
    )

    order.refresh_from_db()
    assert order.status == Order.Status.DELIVERED


def test_order_item_inline_and_admin_are_read_only():
    order_admin = admin.site._registry[Order]
    order_item_admin = admin.site._registry[OrderItem]
    inline = OrderItemInline(Order, admin.site)

    assert OrderItemInline in order_admin.inlines
    assert inline.can_delete is False
    assert inline.has_add_permission(RequestFactory().get("/admin/")) is False
    assert {
        "product",
        "product_name",
        "quantity",
        "product_price",
        "line_total",
        "current_stock",
    }.issubset(inline.readonly_fields)
    assert {
        "order",
        "product",
        "product_name",
        "quantity",
        "product_price",
        "line_total",
    }.issubset(order_item_admin.readonly_fields)


def test_payment_inline_and_sensitive_payment_fields_are_read_only():
    order_admin = admin.site._registry[Order]
    payment_admin = admin.site._registry[Payment]
    inline = PaymentInline(Order, admin.site)

    assert PaymentInline in order_admin.inlines
    assert inline.can_delete is False
    assert inline.has_add_permission(RequestFactory().get("/admin/")) is False
    assert {
        "status_badge",
        "authority",
        "ref_id",
        "masked_card_pan",
        "gateway_code",
        "gateway_message",
        "fee",
        "verified_at",
    }.issubset(inline.readonly_fields)
    assert {
        "user",
        "order",
        "amount",
        "status",
        "authority",
        "ref_id",
        "card_pan",
        "card_hash",
        "gateway_response",
        "gateway_code",
        "verified_at",
    }.issubset(payment_admin.readonly_fields)
    assert payment_admin.has_add_permission(RequestFactory().get("/admin/")) is False


def test_order_admin_list_search_filters_and_direct_status_safety():
    order_admin = admin.site._registry[Order]

    assert order_admin.list_display == (
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
    assert {
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
    }.issubset(order_admin.search_fields)
    assert {
        "stock_reduced",
        "requires_manual_review",
        "created_at",
    }.issubset(order_admin.list_filter)
    assert OrderStatusFilter in order_admin.list_filter
    assert PaymentStatusFilter in order_admin.list_filter
    assert "status" in order_admin.readonly_fields
    assert "stock_reduced" in order_admin.readonly_fields


def test_order_admin_filtered_list_and_detail_render_safely(
    client, admin_user, customer, admin_product
):
    order = create_admin_order(
        customer,
        admin_product,
        status=Order.Status.PAID,
        manual_review=True,
    )
    Payment.objects.create(
        user=customer,
        order=order,
        amount=order.total_amount,
        status=Payment.Status.PAID,
        authority="R" * 36,
        ref_id="render-ref-id",
        card_pan="6037991234561234",
        gateway_code=100,
    )
    client.force_login(admin_user)

    list_response = client.get(
        reverse("admin:orders_order_changelist"),
        {
            "q": "render-ref-id",
            "status": Order.Status.PAID,
            "payment_status": Payment.Status.PAID,
        },
    )
    detail_response = client.get(reverse("admin:orders_order_change", args=(order.pk,)))

    assert list_response.status_code == 200
    assert detail_response.status_code == 200
    list_content = list_response.content.decode()
    detail_content = detail_response.content.decode()
    assert "پرداخت موفق، در انتظار تایید فروشگاه" in list_content
    assert "نیازمند بررسی فوری" in list_content
    assert "render-ref-id" in detail_content
    assert "603799******1234" in detail_content
    assert "6037991234561234" not in detail_content
