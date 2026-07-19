from datetime import timedelta
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from orders.models import Cart, CartItem, Coupon, Order
from payments.models import Payment
from payments.services.zarinpal import PaymentVerificationResult
from products.models import Brand, Category, Product

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(
        phone_number="09123456789",
        password="StrongPassword!42",
        first_name="Coupon",
        last_name="User",
        is_active=True,
        is_phone_verified=True,
    )


@pytest.fixture
def product():
    category = Category.objects.create(name="Coupon Toys", slug="coupon-toys")
    brand = Brand.objects.create(name="Coupon Brand", slug="coupon-brand")
    return Product.objects.create(
        category=category,
        brand=brand,
        name="Coupon Toy",
        slug="coupon-toy",
        description="A toy used for coupon tests.",
        sku="COUPON-001",
        price=1_000_000,
        stock=10,
        age_group=Product.AgeGroup.THREE_TO_FIVE,
        gender=Product.Gender.UNISEX,
    )


def auth(user):
    token = RefreshToken.for_user(user).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def add_to_cart(user, product, quantity=1):
    return CartItem.objects.create(
        cart=Cart.objects.create(user=user),
        product=product,
        quantity=quantity,
    )


def apply_coupon(client, user, code):
    return client.post(
        reverse("orders:apply-coupon"),
        {"code": code},
        content_type="application/json",
        **auth(user),
    )


def checkout(client, user, coupon_code=""):
    return client.post(
        reverse("orders:checkout"),
        {
            "shipping_address": "123 Coupon Street",
            "postal_code": "1234567890",
            "recipient_name": "Coupon User",
            "recipient_phone": user.phone_number,
            "shipping_zone": "tabriz",
            "coupon_code": coupon_code,
        },
        content_type="application/json",
        **auth(user),
    )


def verified_result():
    return PaymentVerificationResult(
        code=100,
        message="Verified",
        ref_id="coupon-ref",
        card_pan="603799******1234",
        card_hash="coupon-hash",
        fee=0,
        fee_type="Merchant",
        gateway_response={"data": {"code": 100, "ref_id": "coupon-ref"}},
    )


def test_valid_percentage_coupon(client, user, product):
    add_to_cart(user, product)
    Coupon.objects.create(
        code="OFF10",
        discount_type=Coupon.DiscountType.PERCENTAGE,
        discount_value=10,
    )

    response = apply_coupon(client, user, "OFF10")

    assert response.status_code == 200
    assert response.json() == {
        "subtotal": 1_000_000,
        "discount_amount": 100_000,
        "shipping_cost": 0,
        "total_amount": 900_000,
    }


def test_valid_fixed_coupon(client, user, product):
    add_to_cart(user, product)
    Coupon.objects.create(
        code="FIXED",
        discount_type=Coupon.DiscountType.FIXED,
        discount_value=200_000,
    )

    response = apply_coupon(client, user, "FIXED")

    assert response.status_code == 200
    assert response.json()["discount_amount"] == 200_000
    assert response.json()["total_amount"] == 800_000


def test_expired_coupon_is_rejected(client, user, product):
    add_to_cart(user, product)
    Coupon.objects.create(
        code="EXPIRED",
        discount_type=Coupon.DiscountType.PERCENTAGE,
        discount_value=10,
        expires_at=timezone.now() - timedelta(minutes=1),
    )

    response = apply_coupon(client, user, "EXPIRED")

    assert response.status_code == 400
    assert "expired" in str(response.json()).lower()


def test_inactive_coupon_is_rejected(client, user, product):
    add_to_cart(user, product)
    Coupon.objects.create(
        code="INACTIVE",
        discount_type=Coupon.DiscountType.PERCENTAGE,
        discount_value=10,
        is_active=False,
    )

    response = apply_coupon(client, user, "INACTIVE")

    assert response.status_code == 400
    assert "inactive" in str(response.json()).lower()


def test_coupon_min_order_amount_is_enforced(client, user, product):
    add_to_cart(user, product)
    Coupon.objects.create(
        code="MINIMUM",
        discount_type=Coupon.DiscountType.PERCENTAGE,
        discount_value=10,
        min_order_amount=2_000_000,
    )

    response = apply_coupon(client, user, "MINIMUM")

    assert response.status_code == 400
    assert "minimum" in str(response.json()).lower()


def test_coupon_usage_limit_is_enforced(client, user, product):
    add_to_cart(user, product)
    Coupon.objects.create(
        code="LIMITED",
        discount_type=Coupon.DiscountType.PERCENTAGE,
        discount_value=10,
        usage_limit=1,
        used_count=1,
    )

    response = apply_coupon(client, user, "LIMITED")

    assert response.status_code == 400
    assert "usage limit" in str(response.json()).lower()


def test_checkout_stores_coupon_discount_and_shipping(client, user, product):
    add_to_cart(user, product)
    coupon = Coupon.objects.create(
        code="CHECKOUT10",
        discount_type=Coupon.DiscountType.PERCENTAGE,
        discount_value=10,
    )

    response = checkout(client, user, coupon.code)

    assert response.status_code == 201
    order = Order.objects.get(user=user)
    assert order.coupon == coupon
    assert order.subtotal_amount == 1_000_000
    assert order.discount_amount == 100_000
    assert order.shipping_cost == 50_000
    assert order.total_amount == 950_000
    assert coupon.used_count == 0


def test_shipping_rate_is_added_above_the_previous_free_shipping_threshold(
    client, user, product
):
    add_to_cart(user, product, quantity=2)

    response = checkout(client, user)

    assert response.status_code == 201
    order = Order.objects.get(user=user)
    assert order.subtotal_amount == 2_000_000
    assert order.shipping_cost == 50_000
    assert order.total_amount == 2_050_000


def test_coupon_used_count_increments_after_payment_success(
    client,
    settings,
    user,
    product,
):
    settings.FRONTEND_BASE_URL = "https://ipaktoys.ir"
    add_to_cart(user, product)
    coupon = Coupon.objects.create(
        code="PAY10",
        discount_type=Coupon.DiscountType.PERCENTAGE,
        discount_value=10,
    )
    checkout(client, user, coupon.code)
    order = Order.objects.get(user=user)
    payment = Payment.objects.create(
        user=user,
        order=order,
        amount=order.total_amount,
        authority="C" * 36,
    )

    with patch(
        "payments.views.ZarinPalService.verify_payment",
        return_value=verified_result(),
    ):
        response = client.get(
            reverse("payments:zarinpal-callback"),
            {"Authority": payment.authority, "Status": "OK"},
        )

    assert response.status_code == 302
    coupon.refresh_from_db()
    assert coupon.used_count == 1


def test_coupon_used_count_does_not_increment_twice(client, settings, user, product):
    settings.FRONTEND_BASE_URL = "https://ipaktoys.ir"
    add_to_cart(user, product)
    coupon = Coupon.objects.create(
        code="ONCE",
        discount_type=Coupon.DiscountType.PERCENTAGE,
        discount_value=10,
    )
    checkout(client, user, coupon.code)
    order = Order.objects.get(user=user)
    payment = Payment.objects.create(
        user=user,
        order=order,
        amount=order.total_amount,
        authority="D" * 36,
    )

    with patch(
        "payments.views.ZarinPalService.verify_payment",
        return_value=verified_result(),
    ):
        payload = {"Authority": payment.authority, "Status": "OK"}
        client.get(reverse("payments:zarinpal-callback"), payload)
        client.get(reverse("payments:zarinpal-callback"), payload)

    coupon.refresh_from_db()
    assert coupon.used_count == 1
