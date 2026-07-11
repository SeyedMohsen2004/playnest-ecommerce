import pytest
from django.contrib import admin

from accounts.models import PhoneOTP, User
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
