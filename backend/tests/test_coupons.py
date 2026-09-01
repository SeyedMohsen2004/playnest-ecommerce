from datetime import timedelta
from unittest.mock import patch

import pytest
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from orders.models import (
    Cart,
    CartItem,
    Coupon,
    CouponRedemption,
    CouponValidationThrottle,
    Order,
)
from orders.pricing import COUPON_UNAVAILABLE_MESSAGE
from orders.services import cancel_order
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
        code="TEST-OFF10",
        discount_type=Coupon.DiscountType.PERCENTAGE,
        discount_value=10,
    )

    response = apply_coupon(client, user, "TEST-OFF10")

    assert response.status_code == 200
    assert response.json() == {
        "subtotal": 1_000_000,
        "discount_amount": 100_000,
        "shipping_cost": 0,
        "total_amount": 900_000,
    }


def test_percentage_coupon_respects_maximum_discount(client, user, product):
    add_to_cart(user, product)
    Coupon.objects.create(
        code="CAPPED",
        discount_type=Coupon.DiscountType.PERCENTAGE,
        discount_value=50,
        max_discount_amount=100_000,
    )

    response = apply_coupon(client, user, "CAPPED")

    assert response.status_code == 200
    assert response.json()["discount_amount"] == 100_000
    assert response.json()["total_amount"] == 900_000


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


def test_fixed_coupon_cannot_exceed_order_subtotal(client, user, product):
    add_to_cart(user, product)
    Coupon.objects.create(
        code="TOO-LARGE",
        discount_type=Coupon.DiscountType.FIXED,
        discount_value=1_000_001,
    )

    response = apply_coupon(client, user, "TOO-LARGE")

    assert response.status_code == 400
    assert response.json()["code"] == [COUPON_UNAVAILABLE_MESSAGE]


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
    assert response.json()["code"] == [COUPON_UNAVAILABLE_MESSAGE]


def test_future_coupon_is_rejected(client, user, product):
    add_to_cart(user, product)
    Coupon.objects.create(
        code="FUTURE",
        discount_type=Coupon.DiscountType.PERCENTAGE,
        discount_value=10,
        starts_at=timezone.now() + timedelta(minutes=1),
    )

    response = apply_coupon(client, user, "FUTURE")

    assert response.status_code == 400
    assert response.json()["code"] == [COUPON_UNAVAILABLE_MESSAGE]


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
    assert response.json()["code"] == [COUPON_UNAVAILABLE_MESSAGE]


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
    assert response.json()["code"] == [
        "مبلغ سفارش به حداقل لازم برای استفاده از این کد نرسیده است."
    ]


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
    assert response.json()["code"] == [COUPON_UNAVAILABLE_MESSAGE]


def test_coupon_apply_requires_authentication(client):
    response = client.post(
        reverse("orders:apply-coupon"),
        {"code": "ANY-CODE"},
        content_type="application/json",
    )

    assert response.status_code == 401


def test_coupon_enumeration_sensitive_failures_share_one_message(
    client,
    user,
    product,
):
    add_to_cart(user, product)

    response = apply_coupon(client, user, "DOES-NOT-EXIST")

    assert response.status_code == 400
    assert response.json()["code"] == [COUPON_UNAVAILABLE_MESSAGE]


def test_coupon_apply_is_scoped_and_rate_limited_per_user(
    client,
    user,
    product,
):
    add_to_cart(user, product)
    second_user = User.objects.create_user(
        phone_number="09123456780",
        password="StrongPassword!42",
        is_active=True,
        is_phone_verified=True,
    )
    add_to_cart(second_user, product)
    allowed = [apply_coupon(client, user, f"INVALID-{attempt}") for attempt in range(8)]
    blocked = apply_coupon(client, user, "INVALID-9")
    unrelated_user = apply_coupon(client, second_user, "INVALID-OTHER-USER")

    assert all(response.status_code == 400 for response in allowed)
    assert blocked.status_code == 429
    assert unrelated_user.status_code == 400
    assert CouponValidationThrottle.objects.get(user=user).attempt_count == 8
    assert CouponValidationThrottle.objects.get(user=second_user).attempt_count == 1

    throttle = CouponValidationThrottle.objects.get(user=user)
    throttle.window_started_at = timezone.now() - timedelta(minutes=2)
    throttle.save(update_fields=("window_started_at", "updated_at"))
    recovered = apply_coupon(client, user, "INVALID-AFTER-WINDOW")
    throttle.refresh_from_db()
    assert recovered.status_code == 400
    assert throttle.attempt_count == 1


def test_per_user_coupon_limit_counts_reservations_and_is_user_specific(
    client,
    user,
    product,
):
    add_to_cart(user, product)
    coupon = Coupon.objects.create(
        code="ONE-PER-CUSTOMER",
        discount_type=Coupon.DiscountType.PERCENTAGE,
        discount_value=10,
        per_user_usage_limit=1,
    )

    first = checkout(client, user, coupon.code)
    repeated = checkout(client, user, coupon.code)

    second_user = User.objects.create_user(
        phone_number="09123456780",
        password="StrongPassword!42",
        is_active=True,
        is_phone_verified=True,
    )
    add_to_cart(second_user, product)
    other_customer = checkout(client, second_user, coupon.code)

    assert first.status_code == 201
    assert repeated.status_code == 400
    assert repeated.json()["coupon"] == [COUPON_UNAVAILABLE_MESSAGE]
    assert other_customer.status_code == 201


def test_released_coupon_reservation_restores_per_user_allowance(
    client,
    user,
    product,
):
    add_to_cart(user, product)
    coupon = Coupon.objects.create(
        code="REUSABLE-AFTER-CANCEL",
        discount_type=Coupon.DiscountType.PERCENTAGE,
        discount_value=10,
        per_user_usage_limit=1,
    )
    first = checkout(client, user, coupon.code)
    first_order = Order.objects.get(pk=first.json()["id"])

    cancel_order(first_order.id)
    second = checkout(client, user, coupon.code)

    assert second.status_code == 201
    assert (
        CouponRedemption.objects.filter(
            coupon=coupon,
            state=CouponRedemption.State.RELEASED,
        ).count()
        == 1
    )
    assert (
        CouponRedemption.objects.filter(
            coupon=coupon,
            state=CouponRedemption.State.RESERVED,
        ).count()
        == 1
    )


def test_null_per_user_coupon_limit_preserves_unlimited_behavior(
    client,
    user,
    product,
):
    add_to_cart(user, product)
    coupon = Coupon.objects.create(
        code="UNLIMITED-PER-CUSTOMER",
        discount_type=Coupon.DiscountType.PERCENTAGE,
        discount_value=10,
        per_user_usage_limit=None,
    )

    assert checkout(client, user, coupon.code).status_code == 201
    assert checkout(client, user, coupon.code).status_code == 201
    assert coupon.redemptions.count() == 2


def test_per_user_coupon_limit_must_be_positive():
    with pytest.raises(IntegrityError), transaction.atomic():
        Coupon.objects.create(
            code="INVALID-PER-USER-LIMIT",
            discount_type=Coupon.DiscountType.PERCENTAGE,
            discount_value=10,
            per_user_usage_limit=0,
        )


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
    settings.FRONTEND_BASE_URL = "https://shop.example.invalid"
    add_to_cart(user, product)
    coupon = Coupon.objects.create(
        code="PAY10",
        discount_type=Coupon.DiscountType.PERCENTAGE,
        discount_value=10,
        per_user_usage_limit=1,
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
    assert order.coupon_redemption.state == CouponRedemption.State.CONSUMED

    CartItem.objects.create(
        cart=Cart.objects.get(user=user),
        product=product,
        quantity=1,
    )
    repeated = checkout(client, user, coupon.code)
    assert repeated.status_code == 400
    assert repeated.json()["coupon"] == [COUPON_UNAVAILABLE_MESSAGE]


def test_coupon_used_count_does_not_increment_twice(client, settings, user, product):
    settings.FRONTEND_BASE_URL = "https://shop.example.invalid"
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
