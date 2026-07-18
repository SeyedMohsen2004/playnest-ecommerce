from unittest.mock import Mock, patch

import pytest
import requests
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from orders.models import Cart, CartItem, Coupon, Order, OrderItem
from payments.models import Payment
from payments.serializers import PaymentSerializer
from payments.services.zarinpal import (
    PaymentCreationResult,
    PaymentVerificationResult,
    ZarinPalService,
    ZarinPalTransportError,
    ZarinPalVerificationError,
)
from products.models import Brand, Category, Product

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def payment_settings(settings):
    settings.FRONTEND_BASE_URL = "https://ipaktoys.ir"
    settings.ZARINPAL_MERCHANT_ID = "test-merchant"
    settings.ZARINPAL_SANDBOX = True
    settings.ZARINPAL_CALLBACK_URL = (
        "https://ipaktoys.ir/api/v1/payments/zarinpal/callback/"
    )


@pytest.fixture
def user():
    return User.objects.create_user(
        phone_number="09123456789",
        password="StrongPassword!42",
        first_name="Payment",
        last_name="User",
        is_active=True,
        is_phone_verified=True,
    )


@pytest.fixture
def other_user():
    return User.objects.create_user(
        phone_number="09987654321",
        password="StrongPassword!42",
        first_name="Other",
        last_name="User",
        is_active=True,
        is_phone_verified=True,
    )


@pytest.fixture
def category():
    return Category.objects.create(name="Payment Toys", slug="payment-toys")


@pytest.fixture
def brand():
    return Brand.objects.create(name="Pay Brand", slug="pay-brand")


@pytest.fixture
def product(category, brand):
    return Product.objects.create(
        category=category,
        brand=brand,
        name="Payment Toy",
        slug="payment-toy",
        description="A toy used for payment tests.",
        sku="PAY-001",
        price=1000,
        stock=10,
        age_group=Product.AgeGroup.THREE_TO_FIVE,
        gender=Product.Gender.UNISEX,
    )


@pytest.fixture
def extra_product(category, brand):
    return Product.objects.create(
        category=category,
        brand=brand,
        name="Unrelated Toy",
        slug="unrelated-toy",
        description="An unrelated cart item.",
        sku="PAY-002",
        price=1500,
        stock=8,
        age_group=Product.AgeGroup.THREE_TO_FIVE,
        gender=Product.Gender.UNISEX,
    )


@pytest.fixture
def order(user, product):
    instance = Order.objects.create(
        user=user,
        subtotal_amount=2000,
        total_amount=2000,
        shipping_address="123 Payment Street",
        postal_code="1234567890",
        recipient_name="Payment User",
        recipient_phone=user.phone_number,
    )
    OrderItem.objects.create(
        order=instance,
        product=product,
        product_name=product.name,
        product_price=1000,
        quantity=2,
        line_total=2000,
    )
    return instance


@pytest.fixture
def payment(user, order):
    return Payment.objects.create(
        user=user,
        order=order,
        amount=order.total_amount,
        authority="A" * 36,
    )


def auth(user):
    token = RefreshToken.for_user(user).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def callback(client, *, authority=None, status=None):
    parameters = {}
    if authority is not None:
        parameters["Authority"] = authority
    if status is not None:
        parameters["Status"] = status
    return client.get(reverse("payments:zarinpal-callback"), parameters)


def verify_result(code=100):
    return PaymentVerificationResult(
        code=code,
        message="Verified",
        ref_id="123456789",
        card_pan="603799******1234",
        card_hash="safe-card-hash",
        fee=100,
        fee_type="Merchant",
        gateway_response={
            "data": {
                "code": code,
                "message": "Verified",
                "ref_id": "123456789",
                "card_pan": "603799******1234",
                "card_hash": "safe-card-hash",
                "fee": 100,
                "fee_type": "Merchant",
            }
        },
    )


def creation_result():
    return PaymentCreationResult(
        authority="B" * 36,
        payment_url=f"https://sandbox.zarinpal.com/pg/StartPay/{'B' * 36}",
        code=100,
        message="Success",
        gateway_response={"data": {"code": 100, "authority": "B" * 36}},
    )


def test_missing_authority_redirects_without_verify(client):
    with patch("payments.views.ZarinPalService.verify_payment") as verify:
        response = callback(client, status="OK")

    assert response.status_code == 302
    assert response.url.endswith("/payment/failed?reason=missing_authority")
    verify.assert_not_called()


@pytest.mark.parametrize("gateway_status", (None, "", "UNKNOWN"))
def test_invalid_callback_status_redirects_without_verify(
    client, payment, gateway_status
):
    with patch("payments.views.ZarinPalService.verify_payment") as verify:
        response = callback(
            client,
            authority=payment.authority,
            status=gateway_status,
        )

    assert response.status_code == 302
    assert "reason=invalid_callback_status" in response.url
    verify.assert_not_called()


def test_unknown_authority_redirects_without_verify(client):
    with patch("payments.views.ZarinPalService.verify_payment") as verify:
        response = callback(client, authority="Z" * 36, status="OK")

    assert "reason=payment_not_found" in response.url
    verify.assert_not_called()


def test_nok_does_not_verify_or_touch_stock_or_cart(client, payment, product, user):
    cart = Cart.objects.create(user=user)
    item = CartItem.objects.create(cart=cart, product=product, quantity=4)

    with patch("payments.views.ZarinPalService.verify_payment") as verify:
        response = callback(client, authority=payment.authority, status="NOK")

    payment.refresh_from_db()
    payment.order.refresh_from_db()
    product.refresh_from_db()
    item.refresh_from_db()
    assert response.status_code == 302
    assert "reason=cancelled_or_failed" in response.url
    assert payment.status == Payment.Status.FAILED
    assert payment.order.status == Order.Status.PAYMENT_FAILED
    assert product.stock == 10
    assert item.quantity == 4
    verify.assert_not_called()


def test_nok_never_downgrades_paid_payment_or_order(client, payment):
    payment.status = Payment.Status.PAID
    payment.status_from_gateway = "OK"
    payment.gateway_code = 100
    payment.order.status = Order.Status.PAID
    payment.order.stock_reduced = True
    payment.save(update_fields=("status", "status_from_gateway", "gateway_code"))
    payment.order.save(update_fields=("status", "stock_reduced"))

    callback(client, authority=payment.authority, status="NOK")

    payment.refresh_from_db()
    payment.order.refresh_from_db()
    assert payment.status == Payment.Status.PAID
    assert payment.status_from_gateway == "OK"
    assert payment.gateway_code == 100
    assert payment.order.status == Order.Status.PAID
    assert payment.order.stock_reduced is True


def test_ok_verifies_with_stored_authority_and_amount(client, payment):
    payment.order.total_amount = 999999
    payment.order.save(update_fields=("total_amount",))

    with patch(
        "payments.views.ZarinPalService.verify_payment",
        return_value=verify_result(),
    ) as verify:
        callback(client, authority=payment.authority, status="OK")

    verify.assert_called_once_with(
        authority=payment.authority,
        amount=payment.amount,
    )


def test_code_100_finalizes_payment_order_stock_and_safe_gateway_fields(
    client, payment, product
):
    with patch(
        "payments.views.ZarinPalService.verify_payment",
        return_value=verify_result(100),
    ):
        response = callback(client, authority=payment.authority, status="OK")

    payment.refresh_from_db()
    payment.order.refresh_from_db()
    product.refresh_from_db()
    assert response.status_code == 302
    assert response.url.startswith("https://ipaktoys.ir/payment/success")
    assert payment.status == Payment.Status.PAID
    assert payment.gateway_code == 100
    assert payment.ref_id == "123456789"
    assert payment.card_pan == "603799******1234"
    assert payment.card_hash == "safe-card-hash"
    assert payment.fee == 100
    assert payment.fee_type == "Merchant"
    assert payment.verified_at is not None
    assert payment.order.status == Order.Status.PAID
    assert payment.order.stock_reduced is True
    assert product.stock == 8


def test_code_101_completes_incomplete_local_finalization(client, payment, product):
    payment.status = Payment.Status.PAID
    payment.save(update_fields=("status",))

    with patch(
        "payments.views.ZarinPalService.verify_payment",
        return_value=verify_result(101),
    ):
        response = callback(client, authority=payment.authority, status="OK")

    payment.refresh_from_db()
    payment.order.refresh_from_db()
    product.refresh_from_db()
    assert "/payment/success" in response.url
    assert payment.gateway_code == 101
    assert payment.order.stock_reduced is True
    assert product.stock == 8


def test_repeated_callback_is_idempotent_for_stock_and_cart(
    client, payment, product, user
):
    cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=cart, product=product, quantity=5)
    gateway_verify = Mock(return_value=verify_result(100))

    with patch(
        "payments.views.ZarinPalService.verify_payment",
        gateway_verify,
    ):
        first = callback(client, authority=payment.authority, status="OK")
        second = callback(client, authority=payment.authority, status="OK")

    payment.refresh_from_db()
    product.refresh_from_db()
    cart_item = CartItem.objects.get(cart=cart, product=product)
    assert "/payment/success" in first.url
    assert "/payment/success" in second.url
    assert product.stock == 8
    assert cart_item.quantity == 3
    assert payment.cart_finalized is True
    assert gateway_verify.call_count == 1


def test_success_removes_only_purchased_quantities_and_preserves_unrelated_items(
    client, payment, product, extra_product, user
):
    cart = Cart.objects.create(user=user)
    purchased = CartItem.objects.create(cart=cart, product=product, quantity=5)
    unrelated = CartItem.objects.create(
        cart=cart,
        product=extra_product,
        quantity=3,
    )

    with patch(
        "payments.views.ZarinPalService.verify_payment",
        return_value=verify_result(),
    ):
        callback(client, authority=payment.authority, status="OK")

    purchased.refresh_from_db()
    unrelated.refresh_from_db()
    assert purchased.quantity == 3
    assert unrelated.quantity == 3


def test_success_deletes_cart_line_when_quantity_equals_purchase(
    client, payment, product, user
):
    cart = Cart.objects.create(user=user)
    item = CartItem.objects.create(cart=cart, product=product, quantity=2)

    with patch(
        "payments.views.ZarinPalService.verify_payment",
        return_value=verify_result(),
    ):
        callback(client, authority=payment.authority, status="OK")

    assert not CartItem.objects.filter(pk=item.pk).exists()


def test_coupon_usage_increments_once_on_repeated_callback(client, payment, product):
    coupon = Coupon.objects.create(
        code="PAY10",
        discount_type=Coupon.DiscountType.FIXED,
        discount_value=100,
    )
    payment.order.coupon = coupon
    payment.order.save(update_fields=("coupon",))

    with patch(
        "payments.views.ZarinPalService.verify_payment",
        return_value=verify_result(),
    ):
        callback(client, authority=payment.authority, status="OK")
        callback(client, authority=payment.authority, status="OK")

    coupon.refresh_from_db()
    product.refresh_from_db()
    assert coupon.used_count == 1
    assert product.stock == 8


def test_definite_verify_failure_marks_eligible_states_failed_without_cart_change(
    client, payment, product, user
):
    cart = Cart.objects.create(user=user)
    item = CartItem.objects.create(cart=cart, product=product, quantity=2)
    error = ZarinPalVerificationError(
        "Verification rejected.",
        code=-51,
        gateway_response={"errors": {"code": -51, "message": "Rejected"}},
    )

    with patch(
        "payments.views.ZarinPalService.verify_payment",
        side_effect=error,
    ):
        response = callback(client, authority=payment.authority, status="OK")

    payment.refresh_from_db()
    payment.order.refresh_from_db()
    product.refresh_from_db()
    item.refresh_from_db()
    assert "reason=verification_failed" in response.url
    assert payment.status == Payment.Status.FAILED
    assert payment.order.status == Order.Status.PAYMENT_FAILED
    assert payment.gateway_code == -51
    assert product.stock == 10
    assert item.quantity == 2


def test_failed_verify_never_downgrades_paid_order(client, payment):
    payment.status = Payment.Status.PAID
    payment.order.status = Order.Status.PAID
    payment.save(update_fields=("status",))
    payment.order.save(update_fields=("status",))
    error = ZarinPalVerificationError("Rejected", code=-51)

    with patch(
        "payments.views.ZarinPalService.verify_payment",
        side_effect=error,
    ):
        callback(client, authority=payment.authority, status="OK")

    payment.refresh_from_db()
    payment.order.refresh_from_db()
    assert payment.status == Payment.Status.PAID
    assert payment.order.status == Order.Status.PAID


def test_transport_failure_preserves_pending_state_and_cart(
    client, payment, product, user
):
    cart = Cart.objects.create(user=user)
    item = CartItem.objects.create(cart=cart, product=product, quantity=2)

    with patch(
        "payments.views.ZarinPalService.verify_payment",
        side_effect=ZarinPalTransportError("Timed out"),
    ):
        response = callback(client, authority=payment.authority, status="OK")

    payment.refresh_from_db()
    payment.order.refresh_from_db()
    item.refresh_from_db()
    assert "reason=verification_unavailable" in response.url
    assert payment.status == Payment.Status.PENDING
    assert payment.order.status == Order.Status.PENDING
    assert item.quantity == 2


def test_cancelled_order_cannot_become_paid(client, payment, product):
    payment.status = Payment.Status.CANCELLED
    payment.order.status = Order.Status.CANCELLED
    payment.save(update_fields=("status",))
    payment.order.save(update_fields=("status",))

    with patch(
        "payments.views.ZarinPalService.verify_payment",
        return_value=verify_result(),
    ):
        response = callback(client, authority=payment.authority, status="OK")

    payment.refresh_from_db()
    payment.order.refresh_from_db()
    product.refresh_from_db()
    assert "reason=order_cancelled" in response.url
    assert payment.status == Payment.Status.PAID
    assert payment.order.status == Order.Status.CANCELLED
    assert payment.order.requires_manual_review is True
    assert payment.order.stock_reduced is False
    assert product.stock == 10


def test_paid_but_insufficient_stock_flags_manual_review_and_keeps_cart(
    client, payment, product, user
):
    product.stock = 1
    product.save(update_fields=("stock",))
    cart = Cart.objects.create(user=user)
    item = CartItem.objects.create(cart=cart, product=product, quantity=2)

    with patch(
        "payments.views.ZarinPalService.verify_payment",
        return_value=verify_result(),
    ):
        response = callback(client, authority=payment.authority, status="OK")

    payment.refresh_from_db()
    payment.order.refresh_from_db()
    product.refresh_from_db()
    item.refresh_from_db()
    assert "/payment/success" in response.url
    assert payment.status == Payment.Status.PAID
    assert payment.order.status == Order.Status.PAID
    assert payment.order.requires_manual_review is True
    assert payment.order.stock_reduced is False
    assert payment.cart_finalized is False
    assert product.stock == 1
    assert item.quantity == 2


def test_legacy_manual_verify_is_gone_and_cannot_mark_paid(client, payment):
    response = client.post(
        reverse("payments:verify"),
        {"authority": payment.authority, "status": "OK"},
        content_type="application/json",
    )

    payment.refresh_from_db()
    payment.order.refresh_from_db()
    assert response.status_code == 410
    assert payment.status == Payment.Status.PENDING
    assert payment.order.status == Order.Status.PENDING


def test_customer_payment_serializer_hides_internal_gateway_data(payment):
    payment.gateway_response = {"data": {"secret": "not-for-customers"}}
    payment.gateway_message = "internal diagnostic"
    payment.card_hash = "internal-card-hash"
    payment.card_pan = "6037991234561234"
    data = PaymentSerializer(payment).data

    assert "gateway_response" not in data
    assert "gateway_message" not in data
    assert "card_hash" not in data
    assert "authority" not in data
    assert "status_from_gateway" not in data
    assert data["card_pan"] == "603799******1234"


def test_payment_request_uses_order_id_and_stores_new_authority(client, user, order):
    with patch(
        "payments.services.ZarinPalService.create_payment",
        return_value=creation_result(),
    ):
        response = client.post(
            reverse("payments:request"),
            {"order_id": order.id},
            content_type="application/json",
            **auth(user),
        )

    assert response.status_code == 201
    payment = Payment.objects.get(order=order)
    assert payment.authority == "B" * 36
    assert response.json()["payment_url"].endswith("B" * 36)


def test_payment_request_rejects_wrong_payload_without_gateway_call(
    client, user, order
):
    with patch("payments.services.ZarinPalService.create_payment") as create:
        response = client.post(
            reverse("payments:request"),
            {"order": order.id},
            content_type="application/json",
            **auth(user),
        )

    assert response.status_code == 400
    create.assert_not_called()


def test_payment_request_rejects_another_users_order(client, other_user, order):
    response = client.post(
        reverse("payments:request"),
        {"order_id": order.id},
        content_type="application/json",
        **auth(other_user),
    )

    assert response.status_code == 403


def test_payment_request_rechecks_stock_before_gateway(client, user, order, product):
    product.stock = 1
    product.save(update_fields=("stock",))

    with patch("payments.services.ZarinPalService.create_payment") as create:
        response = client.post(
            reverse("payments:request"),
            {"order_id": order.id},
            content_type="application/json",
            **auth(user),
        )

    assert response.status_code == 400
    create.assert_not_called()


def test_zarinpal_verify_sends_json_headers_and_normalizes_fields(settings):
    response = Mock(status_code=200)
    response.json.return_value = {
        "data": {
            "code": 100,
            "message": "Verified",
            "ref_id": 123,
            "card_pan": "6037991234561234",
            "card_hash": "hash",
            "fee": "100",
            "fee_type": "Merchant",
        }
    }

    with patch(
        "payments.services.zarinpal.requests.post", return_value=response
    ) as post:
        result = ZarinPalService().verify_payment("A" * 36, 2000)

    assert result.code == 100
    assert result.ref_id == "123"
    assert result.card_pan == "603799******1234"
    assert result.fee == 100
    post.assert_called_once_with(
        ZarinPalService.SANDBOX_ENDPOINTS.verify_url,
        json={
            "merchant_id": "test-merchant",
            "amount": 2000,
            "authority": "A" * 36,
        },
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        timeout=15,
    )


def test_zarinpal_verify_accepts_code_101():
    response = Mock(status_code=200)
    response.json.return_value = {"data": {"code": 101, "message": "Verified"}}

    with patch("payments.services.zarinpal.requests.post", return_value=response):
        result = ZarinPalService().verify_payment("A" * 36, 2000)

    assert result.is_successful is True
    assert result.code == 101


def test_zarinpal_timeout_is_normalized():
    with patch(
        "payments.services.zarinpal.requests.post",
        side_effect=requests.Timeout,
    ):
        with pytest.raises(ZarinPalTransportError, match="timed out"):
            ZarinPalService().verify_payment("A" * 36, 2000)


def test_zarinpal_invalid_json_is_normalized():
    response = Mock(status_code=200)
    response.json.side_effect = ValueError("invalid JSON")

    with patch("payments.services.zarinpal.requests.post", return_value=response):
        with pytest.raises(ZarinPalTransportError, match="invalid response"):
            ZarinPalService().verify_payment("A" * 36, 2000)


def test_zarinpal_non_success_code_is_not_successful():
    response = Mock(status_code=200)
    response.json.return_value = {"data": {"code": -51, "message": "Payment not found"}}

    with patch("payments.services.zarinpal.requests.post", return_value=response):
        with pytest.raises(ZarinPalVerificationError) as exc_info:
            ZarinPalService().verify_payment("A" * 36, 2000)

    assert exc_info.value.code == -51
