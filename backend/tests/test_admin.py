import pytest
from django.contrib import admin

from accounts.models import PhoneOTP, User
from orders.models import Cart, CartItem, Coupon, Order, OrderItem
from payments.models import Payment
from products.models import (
    Brand,
    Category,
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
